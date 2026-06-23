"""
Twitter/X Auto-Posting Bot for StreamVault

Posts movies and TV shows to Twitter automatically.
Requires Twitter API v2 credentials.
"""
import asyncio
import logging
import os
from pathlib import Path

import tweepy

from config import (
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_SECRET,
    TWITTER_BEARER_TOKEN
)
from shared_utils import (
    fetch_shows,
    fetch_movies,
    fetch_anime,
    load_posted_content,
    save_posted_content,
    format_show_for_twitter,
    format_movie_for_twitter,
    format_anime_for_twitter,
    get_promotion_message_twitter
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Tracking file
POSTED_FILE = "twitter_posted.json"


def get_twitter_client():
    """Initialize Twitter API v2 client."""
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        logger.error("Twitter API credentials not set!")
        return None, None
    
    # Client for tweeting (API v2)
    client = tweepy.Client(
        bearer_token=TWITTER_BEARER_TOKEN,
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_SECRET
    )
    
    # Auth for media upload (API v1.1)
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY,
        TWITTER_API_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_SECRET
    )
    api = tweepy.API(auth)
    
    return client, api


def download_image(url: str, filename: str) -> str:
    """Download image from URL to local file."""
    import requests
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        filepath = f"temp_{filename}.jpg"
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None


def post_tweet(client, api, text: str, image_url: str = None) -> bool:
    """Post a tweet with optional image."""
    try:
        media_id = None
        temp_file = None
        
        # Upload image if provided
        if image_url and image_url.startswith('http'):
            temp_file = download_image(image_url, "poster")
            if temp_file and Path(temp_file).exists():
                media = api.media_upload(temp_file)
                media_id = media.media_id
        
        # Post tweet
        if media_id:
            client.create_tweet(text=text, media_ids=[media_id])
        else:
            client.create_tweet(text=text)
        
        # Cleanup temp file
        if temp_file and Path(temp_file).exists():
            os.remove(temp_file)
        
        return True
    except Exception as e:
        logger.error(f"Error posting tweet: {e}")
        if temp_file and Path(temp_file).exists():
            os.remove(temp_file)
        return False


def post_one_item(item_type: str = None):
    """Post ONE show or movie to Twitter."""
    client, api = get_twitter_client()
    if not client:
        return
    
    posted = load_posted_content(POSTED_FILE)
    
    # Fetch content
    logger.info("Fetching content...")
    shows = fetch_shows()
    movies = fetch_movies()
    anime = fetch_anime()
    
    # Find unposted content
    unposted_shows = [s for s in shows if s.get('id') not in posted.get("shows", [])]
    unposted_movies = [m for m in movies if m.get('id') not in posted.get("movies", [])]
    unposted_anime = [a for a in anime if a.get('id') not in posted.get("anime", [])]
    
    logger.info(f"Unposted: {len(unposted_shows)} shows, {len(unposted_movies)} movies, {len(unposted_anime)} anime")
    
    if not unposted_shows and not unposted_movies and not unposted_anime:
        logger.info("✅ All content has been posted!")
        return
    
    # Select item based on user choice
    item = None
    
    if item_type == "show":
        if unposted_shows:
            item = unposted_shows[0]
        else:
            logger.info("❌ No unposted shows available!")
            return
    elif item_type == "movie":
        if unposted_movies:
            item = unposted_movies[0]
        else:
            logger.info("❌ No unposted movies available!")
            return
    elif item_type == "anime":
        if unposted_anime:
            item = unposted_anime[0]
        else:
            logger.info("❌ No unposted anime available!")
            return
    else:
        # Auto-alternate between show, movie, and anime
        last_type = posted.get("last_type", "movie")
        if last_type == "movie" and unposted_shows:
            item = unposted_shows[0]
            item_type = "show"
        elif last_type == "show" and unposted_anime:
            item = unposted_anime[0]
            item_type = "anime"
        elif unposted_movies:
            item = unposted_movies[0]
            item_type = "movie"
        elif unposted_shows:
            item = unposted_shows[0]
            item_type = "show"
        elif unposted_anime:
            item = unposted_anime[0]
            item_type = "anime"
    
    if not item:
        logger.info("✅ All content has been posted!")
        return
    
    # Post the item
    item_id = item.get('id')
    title = item.get('title', 'Unknown')
    poster = item.get('posterUrl')
    
    if item_type == "show":
        tweet = format_show_for_twitter(item)
    elif item_type == "anime":
        tweet = format_anime_for_twitter(item)
    else:
        tweet = format_movie_for_twitter(item)
    
    logger.info(f"📢 Posting {item_type}: {title}")
    
    if post_tweet(client, api, tweet, poster):
        if item_type == "show":
            posted["shows"].append(item_id)
        elif item_type == "anime":
            if "anime" not in posted:
                posted["anime"] = []
            posted["anime"].append(item_id)
        else:
            posted["movies"].append(item_id)
        posted["last_type"] = item_type
        save_posted_content(posted, POSTED_FILE)
        logger.info(f"✅ Posted {item_type}: {title}")
    else:
        logger.error(f"❌ Failed to post: {title}")


if __name__ == "__main__":
    print("\n🐦 StreamVault Twitter Bot")
    print("=" * 30)
    print("1. Post a Show")
    print("2. Post a Movie")
    print("3. Post an Anime")
    print("4. Auto (alternate)")
    print("=" * 30)
    
    choice = input("Choose (1/2/3/4): ").strip()
    
    if choice == "1":
        post_one_item("show")
    elif choice == "2":
        post_one_item("movie")
    elif choice == "3":
        post_one_item("anime")
    else:
        post_one_item()
