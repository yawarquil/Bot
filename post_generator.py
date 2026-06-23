"""
StreamVault Post Generator
Generates post content and downloads images for manual posting to Creator Studio.
"""
import os
import json
import logging
import requests
from pathlib import Path
from datetime import datetime

from shared_utils import (
    fetch_shows, fetch_movies, fetch_anime,
    format_show_for_instagram, format_movie_for_instagram, format_anime_for_instagram,
    STREAMVAULT_BASE_URL
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Output directory for generated posts
OUTPUT_DIR = Path("generated_posts")
POSTED_FILE = "generator_posted.json"


def load_posted_content() -> dict:
    try:
        if Path(POSTED_FILE).exists():
            with open(POSTED_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"shows": [], "movies": [], "anime": [], "last_type": "movie"}


def save_posted_content(data: dict):
    with open(POSTED_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def download_image(url: str, filename: str) -> str:
    """Download image and save locally."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        filepath = OUTPUT_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return str(filepath)
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None


def generate_post(item_type: str = None):
    """Generate post content and download image."""
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    posted = load_posted_content()
    
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
        logger.info("✅ All content has been processed!")
        return
    
    # Select item
    item = None
    
    if item_type == "show":
        if unposted_shows:
            item = unposted_shows[0]
        else:
            logger.info("❌ No unposted shows!")
            return
    elif item_type == "movie":
        if unposted_movies:
            item = unposted_movies[0]
        else:
            logger.info("❌ No unposted movies!")
            return
    elif item_type == "anime":
        if unposted_anime:
            item = unposted_anime[0]
        else:
            logger.info("❌ No unposted anime!")
            return
    else:
        # Auto-alternate
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
        return
    
    # Get item details
    item_id = item.get('id')
    title = item.get('title', 'Unknown')
    poster_url = item.get('posterUrl', '')
    slug = item.get('slug', '')
    
    # Generate caption
    if item_type == "show":
        caption = format_show_for_instagram(item)
    elif item_type == "anime":
        caption = format_anime_for_instagram(item)
    else:
        caption = format_movie_for_instagram(item)
    
    logger.info(f"📢 Generating post for: {title}")
    
    # Create timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
    
    # Download poster
    image_path = None
    if poster_url and poster_url.startswith('http'):
        image_filename = f"{timestamp}_{safe_title}.jpg"
        image_path = download_image(poster_url, image_filename)
        if image_path:
            logger.info(f"📷 Image saved: {image_path}")
    
    # Save caption to text file
    caption_filename = f"{timestamp}_{safe_title}_caption.txt"
    caption_path = OUTPUT_DIR / caption_filename
    with open(caption_path, 'w', encoding='utf-8') as f:
        f.write(caption)
    logger.info(f"📝 Caption saved: {caption_path}")
    
    # Mark as posted
    if item_type == "show":
        posted["shows"].append(item_id)
    elif item_type == "anime":
        if "anime" not in posted:
            posted["anime"] = []
        posted["anime"].append(item_id)
    else:
        posted["movies"].append(item_id)
    posted["last_type"] = item_type
    save_posted_content(posted)
    
    # Print summary
    print("\n" + "=" * 50)
    print("✅ POST GENERATED!")
    print("=" * 50)
    print(f"📺 Title: {title}")
    print(f"📷 Image: {image_path}")
    print(f"📝 Caption: {caption_path}")
    print("=" * 50)
    print("\n📋 CAPTION (copy this):\n")
    print(caption)
    print("\n" + "=" * 50)
    print("📌 Next steps:")
    print("1. Open Creator Studio: business.facebook.com/creatorstudio")
    print("2. Click 'Create Post'")
    print("3. Upload the image from: generated_posts/")
    print("4. Paste the caption above")
    print("5. Post or Schedule!")
    print("=" * 50)


if __name__ == "__main__":
    print("\n📱 StreamVault Post Generator")
    print("=" * 40)
    print("Generates content for Creator Studio")
    print("=" * 40)
    print("1. Generate Show Post")
    print("2. Generate Movie Post")
    print("3. Generate Anime Post")
    print("4. Auto (alternate)")
    print("=" * 40)
    
    choice = input("Choose (1/2/3/4): ").strip()
    
    if choice == "1":
        generate_post("show")
    elif choice == "2":
        generate_post("movie")
    elif choice == "3":
        generate_post("anime")
    else:
        generate_post()
