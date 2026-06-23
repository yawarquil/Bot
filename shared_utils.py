"""
Shared utilities for all social media bots.
Contains common functions for fetching content and formatting messages.
"""
import json
import logging
from pathlib import Path
import requests

from config import (
    STREAMVAULT_API_SHOWS,
    STREAMVAULT_API_MOVIES,
    STREAMVAULT_API_ANIME,
    STREAMVAULT_API_KEY,
    STREAMVAULT_BASE_URL,
    CHANNEL_INVITE_LINK,
    WEBSITE_URL
)

logger = logging.getLogger(__name__)


def load_posted_content(file_path: str) -> dict:
    """Load posted content tracking file."""
    try:
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"shows": [], "movies": [], "anime": [], "failed_shows": [], "failed_movies": [], "failed_anime": [], "last_type": "movie"}


def save_posted_content(data: dict, file_path: str):
    """Save posted content tracking file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def fetch_content(api_url: str) -> list:
    """Fetch content from StreamVault API."""
    try:
        response = requests.get(
            api_url,
            headers={"X-API-Key": STREAMVAULT_API_KEY} if STREAMVAULT_API_KEY else {},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching from {api_url}: {e}")
        return []


def fetch_shows() -> list:
    """Fetch all shows."""
    return fetch_content(STREAMVAULT_API_SHOWS)


def fetch_movies() -> list:
    """Fetch all movies."""
    return fetch_content(STREAMVAULT_API_MOVIES)


def fetch_anime() -> list:
    """Fetch all anime."""
    return fetch_content(STREAMVAULT_API_ANIME)


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length-3].rsplit(' ', 1)[0] + "..."


def clean_text(text: str) -> str:
    """Remove special characters that can cause issues."""
    if not text:
        return ""
    # Remove asterisks and other problematic chars
    for char in ['*', '_', '`', '~']:
        text = text.replace(char, '')
    return text


def get_show_url(slug: str) -> str:
    """Get the watch URL for a show."""
    return f"{STREAMVAULT_BASE_URL}/show/{slug}"


def get_movie_url(slug: str) -> str:
    """Get the watch URL for a movie."""
    return f"{STREAMVAULT_BASE_URL}/movie/{slug}"


def get_anime_url(slug: str) -> str:
    """Get the watch URL for an anime."""
    return f"{STREAMVAULT_BASE_URL}/anime/{slug}"


def get_season_url(slug: str, season: int) -> str:
    """Get direct season link."""
    return f"{STREAMVAULT_BASE_URL}/watch/{slug}?season={season}&episode=1"


# Genre to hashtag mapping
GENRE_HASHTAGS = {
    "action": ["#Action", "#ActionMovies", "#Thriller"],
    "comedy": ["#Comedy", "#Funny", "#LOL"],
    "drama": ["#Drama", "#DramaMovies", "#Emotional"],
    "horror": ["#Horror", "#Scary", "#HorrorMovies"],
    "romance": ["#Romance", "#Love", "#RomCom"],
    "sci-fi": ["#SciFi", "#ScienceFiction", "#Futuristic"],
    "thriller": ["#Thriller", "#Suspense", "#Mystery"],
    "crime": ["#Crime", "#CrimeDrama", "#Detective"],
    "fantasy": ["#Fantasy", "#Magic", "#Epic"],
    "animation": ["#Animation", "#Animated", "#Cartoon"],
    "documentary": ["#Documentary", "#RealStory", "#TrueStory"],
    "adventure": ["#Adventure", "#Epic", "#Journey"],
    "mystery": ["#Mystery", "#Suspense", "#WhoDidIt"],
    "family": ["#Family", "#FamilyFriendly", "#Kids"],
    "war": ["#War", "#Military", "#Historical"],
    "western": ["#Western", "#Cowboys", "#Classic"],
    "musical": ["#Musical", "#Music", "#Songs"],
    "sport": ["#Sports", "#Inspirational", "#GameDay"],
    "biography": ["#Biography", "#TrueStory", "#Inspirational"],
    "history": ["#History", "#Historical", "#Period"],
}

# Trending hashtags for social media
TRENDING_SHOW_TAGS = ["#NowWatching", "#BingeWatch", "#MustWatch", "#Trending", "#Viral", "#FYP"]
TRENDING_MOVIE_TAGS = ["#MovieNight", "#WeekendVibes", "#MustWatch", "#Trending", "#Viral", "#FYP"]


def generate_hashtags(genres: str, is_show: bool = True, title: str = "") -> str:
    """Generate 5-6 relevant hashtags based on genres and trending tags."""
    hashtags = []
    
    # ALWAYS add title hashtag first
    if title:
        clean_title = ''.join(c for c in title if c.isalnum())
        if clean_title:
            hashtags.append(f"#{clean_title}")
    
    # Add Netflix for both shows and movies
    hashtags.append("#Netflix")
    
    # Add type-specific hashtag
    if is_show:
        hashtags.append("#TVShows")
    else:
        hashtags.append("#Movies")
    
    # Add genre-based hashtags
    if genres:
        for genre in genres.lower().split(", ")[:2]:
            genre = genre.strip()
            if genre in GENRE_HASHTAGS:
                hashtags.append(GENRE_HASHTAGS[genre][0])
    
    # Add StreamVault
    hashtags.append("#StreamVault")
    
    # Limit to 6 hashtags
    return " ".join(hashtags[:6])


# ==================== TWITTER FORMAT ====================

def format_show_for_twitter(show: dict) -> str:
    """Format show for Twitter (280 char limit)."""
    title = clean_text(show.get('title', 'Unknown'))
    year = show.get('year') or show.get('releaseYear', '')
    rating = show.get('imdbRating', 'N/A')
    genres = clean_text(show.get('genres', ''))
    slug = show.get('slug', '')
    total_seasons = show.get('totalSeasons', 0)
    
    url = get_show_url(slug)
    hashtags = generate_hashtags(genres, is_show=True, title=title)
    
    tweet = f"""📺 {title.upper()}"""
    if year:
        tweet += f" ({year})"
    tweet += f"""
