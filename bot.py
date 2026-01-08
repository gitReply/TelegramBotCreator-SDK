"""
Telegram Bot Creator SDK
Automatically creates Telegram bots via BotFather
"""
import asyncio
import logging
import os
import re
import secrets
import string
from typing import Dict, Optional
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

try:
    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError
    from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_DESCRIPTION = os.getenv('BOT_DESCRIPTION', 'Want the same gift? Check out @FameGifterBot\n\nBot created for entertainment purposes.')
USERNAME_PREFIX = os.getenv('USERNAME_PREFIX', 'famegifter')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class BotCreationStates(StatesGroup):
    waiting_for_bot_name = State()
    waiting_for_avatar = State()


@dp.message(CommandStart())
async def start_handler(message: Message):
    """Handle /start command"""
    status = "Ready" if TELETHON_AVAILABLE and os.getenv('TELEGRAM_API_ID') and os.getenv('TELEGRAM_API_HASH') else "Not configured"
    
    await message.answer(
        f"Bot Creator SDK\n\n"
        f"Status: {status}\n\n"
        f"Commands:\n"
        f"/create - Create a new bot\n"
        f"/help - Show help"
    )


@dp.message(Command('help'))
async def help_handler(message: Message):
    """Handle /help command"""
    setup_info = ""
    if not TELETHON_AVAILABLE:
        setup_info = "\n\nSetup: pip install telethon"
    elif not os.getenv('TELEGRAM_API_ID') or not os.getenv('TELEGRAM_API_HASH'):
        setup_info = "\n\nConfiguration required:\n1. Get API_ID and API_HASH from https://my.telegram.org/apps\n2. Add them to .env file\n3. Run: python setup_telethon.py"
    
    await message.answer(
        f"Bot Creator SDK Help\n\n"
        f"Usage:\n"
        f"1. Use /create command\n"
        f"2. Enter bot name\n"
        f"3. Send avatar photo (optional)\n\n"
        f"The bot will:\n"
        f"- Generate unique username\n"
        f"- Create bot via BotFather\n"
        f"- Set description\n"
        f"- Return token{setup_info}"
    )


@dp.message(Command('create'))
async def create_handler(message: Message, state: FSMContext):
    """Handle /create command"""
    await message.answer("Enter bot name:")
    await state.set_state(BotCreationStates.waiting_for_bot_name)


@dp.message(BotCreationStates.waiting_for_bot_name)
async def process_bot_name(message: Message, state: FSMContext):
    """Process bot name input"""
    bot_name = message.text.strip()
    
    if len(bot_name) < 3 or len(bot_name) > 100:
        await message.answer("Bot name must be between 3 and 100 characters. Try again:")
        return
    
    # Generate username: prefix + random suffix + 'bot'
    random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    username = f"{USERNAME_PREFIX}{random_suffix}bot"
    
    await message.answer(f"Creating bot: {bot_name}\nUsername: @{username}")
    
    result = await create_bot(bot_name, username)
    
    if result.get('token'):
        bot_username = result.get('username', username).replace('@', '')
        description_set = await set_bot_description(result['token'], bot_username)
        
        await state.update_data(
            bot_token=result['token'],
            bot_username=bot_username,
            bot_name=bot_name
        )
        
        await message.answer(
            f"Bot created successfully\n\n"
            f"Name: {bot_name}\n"
            f"Username: @{bot_username}\n"
            f"Token: `{result['token']}`\n\n"
            f"Description: {'Set' if description_set else 'Not set'}\n\n"
            f"Send photo for bot avatar (or /skip to skip):",
            parse_mode='Markdown'
        )
        await state.set_state(BotCreationStates.waiting_for_avatar)
    else:
        error_msg = result.get('error', 'Unknown error')
        if "already" in error_msg.lower() or "taken" in error_msg.lower():
            # Retry with new username
            random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
            username = f"{USERNAME_PREFIX}{random_suffix}bot"
            result = await create_bot(bot_name, username)
            
            if result.get('token'):
                bot_username = result.get('username', username).replace('@', '')
                description_set = await set_bot_description(result['token'], bot_username)
                await state.update_data(
                    bot_token=result['token'],
                    bot_username=bot_username,
                    bot_name=bot_name
                )
                await message.answer(
                    f"Bot created successfully\n\n"
                    f"Name: {bot_name}\n"
                    f"Username: @{bot_username}\n"
                    f"Token: `{result['token']}`\n\n"
                    f"Description: {'Set' if description_set else 'Not set'}\n\n"
                    f"Send photo for bot avatar (or /skip to skip):",
                    parse_mode='Markdown'
                )
                await state.set_state(BotCreationStates.waiting_for_avatar)
            else:
                await message.answer(f"Error: {result.get('error', 'Unknown error')}")
                await state.clear()
        else:
            await message.answer(f"Error: {error_msg}")
            await state.clear()


