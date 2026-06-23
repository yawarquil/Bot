"""
Instagram Auto-Posting Bot for StreamVault

Posts movies and TV shows to Instagram automatically.
Requires Meta Graph API credentials and a Business/Creator Instagram account.
"""
import logging
import os
import time
from pathlib import Path

import requests

from config import (
    META_ACCESS_TOKEN,
    INSTAGRAM_ACCOUNT_ID
)
from shared_utils import (
    fetch_shows,
    fetch_movies,
    load_posted_content,
    save_posted_content,
    format_show_for_instagram,
    format_movie_for_instagram,
    get_promotion_message_instagram
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Tracking file
POSTED_FILE = "instagram_posted.json"

# Instagram Graph API base URL
GRAPH_API_URL = "https://graph.facebook.com/v18.0"


def create_media_container(image_url: str, caption: str) -> str:
    """Create a media container for Instagram post."""
    if not META_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
        logger.error("Instagram credentials not set!")
        return None
    
    try:
        url = f"{GRAPH_API_URL}/{INSTAGRAM_ACCOUNT_ID}/media"
        params = {
            "image_url": image_url,
            "caption": caption,
            "access_token": META_ACCESS_TOKEN
        }
        
        response = requests.post(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return data.get("id")
    except Exception as e:
        logger.error(f"Error creating media container: {e}")
        return None


def publish_media(creation_id: str) -> bool:
    """Publish the media container to Instagram."""
    try:
        url = f"{GRAPH_API_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        params = {
            "creation_id": creation_id,
            "access_token": META_ACCESS_TOKEN
        }
        
        response = requests.post(url, params=params)
        response.raise_for_status()
        
        return True
    except Exception as e:
        logger.error(f"Error publishing media: {e}")
        return False


def post_to_instagram(image_url: str, caption: str) -> bool:
    """Post an image with caption to Instagram."""
    if not image_url or not image_url.startswith('http'):
        logger.warning("No valid image URL provided")
        return False
    
    # Step 1: Create media container
    creation_id = create_media_container(image_url, caption)
    if not creation_id:
        return False
    
    # Wait for processing
    time.sleep(5)
    
    # Step 2: Publish the media
    return publish_media(creation_id)


def post_one_item(item_type: str = None):
    """Post ONE show or movie to Instagram."""
    if not META_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
        logger.error("Instagram API credentials not set!")
        logger.error("Set META_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in .env")
        return
    
    posted = load_posted_content(POSTED_FILE)
    
    # Fetch content
    logger.info("Fetching content...")
    shows = fetch_shows()
    movies = fetch_movies()
    
    # Find unposted content with valid posters
    unposted_shows = [s for s in shows if s.get('id') not in posted.get("shows", []) and s.get('posterUrl', '').startswith('http')]
    unposted_movies = [m for m in movies if m.get('id') not in posted.get("movies", []) and m.get('posterUrl', '').startswith('http')]
    
    logger.info(f"Unposted: {len(unposted_shows)} shows, {len(unposted_movies)} movies")
    
    if not unposted_shows and not unposted_movies:
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
    else:
        # Auto-alternate
        last_type = posted.get("last_type", "movie")
        if last_type == "movie" and unposted_shows:
            item = unposted_shows[0]
            item_type = "show"
        elif unposted_movies:
            item = unposted_movies[0]
            item_type = "movie"
        elif unposted_shows:
            item = unposted_shows[0]
            item_type = "show"
    
    if not item:
        logger.info("✅ All content has been posted!")
        return
    
    # Post the item
    item_id = item.get('id')
    title = item.get('title', 'Unknown')
    poster = item.get('posterUrl')
    
    if item_type == "show":
        caption = format_show_for_instagram(item)
    else:
        caption = format_movie_for_instagram(item)
    
    logger.info(f"📢 Posting {item_type}: {title}")
    
    if post_to_instagram(poster, caption):
        if item_type == "show":
            posted["shows"].append(item_id)
        else:
            posted["movies"].append(item_id)
        posted["last_type"] = item_type
        save_posted_content(posted, POSTED_FILE)
        logger.info(f"✅ Posted {item_type}: {title}")
    else:
        logger.error(f"❌ Failed to post: {title}")


if __name__ == "__main__":
    print("\n📷 StreamVault Instagram Bot")
    print("=" * 30)
    print("1. Post a Show")
    print("2. Post a Movie")
    print("3. Auto (alternate)")
    print("=" * 30)
    
    choice = input("Choose (1/2/3): ").strip()
    
    if choice == "1":
        post_one_item("show")
    elif choice == "2":
        post_one_item("movie")
    else:
        post_one_item()