⭐ {rating} | {genres}
📂 {total_seasons} Seasons

🔗 {url}

{hashtags}"""
    
    return tweet[:280]


def format_movie_for_twitter(movie: dict) -> str:
    """Format movie for Twitter (280 char limit)."""
    title = clean_text(movie.get('title', 'Unknown'))
    year = movie.get('year', '')
    rating = movie.get('imdbRating', 'N/A')
    genres = clean_text(movie.get('genres', ''))
    slug = movie.get('slug', '')
    
    url = get_movie_url(slug)
    hashtags = generate_hashtags(genres, is_show=False, title=title)
    
    tweet = f"""🎬 {title.upper()}"""
    if year:
        tweet += f" ({year})"
    tweet += f"""
⭐ {rating} | {genres}

🔗 {url}

{hashtags}"""
    
    return tweet[:280]


# ==================== INSTAGRAM FORMAT ====================

def format_show_for_instagram(show: dict) -> str:
    """Format show for Instagram caption (same as Twitter)."""
    title = clean_text(show.get('title', 'Unknown'))
    year = show.get('year') or show.get('releaseYear', '')
    rating = show.get('imdbRating', 'N/A')
    genres = clean_text(show.get('genres', ''))
    slug = show.get('slug', '')
    total_seasons = show.get('totalSeasons', 0)
    
    url = get_show_url(slug)
    hashtags = generate_hashtags(genres, is_show=True, title=title)
    
    caption = f"""📺 {title.upper()}"""
    if year:
        caption += f" ({year})"
    caption += f"""
⭐ {rating} | {genres}
📂 {total_seasons} Seasons

🔗 {url}

{hashtags}"""
    
    return caption


def format_movie_for_instagram(movie: dict) -> str:
    """Format movie for Instagram caption (same as Twitter)."""
    title = clean_text(movie.get('title', 'Unknown'))
    year = movie.get('year', '')
    rating = movie.get('imdbRating', 'N/A')
    genres = clean_text(movie.get('genres', ''))
    slug = movie.get('slug', '')
    
    url = get_movie_url(slug)
    hashtags = generate_hashtags(genres, is_show=False, title=title)
    
    caption = f"""🎬 {title.upper()}"""
    if year:
        caption += f" ({year})"
    caption += f"""
