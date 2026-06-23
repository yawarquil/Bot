# StreamVault Social Media Bots

Automatically posts movies and TV shows from StreamVault.live to multiple platforms.

## Bots Available

| Bot | Platform | File |
|-----|----------|------|
| 📱 Telegram | @streamvaultt | `telegram_bot.py` |
| 🐦 Twitter/X | Twitter | `twitter_bot.py` |
| 📷 Instagram | Instagram | `instagram_bot.py` |
| 📘 Facebook | Facebook Page | `facebook_bot.py` |

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your API credentials:
```bash
cp .env.example .env
```

### 3. Run Bots
```bash
# Telegram
python telegram_bot.py

# Twitter
python twitter_bot.py

# Instagram
python instagram_bot.py

# Facebook
python facebook_bot.py
```

## Getting API Credentials

### Telegram
1. Message [@BotFather](https://t.me/BotFather)
2. Create new bot with `/newbot`
3. Copy the token

### Twitter
1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Apply for developer access
3. Create a project and app
4. Generate API keys and tokens

### Instagram/Facebook
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create an app (Business type)
3. Add Instagram Graph API product
4. Connect your Business Instagram account
5. Generate access token

## File Structure
```
moviebot/
├── telegram_bot.py      # Telegram channel poster
├── twitter_bot.py       # Twitter poster
├── instagram_bot.py     # Instagram poster
├── facebook_bot.py      # Facebook page poster
├── shared_utils.py      # Shared formatting functions
├── config.py            # Configuration
├── requirements.txt     # Dependencies
└── .env                 # API credentials (create from .env.example)
```