@dp.message(StateFilter(BotCreationStates.waiting_for_avatar), F.photo)
async def process_avatar(message: Message, state: FSMContext):
    """Process avatar photo"""
    try:
        data = await state.get_data()
        bot_token = data.get('bot_token')
        bot_username = data.get('bot_username')
        bot_name = data.get('bot_name')
        
        if not bot_token or not bot_username:
            await message.answer("Error: Bot data not found. Start over with /create")
            await state.clear()
            return
        
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        
        os.makedirs('temp', exist_ok=True)
        temp_file = f"temp/avatar_{message.from_user.id}_{photo.file_id}.jpg"
        await bot.download_file(file_info.file_path, temp_file)
        
        avatar_set = await set_bot_avatar(bot_username, temp_file)
        
        try:
            os.remove(temp_file)
        except:
            pass
        
        if avatar_set:
            await message.answer(
                f"Avatar set successfully\n\n"
                f"Name: {bot_name}\n"
                f"Username: @{bot_username}\n"
                f"Token: `{bot_token}`\n\n"
                f"Save token securely. Use /create to create another bot.",
                parse_mode='Markdown'
            )
        else:
            await message.answer(
                f"Avatar not set automatically. Set manually via @BotFather\n\n"
                f"Token: `{bot_token}`",
                parse_mode='Markdown'
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Avatar processing error: {e}", exc_info=True)
        await message.answer(f"Error processing avatar: {str(e)}")
        await state.clear()


@dp.message(StateFilter(BotCreationStates.waiting_for_avatar))
async def process_avatar_invalid(message: Message, state: FSMContext):
    """Handle invalid input while waiting for avatar"""
    await message.answer("Please send a photo or use /skip to skip avatar setup")


@dp.message(Command('skip'), StateFilter(BotCreationStates.waiting_for_avatar))
async def skip_avatar(message: Message, state: FSMContext):
    """Skip avatar setup"""
    data = await state.get_data()
    bot_token = data.get('bot_token')
    bot_username = data.get('bot_username')
    bot_name = data.get('bot_name')
    
    await message.answer(
        f"Avatar setup skipped\n\n"
        f"Name: {bot_name}\n"
        f"Username: @{bot_username}\n"
        f"Token: `{bot_token}`\n\n"
        f"Save token securely. Use /create to create another bot.",
        parse_mode='Markdown'
    )
    await state.clear()


async def create_bot(bot_name: str, username: str) -> Dict:
    """Create bot via BotFather using Telethon"""
    if not TELETHON_AVAILABLE:
        return {'success': False, 'error': 'Telethon not installed', 'token': None}
    
    try:
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not api_id or not api_hash:
            return {'success': False, 'error': 'TELEGRAM_API_ID and TELEGRAM_API_HASH not found', 'token': None}
        
        session_name = 'sessions/bot_creator'
        os.makedirs('sessions', exist_ok=True)
        
        if not os.path.exists(f'{session_name}.session'):
            return {'success': False, 'error': 'Session not authorized. Run setup_telethon.py', 'token': None}
        
        client = TelegramClient(session_name, int(api_id), api_hash)
        
        try:
            await client.start()
            me = await client.get_me()
            logger.info(f"Authorized as: {me.first_name}")
            
            botfather_username = 'BotFather'
            
            await client.send_message(botfather_username, '/newbot')
            await asyncio.sleep(3)
            
            await client.send_message(botfather_username, bot_name)
            await asyncio.sleep(3)
            
            await client.send_message(botfather_username, username)
            await asyncio.sleep(4)
            
            messages = await client.get_messages(botfather_username, limit=5)
            
            token = None
            error_found = False
            last_message_text = ""
            
            for msg in messages:
                if msg.text:
                    last_message_text = msg.text
                    
                    error_indicators = ["Sorry", "error", "already", "taken", "invalid", "not available"]
                    if any(indicator.lower() in msg.text.lower() for indicator in error_indicators):
                        error_found = True
                    
                    token_patterns = [
                        r'(\d+:[A-Za-z0-9_-]{20,})',
                        r'Use this token.*?(\d+:[A-Za-z0-9_-]+)',
                        r'Токен.*?(\d+:[A-Za-z0-9_-]+)',
                    ]
                    
                    for pattern in token_patterns:
                        match = re.search(pattern, msg.text, re.IGNORECASE)
                        if match:
                            token = match.group(1)
                            break
                    
                    if token:
                        break
            
            if token:
                return {'success': True, 'token': token, 'username': username}
            else:
                error_msg = last_message_text[:500] if error_found and last_message_text else "Token not found in BotFather response"
                return {'success': False, 'error': error_msg, 'token': None}
                
        finally:
            await client.disconnect()
            
    except SessionPasswordNeededError:
        return {'success': False, 'error': '2FA required. Run setup_telethon.py', 'token': None}
    except Exception as e:
        logger.error(f"Bot creation error: {e}", exc_info=True)
        return {'success': False, 'error': str(e), 'token': None}


async def set_bot_description(token: str, bot_username: str) -> bool:
    """Set bot description via BotFather"""
    if not TELETHON_AVAILABLE:
        return False
    
    try:
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not api_id or not api_hash:
            return False
        
        session_name = 'sessions/bot_creator'
        client = TelegramClient(session_name, int(api_id), api_hash)
        
        try:
            await client.start()
            botfather_username = 'BotFather'
            clean_username = bot_username.replace('@', '')
            
            await client.send_message(botfather_username, '/setdescription')
            await asyncio.sleep(3)
            
            messages = await client.get_messages(botfather_username, limit=1)
            
            if messages and messages[0].reply_markup:
                msg = messages[0]
                bot_found = False
                
                try:
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            button_text = button.text if hasattr(button, 'text') else str(button)
                            if clean_username.lower() in button_text.lower():
                                botfather_entity = await client.get_entity(botfather_username)
                                await client(GetBotCallbackAnswerRequest(
                                    peer=botfather_entity,
                                    msg_id=msg.id,
                                    data=button.data
                                ))
                                bot_found = True
                                await asyncio.sleep(3)
                                break
                        if bot_found:
                            break
                    
                    if not bot_found:
                        first_row = msg.reply_markup.rows[0]
                        first_button = first_row.buttons[0]
                        botfather_entity = await client.get_entity(botfather_username)
                        await client(GetBotCallbackAnswerRequest(
                            peer=botfather_entity,
                            msg_id=msg.id,
                            data=first_button.data
                        ))
                        await asyncio.sleep(3)
                except Exception as e:
                    logger.warning(f"Button click error: {e}")
                    await client.send_message(botfather_username, f"@{clean_username}")
                    await asyncio.sleep(3)
            else:
                await client.send_message(botfather_username, f"@{clean_username}")
                await asyncio.sleep(3)
            
            await client.send_message(botfather_username, BOT_DESCRIPTION)
            await asyncio.sleep(3)
            
            messages = await client.get_messages(botfather_username, limit=3)
            
            for msg in messages:
                if msg.text:
                    success_indicators = ["successfully", "успешно", "Success", "description"]
                    if any(indicator.lower() in msg.text.lower() for indicator in success_indicators):
                        return True
                    error_indicators = ["error", "ошибка", "Sorry", "invalid"]
                    if any(indicator.lower() in msg.text.lower() for indicator in error_indicators):
                        return False
            
            return False
            
        finally:
            await client.disconnect()
            
    except Exception as e:
        logger.error(f"Description setting error: {e}", exc_info=True)
        return False


async def set_bot_avatar(bot_username: str, photo_path: str) -> bool:
    """Set bot avatar via BotFather"""
    if not TELETHON_AVAILABLE:
        return False
    
    try:
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not api_id or not api_hash or not os.path.exists(photo_path):
            return False
        
        session_name = 'sessions/bot_creator'
        client = TelegramClient(session_name, int(api_id), api_hash)
        
        try:
            await client.start()
            botfather_username = 'BotFather'
            clean_username = bot_username.replace('@', '')
            
            await client.send_message(botfather_username, '/setuserpic')
            await asyncio.sleep(3)
            
            messages = await client.get_messages(botfather_username, limit=1)
            
            if messages and messages[0].reply_markup:
                msg = messages[0]
                bot_found = False
                
                try:
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            button_text = button.text if hasattr(button, 'text') else str(button)
                            if clean_username.lower() in button_text.lower():
                                botfather_entity = await client.get_entity(botfather_username)
                                await client(GetBotCallbackAnswerRequest(
                                    peer=botfather_entity,
                                    msg_id=msg.id,
                                    data=button.data
                                ))
                                bot_found = True
                                await asyncio.sleep(3)
                                break
                        if bot_found:
                            break
                    
                    if not bot_found:
                        first_row = msg.reply_markup.rows[0]
                        first_button = first_row.buttons[0]
                        botfather_entity = await client.get_entity(botfather_username)
                        await client(GetBotCallbackAnswerRequest(
                            peer=botfather_entity,
                            msg_id=msg.id,
                            data=first_button.data
                        ))
                        await asyncio.sleep(3)
                except Exception as e:
                    logger.warning(f"Button click error: {e}")
                    await client.send_message(botfather_username, f"@{clean_username}")
                    await asyncio.sleep(3)
            else:
                await client.send_message(botfather_username, f"@{clean_username}")
                await asyncio.sleep(3)
            
            await client.send_file(botfather_username, photo_path)
            await asyncio.sleep(4)
            
            messages = await client.get_messages(botfather_username, limit=3)
            
            for msg in messages:
                if msg.text:
                    success_indicators = ["successfully", "успешно", "Success", "picture"]
                    if any(indicator.lower() in msg.text.lower() for indicator in success_indicators):
                        return True
                    error_indicators = ["error", "ошибка", "Sorry", "invalid"]
                    if any(indicator.lower() in msg.text.lower() for indicator in error_indicators):
                        return False
            
            return False
            
        finally:
            await client.disconnect()
            
    except Exception as e:
        logger.error(f"Avatar setting error: {e}", exc_info=True)
        return False


@dp.message()
async def unknown_handler(message: Message):
    """Handle unknown messages"""
    await message.answer("Unknown command. Use /help for available commands.")


async def main():
    """Main function"""
    logger.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Critical error: {e}")
