"""
Plex webhook listener — receives Plex events and sends Telegram notifications.

Register this URL in Plex: Settings → Webhooks → Add Webhook
  http://<server-ip>:<plex_webhook_port>/plex
"""
import io
import json
import requests
from aiohttp import web
from log import set_up_logger
import plex_helper
import settings as _settings

logger = set_up_logger(__name__, False, False)

# Events we notify on by default
DEFAULT_EVENTS = {"media.play", "media.resume", "media.scrobble"}

_EMOJI = {
    "media.play": "▶️",
    "media.resume": "⏯️",
    "media.pause": "⏸️",
    "media.stop": "⏹️",
    "media.scrobble": "✅",
    "library.new": "🆕",
}
_LABEL = {
    "media.play": "Now Playing",
    "media.resume": "Resumed",
    "media.pause": "Paused",
    "media.stop": "Stopped",
    "media.scrobble": "Watched",
    "library.new": "New in Library",
}


def _fetch_poster(payload: dict):
    """Fetch the poster from Plex and return a BytesIO, or None on failure."""
    meta = payload.get("Metadata", {})
    media_type = meta.get("type", "")

    # For episodes use the show poster; for everything else use the item thumb
    if media_type == "episode":
        thumb_path = meta.get("grandparentThumb") or meta.get("thumb")
    else:
        thumb_path = meta.get("thumb")

    if not thumb_path:
        return None

    plex_url = getattr(_settings, "plex_url", "http://localhost:32400")
    plex_token = getattr(_settings, "plex_token", "")
    if not plex_token:
        return None

    url = f"{plex_url}{thumb_path}"
    try:
        resp = requests.get(url, params={"X-Plex-Token": plex_token}, timeout=5)
        resp.raise_for_status()
        return io.BytesIO(resp.content)
    except Exception as e:
        logger.warning(f"Could not fetch Plex poster from {thumb_path}: {e}")
        return None


def _format_notification(payload: dict) -> str:
    event = payload.get("event", "")
    emoji = _EMOJI.get(event, "📺")
    label = _LABEL.get(event, event)

    meta = payload.get("Metadata", {})
    media_type = meta.get("type", "")
    title = meta.get("title", "Unknown")
    year = meta.get("year", "")

    account = payload.get("Account", {})
    player = payload.get("Player", {})
    user = account.get("title", "Unknown")
    device = player.get("title", "Unknown")

    if media_type == "episode":
        show = meta.get("grandparentTitle", "")
        season = meta.get("parentIndex", "?")
        episode = meta.get("index", "?")
        try:
            content = f"📺 <b>{show}</b> S{int(season):02d}E{int(episode):02d} — {title}"
        except (ValueError, TypeError):
            content = f"📺 <b>{show}</b> — {title}"
    elif media_type == "movie":
        content = f"🎬 <b>{title}</b>" + (f" ({year})" if year else "")
    elif media_type == "track":
        artist = meta.get("grandparentTitle", "")
        content = f"🎵 <b>{artist}</b> — {title}"
    else:
        content = f"<b>{title}</b>"

    lines = [
        f"{emoji} <b>{label}</b>",
        content,
        f"👤 {user}  •  📱 {device}",
    ]
    return "\n".join(lines)


async def _handle_plex_webhook(request: web.Request, bot, admin_ids: list, events: set) -> web.Response:
    try:
        data = await request.post()
        raw = data.get("payload")
        if not raw:
            return web.Response(status=400, text="Missing payload field")

        payload = json.loads(raw)
        event = payload.get("event", "")

        if event not in events:
            logger.debug(f"Ignoring Plex event: {event}")
            return web.Response(status=200, text="OK")

        logger.info(f"Plex event: {event}")
        text = _format_notification(payload)
        poster = _fetch_poster(payload)

        for uid in admin_ids:
            try:
                if poster:
                    await bot.send_photo(
                        chat_id=int(uid),
                        photo=poster,
                        caption=text,
                        parse_mode="HTML",
                    )
                    poster.seek(0)  # reset for next recipient
                else:
                    await bot.send_message(chat_id=int(uid), text=text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to send Plex notification to {uid}: {e}")

    except Exception as e:
        logger.error(f"Error handling Plex webhook: {e}")

    return web.Response(status=200, text="OK")


async def start_webhook_server(bot, admin_ids: list, port: int = 32401, events: set = None):
    if events is None:
        events = DEFAULT_EVENTS

    app = web.Application()
    app.router.add_post("/plex", lambda r: _handle_plex_webhook(r, bot, admin_ids, events))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Plex webhook server listening on port {port} — register http://<ip>:{port}/plex in Plex settings")
    return runner