⭐ {rating} | {genres}

🔗 {url}

{hashtags}"""
    
    return caption


# ==================== FACEBOOK FORMAT ====================

def format_show_for_facebook(show: dict) -> str:
    """Format show for Facebook post."""
    # Facebook allows longer posts, similar to Instagram
    return format_show_for_instagram(show)


def format_movie_for_facebook(movie: dict) -> str:
    """Format movie for Facebook post."""
    return format_movie_for_instagram(movie)


# ==================== ANIME FORMAT ====================

def format_anime_for_twitter(anime: dict) -> str:
    """Format anime for Twitter (280 char limit)."""
    title = clean_text(anime.get('title', 'Unknown'))
    year = anime.get('year', '')
    rating = anime.get('imdbRating', 'N/A')
    genres = clean_text(anime.get('genres', ''))
    slug = anime.get('slug', '')
    total_episodes = anime.get('totalEpisodes', 0)
    
    url = get_anime_url(slug)
    hashtags = f"#{title.replace(' ', '').replace('-', '')[:15]} #Anime #AnimeFans #Otaku #StreamVault"
    
    tweet = f"""🎌 {title.upper()}"""
    if year:
        tweet += f" ({year})"
    tweet += f"""
⭐ {rating} | {genres}
📺 {total_episodes} Episodes

🔗 {url}

{hashtags}"""
    
    return tweet[:280]


def format_anime_for_instagram(anime: dict) -> str:
    """Format anime for Instagram caption."""
    title = clean_text(anime.get('title', 'Unknown'))
    year = anime.get('year', '')
    rating = anime.get('imdbRating', 'N/A')
    genres = clean_text(anime.get('genres', ''))
    slug = anime.get('slug', '')
    total_episodes = anime.get('totalEpisodes', 0)
    studio = clean_text(anime.get('studio', ''))
    
    url = get_anime_url(slug)
    hashtags = f"#{title.replace(' ', '').replace('-', '')[:15]} #Anime #AnimeFans #Otaku #Weeb #JapaneseAnime #StreamVault"
    
    caption = f"""🎌 {title.upper()}"""
    if year:
        caption += f" ({year})"
    caption += f"""
⭐ {rating} | {genres}
📺 {total_episodes} Episodes"""
    if studio:
        caption += f"\n🎬 Studio: {studio}"
    caption += f"""

🔗 {url}

{hashtags}"""
    
    return caption


def format_anime_for_facebook(anime: dict) -> str:
    """Format anime for Facebook post."""
    return format_anime_for_instagram(anime)


# ==================== PROMOTION MESSAGES ====================

def get_promotion_message_twitter() -> str:
    """Promotion message for Twitter."""
    return f"""🎬 StreamVault - Free Movies & TV Shows!

📺 HD Quality Streaming
🆓 100% Free - No Ads
🌍 Multi-Language Content

👉 {CHANNEL_INVITE_LINK}
🌐 {WEBSITE_URL}

#FreeMovies #FreeTV #Streaming #StreamVault"""


def get_promotion_message_instagram() -> str:
    """Promotion message for Instagram."""
    return f"""📢 JOIN STREAMVAULT

━━━━━━━━━━━━━━━━━━━━━

🎬 Latest Movies & TV Shows
📺 HD Quality Streaming
🆓 100% Free - No Ads
🌍 Multi-Language Content

━━━━━━━━━━━━━━━━━━━━━

👉 Telegram: {CHANNEL_INVITE_LINK}
🌐 Website: {WEBSITE_URL}

━━━━━━━━━━━━━━━━━━━━━

📲 Share with friends! 🎉

#StreamVault #FreeMovies #FreeTVShows #Streaming #WatchOnline #Movies #TVSeries #Netflix #Amazon #Hollywood #Bollywood"""


def get_promotion_message_facebook() -> str:
    """Promotion message for Facebook."""
    return get_promotion_message_instagram()
