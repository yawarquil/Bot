"""
StreamVault Telegram Bot — One post per hour, alternating movie/show/anime.
Includes health check server for Render/UptimeRobot.
"""
import json
import time
import asyncio
import logging
from pathlib import Path

import requests
from telegram import Bot
from telegram.constants import ParseMode

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_ID,
    STREAMVAULT_API_SHOWS,
    STREAMVAULT_API_MOVIES,
    STREAMVAULT_API_ANIME,
    STREAMVAULT_API_KEY,
    STREAMVAULT_BASE_URL,
    POSTED_CONTENT_FILE,
    CHANNEL_INVITE_LINK,
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

POST_ORDER = ["movie", "show", "anime"]
POSTED_FILE = POSTED_CONTENT_FILE  # reuse existing tracking


def load_state() -> dict:
    try:
        if Path(POSTED_FILE).exists():
            with open(POSTED_FILE) as f:
                data = json.load(f)
                for k in ["shows", "movies", "anime", "failed_shows", "failed_movies", "failed_anime"]:
                    data.setdefault(k, [])
                data.setdefault("next_type", "movie")
                return data
    except:
        pass
    return {"shows": [], "movies": [], "anime": [], "failed_shows": [], "failed_movies": [], "failed_anime": [], "next_type": "movie"}


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


def truncate_text(text: str, max_length: int = 200) -> str:
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length-3].rsplit(" ", 1)[0] + "..."


def escape_markdown(text: str) -> str:
    if not text:
        return text
    text = text.replace("*", "")
    for char in ["_", "`", "[", "]", "(", ")", "~"]:
        text = text.replace(char, "\\" + char)
    return text


def fmt_show(show: dict) -> str:
    title = escape_markdown(show.get("title", "Unknown"))
    year = show.get("year") or show.get("releaseYear", "")
    slug = show.get("slug", "")
    desc = escape_markdown(truncate_text(show.get("description", "")))
    rating = show.get("imdbRating", "N/A")
    genres = escape_markdown(show.get("genres", "N/A"))
    lang = show.get("language", "N/A")
    seasons = show.get("totalSeasons", 0)
    cast = escape_markdown(show.get("cast", ""))

    msgs = [
        f"📺 *{title.upper()}*" + (f" ({year})" if year else ""),
        "",
        f"⭐ {rating} │ 🎭 {genres}",
        f"🌐 {lang}",
        "",
        f"📖 _{desc}_",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
    ]

    if seasons:
        msgs.append(f"📂 *Seasons:* {seasons}")
        msgs.append("")
        for s in range(1, int(seasons) + 1):
            msgs.append(f"▸ [S{s}]({STREAMVAULT_BASE_URL}/watch/{slug}?season={s}&episode=1)")
        msgs.append("")
        msgs.append("━━━━━━━━━━━━━━━━━━━━━")

    if cast:
        c = ", ".join(cast.split(", ")[:4])
        if len(cast.split(", ")) > 4:
            c += "..."
        msgs.extend(["", f"🎭 *Cast:* {c}"])

    msgs.extend(["", f"🔗 *Watch:* [StreamVault]({STREAMVAULT_BASE_URL}/show/{slug})", f"📢 *Join:* {CHANNEL_INVITE_LINK}"])
    return "\n".join(msgs)


def fmt_movie(movie: dict) -> str:
    title = escape_markdown(movie.get("title", "Unknown"))
    year = movie.get("year", "")
    slug = movie.get("slug", "")
    desc = escape_markdown(truncate_text(movie.get("description", "")))
    rating = movie.get("imdbRating", "N/A")
    genres = escape_markdown(movie.get("genres", "N/A"))
    lang = movie.get("language", "N/A")
    dur = movie.get("duration", "")
    cast = escape_markdown(movie.get("cast", ""))
    directors = escape_markdown(movie.get("directors", ""))

    msgs = [
        f"🎬 *{title.upper()}*" + (f" ({year})" if year else ""),
        "",
        f"⭐ {rating} │ 🎭 {genres}" + (f" │ ⏱ {dur} min" if dur else ""),
        f"🌐 {lang}",
        "",
        f"📖 _{desc}_",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
    ]

    if directors:
        msgs.append(f"🎬 *Director:* {directors}")
    if cast:
        c = ", ".join(cast.split(", ")[:4])
        if len(cast.split(", ")) > 4:
            c += "..."
        msgs.append(f"🎭 *Cast:* {c}")

    msgs.append("━━━━━━━━━━━━━━━━━━━━━")
    msgs.extend(["", f"🔗 *Watch:* [StreamVault]({STREAMVAULT_BASE_URL}/movie/{slug})", f"📢 *Join:* {CHANNEL_INVITE_LINK}"])
    return "\n".join(msgs)


