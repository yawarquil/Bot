"""
StreamVault Discord Bot — One post per hour, alternating movie/show/anime.
Posts to type-specific channels. Includes health check server for Render/UptimeRobot.
"""
import json
import time
import logging
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests

from config import (
    STREAMVAULT_API_SHOWS,
    STREAMVAULT_API_MOVIES,
    STREAMVAULT_API_ANIME,
    STREAMVAULT_API_KEY,
    STREAMVAULT_BASE_URL,
    CHANNEL_INVITE_LINK,
    DISCORD_BOT_TOKEN,
    DISCORD_CHANNEL_ID,
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v10"
POSTED_FILE = "discord_posted.json"

# ── Type-specific channels ──
CHANNELS = {
    "movie": 1518946150135234722,   # #🎬-movies
    "show":  1518948924822523954,   # #📺-tv-shows
    "anime": 1518948929264292001,   # #🎌-anime
}

ANN_CHANNEL = int(DISCORD_CHANNEL_ID) if DISCORD_CHANNEL_ID else 1518948905352433835

# Posting order
POST_ORDER = ["movie", "show", "anime"]

# Health check port
HEALTH_PORT = int(__import__("os").getenv("PORT", "10000"))


def headers():
    return {"Authorization": f"Bot {DISCORD_BOT_TOKEN}", "Content-Type": "application/json"}


# ── State ──

def load_state() -> dict:
    try:
        if Path(POSTED_FILE).exists():
            with open(POSTED_FILE) as f:
                return json.load(f)
    except:
        pass
    return {"movies": [], "shows": [], "anime": [], "next_type": "movie"}


def save_state(data: dict):
    with open(POSTED_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fetch_content(api_url: str) -> list:
    try:
        r = requests.get(
            api_url,
            headers={"X-API-Key": STREAMVAULT_API_KEY} if STREAMVAULT_API_KEY else {},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return []


# ── Embeds ──

def build_show_embed(show: dict) -> dict:
    title = show.get("title", "Unknown")
    year = show.get("year") or show.get("releaseYear", "")
    slug = show.get("slug", "")
    desc = (show.get("description", "") or "")[:200]
    if len(show.get("description", "") or "") > 200:
        desc = desc.rsplit(" ", 1)[0] + "..."

    embed = {
        "title": f"📺 {title.upper()}" + (f" ({year})" if year else ""),
        "description": f"📖 *{desc}*" if desc else "",
        "color": 0x3498db,
        "url": f"{STREAMVAULT_BASE_URL}/show/{slug}",
        "fields": [
            {"name": "⭐ Rating", "value": str(show.get("imdbRating", "N/A")), "inline": True},
            {"name": "🎭 Genres", "value": show.get("genres", "N/A"), "inline": True},
            {"name": "🌐 Language", "value": show.get("language", "N/A"), "inline": True},
        ],
        "footer": {"text": f"StreamVault • {CHANNEL_INVITE_LINK}"},
    }
    seasons = show.get("totalSeasons", 0)
    if seasons:
        embed["fields"].append({"name": "📂 Seasons", "value": str(seasons), "inline": True})
    cast = show.get("cast", "")
    if cast:
        c = ", ".join(cast.split(", ")[:4])
        if len(cast.split(", ")) > 4:
            c += "..."
        embed["fields"].append({"name": "🎭 Cast", "value": c, "inline": False})
    poster = show.get("posterUrl", "")
    if poster and poster.startswith("http"):
        embed["image"] = {"url": poster}
    return embed


def build_movie_embed(movie: dict) -> dict:
    title = movie.get("title", "Unknown")
    year = movie.get("year", "")
    slug = movie.get("slug", "")
    desc = (movie.get("description", "") or "")[:200]
    if len(movie.get("description", "") or "") > 200:
        desc = desc.rsplit(" ", 1)[0] + "..."

    embed = {
        "title": f"🎬 {title.upper()}" + (f" ({year})" if year else ""),
        "description": f"📖 *{desc}*" if desc else "",
        "color": 0xe74c3c,
        "url": f"{STREAMVAULT_BASE_URL}/movie/{slug}",
        "fields": [
            {"name": "⭐ Rating", "value": str(movie.get("imdbRating", "N/A")), "inline": True},
            {"name": "🎭 Genres", "value": movie.get("genres", "N/A"), "inline": True},
            {"name": "🌐 Language", "value": movie.get("language", "N/A"), "inline": True},
        ],
        "footer": {"text": f"StreamVault • {CHANNEL_INVITE_LINK}"},
    }
    dur = movie.get("duration", "")
    if dur:
        embed["fields"].append({"name": "⏱ Duration", "value": f"{dur} min", "inline": True})
    directors = movie.get("directors", "")
    if directors:
        embed["fields"].append({"name": "🎬 Director", "value": directors, "inline": True})
    cast = movie.get("cast", "")
    if cast:
        c = ", ".join(cast.split(", ")[:4])
        if len(cast.split(", ")) > 4:
            c += "..."
        embed["fields"].append({"name": "🎭 Cast", "value": c, "inline": False})
    poster = movie.get("posterUrl", "")
    if poster and poster.startswith("http"):
        embed["image"] = {"url": poster}
    return embed


def build_anime_embed(anime: dict) -> dict:
    title = anime.get("title", "Unknown")
    year = anime.get("year", "")
    slug = anime.get("slug", "")
    desc = (anime.get("description", "") or "")[:200]
    if len(anime.get("description", "") or "") > 200:
        desc = desc.rsplit(" ", 1)[0] + "..."

    title_text = f"🎌 {title.upper()}" + (f" ({year})" if year else "")
    alt = anime.get("alternativeTitles", "") or ""
    if alt:
        title_text += f"\n*{alt}*"

    embed = {
        "title": title_text,
        "description": f"📖 *{desc}*" if desc else "",
        "color": 0x9b59b6,
        "url": f"{STREAMVAULT_BASE_URL}/anime/{slug}",
        "fields": [
            {"name": "⭐ Rating", "value": str(anime.get("imdbRating", "N/A")), "inline": True},
            {"name": "🎭 Genres", "value": anime.get("genres", "N/A"), "inline": True},
            {"name": "🌐 Language", "value": anime.get("language", "Japanese"), "inline": True},
            {"name": "📺 Episodes", "value": str(anime.get("totalEpisodes", 0)), "inline": True},
            {"name": "📁 Seasons", "value": str(anime.get("totalSeasons", 1)), "inline": True},
            {"name": "🟢 Status", "value": anime.get("status", "Completed"), "inline": True},
        ],
        "footer": {"text": f"StreamVault • {CHANNEL_INVITE_LINK}"},
    }
    studio = anime.get("studio", "")
    if studio:
        embed["fields"].append({"name": "🎬 Studio", "value": studio, "inline": True})
    cast = anime.get("cast", "")
    if cast:
        c = ", ".join(cast.split(", ")[:4])
        if len(cast.split(", ")) > 4:
            c += "..."
        embed["fields"].append({"name": "🎭 Cast", "value": c, "inline": False})
    poster = anime.get("posterUrl", "")
    if poster and poster.startswith("http"):
        embed["image"] = {"url": poster}
    return embed


BUILDERS = {"show": build_show_embed, "movie": build_movie_embed, "anime": build_anime_embed}
API_URLS = {"show": STREAMVAULT_API_SHOWS, "movie": STREAMVAULT_API_MOVIES, "anime": STREAMVAULT_API_ANIME}


def send_embed(channel_id: int, embed: dict) -> str:
    r = requests.post(
        f"{DISCORD_API}/channels/{channel_id}/messages",
        headers=headers(),
        json={"embeds": [embed]},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["id"]


# ── Main posting loop ──

def post_one(item_type: str, state: dict) -> bool:
    """Post one item of the given type. Returns True if posted, False if nothing left."""
    key = {"movie": "movies", "show": "shows", "anime": "anime"}[item_type]
    posted_ids = state.get(key, [])
    channel_id = CHANNELS[item_type]

    items = fetch_content(API_URLS[item_type])
    if not items:
        logger.warning(f"No {item_type}s fetched!")
        return False

    for item in items:
        item_id = item.get("id")
        if item_id in posted_ids:
            continue

        title = item.get("title", "Unknown")
        embed = BUILDERS[item_type](item)

        try:
            send_embed(channel_id, embed)
            state[key].append(item_id)
            save_state(state)
            logger.info(f"Posted {item_type}: {title} -> #{channel_id}")
            return True
        except Exception as e:
            logger.error(f"Failed {item_type} '{title}': {e}")
            return False

    logger.info(f"All {item_type}s posted! Resetting list to loop...")
    # Reset so it cycles back through
    state[key] = []
    save_state(state)
    # Try again with fresh list
    items2 = fetch_content(API_URLS[item_type])
    if items2:
        item = items2[0]
        embed = BUILDERS[item_type](item)
        try:
            send_embed(channel_id, embed)
            state[key].append(item["id"])
            save_state(state)
            logger.info(f"Posted {item_type}: {item.get('title')} (loop restart)")
            return True
        except Exception as e:
            logger.error(f"Failed on loop restart: {e}")
    return False


def posting_loop():
    """Run forever: post one item per hour, alternating types."""
    logger.info("Starting posting loop (1 post/hour, alternating)...")

    # Post one-off promotion to announcements channel
    try:
        promo = {
            "title": "📢 JOIN STREAMVAULT",
            "description": "🎬 **Latest Movies & TV Shows**\n📺 **HD Quality Streaming**\n🆓 **100% Free - No Ads**\n🌍 **Multi-Language Content**",
            "color": 0xf1c40f,
            "fields": [
                {"name": "👉 Telegram", "value": CHANNEL_INVITE_LINK, "inline": False},
                {"name": "🌐 Website", "value": "streamvault.live & streamvault.in", "inline": True},
                {"name": "🐦 Twitter", "value": "twitter.streamvault.in", "inline": True},
                {"name": "📷 Instagram", "value": "instagram.streamvault.in", "inline": True},
                {"name": "📘 Facebook", "value": "facebook.streamvault.in", "inline": True},
                {"name": "💚 WhatsApp", "value": "whatsapp.streamvault.in", "inline": True},
            ],
            "footer": {"text": "📲 Share with friends! 🎉"},
        }
        mid = send_embed(ANN_CHANNEL, promo)
        # Pin
        requests.put(
            f"{DISCORD_API}/channels/{ANN_CHANNEL}/pins/{mid}",
            headers=headers(),
            timeout=30,
        )
        logger.info("Promotion posted & pinned in announcements")
    except Exception as e:
        logger.error(f"Promotion failed: {e}")

    time.sleep(5)

    state = load_state()
    idx = POST_ORDER.index(state.get("next_type", "movie"))

    while True:
        item_type = POST_ORDER[idx]
        logger.info(f"--- Posting {item_type} ---")

        posted = post_one(item_type, state)

        # Rotate to next type
        idx = (idx + 1) % len(POST_ORDER)
        state["next_type"] = POST_ORDER[idx]
        save_state(state)

        logger.info("Waiting 1 hour...")
        time.sleep(3600)  # 1 hour


# ── Health check server (for Render + UptimeRobot) ──

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # silent


def start_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    logger.info(f"Health server on :{HEALTH_PORT}")
    server.serve_forever()


# ── Entry ──
# Reaction roles are handled in discord_welcome.py (gateway events, real-time).

if __name__ == "__main__":
    import sys

    if not DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN not set!")
        sys.exit(1)

    threading.Thread(target=start_health_server, daemon=True).start()
    posting_loop()
