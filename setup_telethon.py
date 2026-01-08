"""
Setup and authorize Telethon session for bot creation
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

load_dotenv()


async def setup_telethon():
    """Setup and authorize Telethon session"""
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH not found in .env file")
        print("\nInstructions:")
        print("1. Go to https://my.telegram.org/apps")
        print("2. Login to your account")
        print("3. Create a new application (if not created)")
        print("4. Copy api_id and api_hash")
        print("5. Add them to .env file:")
        print("   TELEGRAM_API_ID=your_api_id")
        print("   TELEGRAM_API_HASH=your_api_hash")
        sys.exit(1)
    
    os.makedirs('sessions', exist_ok=True)
    session_name = 'sessions/bot_creator'
    client = TelegramClient(session_name, int(api_id), api_hash)
    
    try:
        print("Connecting to Telegram...")
        await client.connect()
        
        if not await client.is_user_authorized():
            print("Sending verification code...")
            phone = input("Enter phone number (with country code, e.g. +1234567890): ")
            await client.send_code_request(phone)
            
            try:
                code = input("Enter verification code from Telegram: ")
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input("Enter 2FA password: ")
                await client.sign_in(password=password)
        
        me = await client.get_me()
        print(f"Authorization successful!")
        print(f"Authorized as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
        print(f"\nSetup complete! You can now use the bot to create other bots.")
        
    except Exception as e:
        print(f"Setup error: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()


if __name__ == '__main__':
    print("Telethon Setup for Bot Creator SDK\n")
    asyncio.run(setup_telethon())