def fmt_anime(anime: dict) -> str:
    title = escape_markdown(anime.get("title", "Unknown"))
    alt = escape_markdown(anime.get("alternativeTitles", "") or "")
    year = anime.get("year", "")
    slug = anime.get("slug", "")
    desc = escape_markdown(truncate_text(anime.get("description", "")))
    rating = anime.get("imdbRating", "N/A")
    genres = escape_markdown(anime.get("genres", "N/A"))
    lang = anime.get("language", "Japanese")
    eps = anime.get("totalEpisodes", 0)
    seasons = anime.get("totalSeasons", 1)
    studio = escape_markdown(anime.get("studio", ""))
    status = anime.get("status", "Completed")
    cast = escape_markdown(anime.get("cast", ""))

    msgs = [f"🎌 *{title.upper()}*" + (f" ({year})" if year else "")]
    if alt:
        msgs.append(f"_{alt}_")
    msgs.extend([
        "",
        f"⭐ {rating} │ 🎭 {genres}",
        f"🌐 {lang} │ 🎬 {studio}" if studio else f"🌐 {lang}",
        f"📺 {eps} Episodes │ 📁 {seasons} Season{'s' if seasons != 1 else ''}",
        f"🟢 {status}",
        "",
        f"📖 _{desc}_",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
    ])
    if cast:
        c = ", ".join(cast.split(", ")[:4])
        if len(cast.split(", ")) > 4:
            c += "..."
        msgs.append(f"🎭 *Cast:* {c}")
    msgs.append("━━━━━━━━━━━━━━━━━━━━━")
    msgs.extend(["", f"🔗 *Watch:* [StreamVault]({STREAMVAULT_BASE_URL}/anime/{slug})", f"📢 *Join:* {CHANNEL_INVITE_LINK}"])
    return "\n".join(msgs)


FORMATTERS = {"show": fmt_show, "movie": fmt_movie, "anime": fmt_anime}
API_URLS = {"show": STREAMVAULT_API_SHOWS, "movie": STREAMVAULT_API_MOVIES, "anime": STREAMVAULT_API_ANIME}
KEY_MAP = {"show": "shows", "movie": "movies", "anime": "anime"}


async def post_one(bot: Bot, item_type: str, state: dict) -> bool:
    """Post one item of given type. Returns True if posted."""
    key = KEY_MAP[item_type]
    posted_ids = state.get(key, [])
    items = fetch_content(API_URLS[item_type])

    if not items:
        logger.warning(f"No {item_type}s fetched!")
        return False

    for item in items:
        item_id = item.get("id")
        if item_id in posted_ids:
            continue

        title = item.get("title", "Unknown")
        message = FORMATTERS[item_type](item)
        poster = item.get("posterUrl", "")

        try:
            if poster and poster.startswith("http"):
                try:
                    await bot.send_photo(TELEGRAM_CHANNEL_ID, photo=poster, caption=message, parse_mode=ParseMode.MARKDOWN)
                except Exception:
                    await bot.send_message(TELEGRAM_CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN)
            else:
                await bot.send_message(TELEGRAM_CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN)

            state[key].append(item_id)
            save_state(state)
            logger.info(f"Posted {item_type}: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed {item_type} '{title}': {e}")
            return False

    # All posted — reset and loop
    logger.info(f"All {item_type}s posted! Resetting...")
    state[key] = []
    save_state(state)
    items2 = fetch_content(API_URLS[item_type])
    if items2:
        item = items2[0]
        message = FORMATTERS[item_type](item)
        try:
            await bot.send_message(TELEGRAM_CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN)
            state[key].append(item["id"])
            save_state(state)
            logger.info(f"Posted {item_type}: {item.get('title')} (loop)")
            return True
        except Exception as e:
            logger.error(f"Loop restart failed: {e}")
    return False


async def posting_loop():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    state = load_state()

    # Post promotion once
    logger.info("Posting promotion...")
    try:
        promo = (
            "📢 *JOIN STREAMVAULT*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎬 *Latest Movies & TV Shows*\n"
            "📺 *HD Quality Streaming*\n"
            "🆓 *100% Free \\- No Ads*\n"
            "🌍 *Multi\\-Language Content*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👉 *Telegram:* {CHANNEL_INVITE_LINK}\n"
            "🌐 *Website:* streamvault.live & streamvault.in\n"
            "🐦 *Twitter:* twitter.streamvault.in\n"
            "📷 *Instagram:* instagram.streamvault.in\n"
            "📘 *Facebook:* facebook.streamvault.in\n"
            "💚 *WhatsApp:* whatsapp.streamvault.in\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📲 *Share with friends!* 🎉"
        )
        msg = await bot.send_message(TELEGRAM_CHANNEL_ID, text=promo, parse_mode=ParseMode.MARKDOWN)
        await bot.pin_chat_message(TELEGRAM_CHANNEL_ID, message_id=msg.message_id, disable_notification=True)
        logger.info("Promotion pinned!")
    except Exception as e:
        logger.error(f"Promotion failed: {e}")

    await asyncio.sleep(5)

    idx = POST_ORDER.index(state.get("next_type", "movie"))

    while True:
        item_type = POST_ORDER[idx]
        logger.info(f"--- Posting {item_type} ---")
        await post_one(bot, item_type, state)

        idx = (idx + 1) % len(POST_ORDER)
        state["next_type"] = POST_ORDER[idx]
        save_state(state)

        logger.info("Waiting 1 hour...")
        await asyncio.sleep(3600)


# ── Entry ──

if __name__ == "__main__":
    import sys

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    asyncio.run(posting_loop())
