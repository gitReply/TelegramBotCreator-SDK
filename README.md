# Telegram Bot Creator SDK

Python SDK for automatically creating Telegram bots via BotFather. This SDK allows you to programmatically create Telegram bots, set their descriptions, and avatars through a simple interface.

## Features

- **Automatic Bot Creation**: Create Telegram bots via BotFather API
- **Custom Username Generation**: Generate unique usernames with custom prefix
- **Description Management**: Automatically set bot descriptions
- **Avatar Setup**: Set bot avatars from photos
- **Telethon Integration**: Uses Telethon for seamless BotFather interaction

## Installation

```bash
pip install -r requirements.txt
```

### Windows Installation

For Windows users, use the installation script:

```powershell
.\install.ps1
```

Or manually:

```bash
pip install python-dotenv
pip install --prefer-binary aiogram aiofiles telethon
```

## Configuration

1. **Create a main bot via BotFather**:
   - Open [@BotFather](https://t.me/BotFather) in Telegram
   - Send `/newbot` command
   - Follow instructions to create your bot
   - Save the token

2. **Get Telegram API credentials**:
   - Go to https://my.telegram.org/apps
   - Login to your account
   - Create a new application (if not created)
   - Copy `api_id` and `api_hash`

3. **Create `.env` file**:

```env
BOT_TOKEN=your_main_bot_token
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
BOT_DESCRIPTION=Your bot description text
USERNAME_PREFIX=yourprefix
```

4. **Setup Telethon session**:

```bash
python setup_telethon.py
```

This script will:
- Request your phone number
- Send verification code
- Request 2FA password if enabled
- Create authorized session

## Usage

### Basic Usage

```bash
python bot.py
```

### Using as SDK

```python
from bot import create_bot, set_bot_description, set_bot_avatar

# Create a bot
result = await create_bot("My Bot Name", "mybotusernamebot")

if result.get('token'):
    token = result['token']
    username = result['username']
    
    # Set description
    await set_bot_description(token, username)
    
    # Set avatar
    await set_bot_avatar(username, "path/to/avatar.jpg")
```

### Environment Variables

- `BOT_TOKEN` (required): Token of the main bot creator
- `TELEGRAM_API_ID` (required): Telegram API ID
- `TELEGRAM_API_HASH` (required): Telegram API Hash
- `BOT_DESCRIPTION` (optional): Default description for created bots
- `USERNAME_PREFIX` (optional): Prefix for generated usernames (default: `famegifter`)

## API Reference

### `create_bot(bot_name: str, username: str) -> Dict`

Creates a new bot via BotFather.

**Parameters:**
- `bot_name` (str): Name of the bot
- `username` (str): Username for the bot (must end with 'bot')

**Returns:**
- `Dict` with keys:
  - `success` (bool): Whether creation was successful
  - `token` (str|None): Bot token if successful
  - `username` (str|None): Bot username if successful
  - `error` (str|None): Error message if failed

### `set_bot_description(token: str, bot_username: str) -> bool`

Sets bot description via BotFather.

**Parameters:**
- `token` (str): Bot token
- `bot_username` (str): Bot username (without @)

**Returns:**
- `bool`: True if successful, False otherwise

### `set_bot_avatar(bot_username: str, photo_path: str) -> bool`

Sets bot avatar via BotFather.

**Parameters:**
- `bot_username` (str): Bot username (without @)
- `photo_path` (str): Path to photo file

**Returns:**
- `bool`: True if successful, False otherwise

## Project Structure

```
.
├── bot.py                 # Main bot application
├── setup_telethon.py      # Telethon session setup
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables example
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## Troubleshooting

### "Telethon session not authorized"

Run `python setup_telethon.py` to authorize the session.

### "TELEGRAM_API_ID and TELEGRAM_API_HASH not found"

Add these variables to your `.env` file. Get them from https://my.telegram.org/apps

### Installation errors on Windows

Use `--prefer-binary` flag:

```bash
pip install --prefer-binary telethon
```

Or install Microsoft Visual C++ Build Tools or Rust.

## Requirements

- Python 3.8+
- aiogram 3.x
- telethon
- python-dotenv
- aiofiles

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
