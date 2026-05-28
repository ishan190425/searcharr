"""
Plex integration — fetches active playback sessions and formats them for Telegram.
"""
import xml.etree.ElementTree as ET
from typing import Optional
import requests
from log import set_up_logger

logger = set_up_logger(__name__, False, False)


class PlexUnreachable(Exception):
    pass


def get_sessions(url: str, token: str) -> ET.Element:
    endpoint = f"{url}/status/sessions"
    try:
        resp = requests.get(endpoint, params={"X-Plex-Token": token}, timeout=5)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise PlexUnreachable(f"Could not connect to Plex at {url}")
    except requests.exceptions.Timeout:
        raise PlexUnreachable(f"Plex timed out at {url}")
    except requests.exceptions.RequestException as e:
        raise PlexUnreachable(str(e))
    return ET.fromstring(resp.text)


def _ms_to_hhmm(ms: int) -> str:
    total_secs = ms // 1000
    h, rem = divmod(total_secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _progress_bar(elapsed_ms: int, duration_ms: int, width: int = 10) -> str:
    if not duration_ms:
        return "─" * width
    filled = round(width * elapsed_ms / duration_ms)
    filled = max(0, min(width, filled))
    bar = "█" * filled + "─" * (width - filled)
    return f"[{bar}]"


def _format_session(el: ET.Element) -> str:
    media_type = el.get("type", "")
    title = el.get("title", "Unknown")
    year = el.get("year", "")
    duration_ms = int(el.get("duration") or 0)
    offset_ms = int(el.get("viewOffset") or 0)

    user_el = el.find("User")
    player_el = el.find("Player")
    user = user_el.get("title", "Unknown") if user_el is not None else "Unknown"
    device = player_el.get("title", "Unknown") if player_el is not None else "Unknown"
    state = player_el.get("state", "") if player_el is not None else ""

    if media_type == "episode":
        show = el.get("grandparentTitle", "")
        season = el.get("parentIndex", "?")
        episode = el.get("index", "?")
        label = f"📺 <b>{show}</b> S{int(season):02d}E{int(episode):02d} — {title}"
    elif media_type == "movie":
        label = f"🎬 <b>{title}</b>" + (f" ({year})" if year else "")
    elif media_type == "track":
        artist = el.get("grandparentTitle", "")
        label = f"🎵 <b>{artist}</b> — {title}"
    else:
        label = f"▶️ <b>{title}</b>"

    bar = _progress_bar(offset_ms, duration_ms)
    time_str = f"{_ms_to_hhmm(offset_ms)} / {_ms_to_hhmm(duration_ms)}" if duration_ms else ""
    pause_icon = " ⏸" if state == "paused" else ""

    lines = [label]
    if time_str:
        lines.append(f"{bar} {time_str}{pause_icon}")
    lines.append(f"👤 {user}  •  📱 {device}")
    return "\n".join(lines)


def format_nowplaying(root: ET.Element) -> Optional[str]:
    sessions = root.findall("Video") + root.findall("Track")
    if not sessions:
        return None
    return "\n\n".join(_format_session(el) for el in sessions)
