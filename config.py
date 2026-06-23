"""Configuration settings for the StreamVault Social Media Bots."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@streamvaultt")

# StreamVault Configuration
STREAMVAULT_BASE_URL = os.getenv("STREAMVAULT_BASE_URL", "https://streamvault.live")
STREAMVAULT_API_KEY = os.getenv("STREAMVAULT_API_KEY", "")
STREAMVAULT_API_SHOWS = f"{STREAMVAULT_BASE_URL}/api/shows"
STREAMVAULT_API_MOVIES = f"{STREAMVAULT_BASE_URL}/api/movies"
STREAMVAULT_API_ANIME = f"{STREAMVAULT_BASE_URL}/api/anime"

# File paths
POSTED_CONTENT_FILE = "posted_content.json"

# Promotion Settings
CHANNEL_INVITE_LINK = os.getenv("CHANNEL_INVITE_LINK", "https://t.me/streamvaultt")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://streamvault.live")
PROMOTION_INTERVAL = int(os.getenv("PROMOTION_INTERVAL", "10"))

# ==================== TWITTER CONFIGURATION ====================
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# ==================== META (INSTAGRAM/FACEBOOK) CONFIGURATION ====================
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")

# ==================== DISCORD CONFIGURATION ====================
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

