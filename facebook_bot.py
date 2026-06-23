"""
Facebook Page Auto-Posting Bot for StreamVault

Posts movies and TV shows to a Facebook Page automatically.
Requires Meta Graph API credentials.
"""
import logging
import time
from pathlib import Path

import requests

from config import (
    META_ACCESS_TOKEN,
    FACEBOOK_PAGE_ID
)
from shared_utils import (
    fetch_shows,
    fetch_movies,
    load_posted_content,
    save_posted_content,
    format_show_for_facebook,
    format_movie_for_facebook,
    get_promotion_message_facebook
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Tracking file
POSTED_FILE = "facebook_posted.json"

# Facebook Graph API base URL
GRAPH_API_URL = "https://graph.facebook.com/v18.0"


def post_to_facebook(message: str, image_url: str = None) -> bool:
    """Post to Facebook Page (text + link for now, photos require App Review)."""
    if not META_ACCESS_TOKEN or not FACEBOOK_PAGE_ID:
        logger.error("Facebook credentials not set!")
        return False
    
    try:
        # Post as text with link (photos require App Review)
        url = f"{GRAPH_API_URL}/{FACEBOOK_PAGE_ID}/feed"
        params = {
            "message": message,
            "access_token": META_ACCESS_TOKEN
        }
        
        response = requests.post(url, params=params)
        response.raise_for_status()
        
        return True
    except Exception as e:
        logger.error(f"Error posting to Facebook: {e}")
        return False


def post_one_item(item_type: str = None):
    """Post ONE show or movie to Facebook Page."""
    if not META_ACCESS_TOKEN or not FACEBOOK_PAGE_ID:
        logger.error("Facebook API credentials not set!")
        logger.error("Set META_ACCESS_TOKEN and FACEBOOK_PAGE_ID in .env")
        return
    
    posted = load_posted_content(POSTED_FILE)
    
    # Fetch content
    logger.info("Fetching content...")
    shows = fetch_shows()
    movies = fetch_movies()
    
    # Find unposted content
    unposted_shows = [s for s in shows if s.get('id') not in posted.get("shows", [])]
    unposted_movies = [m for m in movies if m.get('id') not in posted.get("movies", [])]
    
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
        message = format_show_for_facebook(item)
    else:
        message = format_movie_for_facebook(item)
    
    logger.info(f"📢 Posting {item_type}: {title}")
    
    if post_to_facebook(message, poster):
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
    print("\n📘 StreamVault Facebook Bot")
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


