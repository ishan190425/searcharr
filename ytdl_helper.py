"""Shared YouTube search/download helpers used by both the CLI and the Telegram bot."""

import re
import shutil
from difflib import SequenceMatcher
from pathlib import Path

import yt_dlp

MOVIE_ROOT = Path("/mnt/media/Movies")
TV_ROOT = Path("/mnt/media/TV")
STAGING_DIR = Path("/mnt/media/staging")

_YT_JUNK = re.compile(
    r"(\s+[-–]\s+|\|).*$"          # everything after spaced dash or pipe
    r"|full\s*(movie|film|hd|comedy|video|song|audio)"
    r"|hd|4k|1080p|720p|bluray|blu.ray"
    r"|english\s*sub(title)?s?"
    r"|hindi\s*(dubbed|sub(titled)?)?|dubbed"
    r"|superhit|blockbuster|bollywood"
    r"|official\s*(trailer|video|audio|music\s*video)"
    r"|ft\.?\s*.*$|feat\.?\s*.*$"
    r"|\[.*?\]|\(.*?\)",
    re.IGNORECASE,
)

_STOPWORDS = {"a", "an", "the", "of", "and", "in", "on", "at", "to", "is", "ft", "by"}


def clean_title(title: str) -> str:
    title = _YT_JUNK.sub(" ", title)
    return re.sub(r"\s+", " ", title).strip(" -|:")


def lookup_canonical_movie_name(title: str, radarr, threshold: float = 0.50) -> str | None:
    """Query Radarr/TMDB and return 'Title (Year)' for the best match, or None."""
    clean = clean_title(title)
    try:
        results = radarr.lookup_movie(clean)
    except Exception:
        return None
    if not results:
        return None
    best_score, best = 0.0, None
    for r in results:
        score = _similarity(clean, r.get("title", ""))
        if score > best_score:
            best_score, best = score, r
    if best_score >= threshold and best and best.get("year"):
        return f"{best['title']} ({best['year']})"
    return None


def lookup_canonical_series_name(title: str, sonarr, threshold: float = 0.50) -> str | None:
    """Query Sonarr/TVDB and return 'Title (Year)' for the best match, or None."""
    clean = clean_title(title)
    try:
        results = sonarr.lookup_series(clean)
    except Exception:
        return None
    if not results:
        return None
    best_score, best = 0.0, None
    for r in results:
        score = _similarity(clean, r.get("title", ""))
        if score > best_score:
            best_score, best = score, r
    if best_score >= threshold and best and best.get("year"):
        return f"{best['title']} ({best['year']})"
    return None


def _normalize(name: str) -> str:
    name = re.sub(r"\(?\d{4}\)?", "", name)
    name = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    return re.sub(r"\s+", " ", name).strip()


def _words(name: str) -> set:
    return set(re.findall(r"[a-z0-9]+", name.lower())) - _STOPWORDS


def _similarity(a: str, b: str) -> float:
    char_score = SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()
    wa = _words(a)
    if not wa:
        return char_score
    return char_score * 0.4 + (len(wa & _words(b)) / len(wa)) * 0.6


def find_media_match(title: str, threshold: float = 0.50):
    best_score, best_path, best_kind = 0.0, None, None
    clean = clean_title(title)
    for kind, root in [("movie", MOVIE_ROOT), ("tv", TV_ROOT)]:
        if not root.exists():
            continue
        for entry in root.iterdir():
            score = _similarity(clean, entry.name)
            if score > best_score:
                best_score, best_path, best_kind = score, entry, kind
    return (best_kind, best_path) if best_score >= threshold else (None, None)


def find_media_matches(title: str, threshold: float = 0.50, max_results: int = 5):
    """Return multiple matches above threshold, sorted by score."""
    clean = clean_title(title)
    matches = []
    for kind, root in [("movie", MOVIE_ROOT), ("tv", TV_ROOT)]:
        if not root.exists():
            continue
        for entry in root.iterdir():
            score = _similarity(clean, entry.name)
            if score >= threshold:
                matches.append((score, kind, entry))
    matches.sort(key=lambda x: x[0], reverse=True)
    return [(kind, path) for score, kind, path in matches[:max_results]]


def search_youtube(query: str, max_results: int = 10) -> list:
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
    return info.get("entries", [])


def _move_to_dest(src: Path, dest_dir: Path, filename: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    # Same filesystem now, move is instant
    shutil.move(str(src), str(dest))
    return dest


def download(url: str, audio_only: bool, output_dir: Path, folder_name: str = "", quiet: bool = False) -> Path:
    import tempfile
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(dir=STAGING_DIR))
    try:
        template = str(tmp_dir / "%(title).80s.%(ext)s")

        if audio_only:
            opts = {
                "format": "bestaudio/best",
                "outtmpl": template,
                "quiet": quiet,
                "restrictfilenames": True,
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
            }
        else:
            opts = {
                "format": "bv*+ba/b",  # More flexible: best video + best audio, fallback to best single
                "outtmpl": template,
                "merge_output_format": "mkv",
                "quiet": quiet,
                "restrictfilenames": True,
            }

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)

        VALID_EXTENSIONS = {'.mkv', '.mp4', '.webm', '.mp3', '.m4a', '.avi'}
        downloaded = sorted(
            [f for f in tmp_dir.iterdir() if f.suffix.lower() in VALID_EXTENSIONS],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not downloaded:
            raise RuntimeError("No completed media file found in staging (only .part files?)")

        src = downloaded[0]
        dest_name = f"{folder_name or output_dir.name}.{src.suffix.lstrip('.')}"
        return _move_to_dest(src, output_dir, dest_name)
    finally:
        # Clean up temp dir (files already moved or download failed)
        shutil.rmtree(tmp_dir, ignore_errors=True)


def get_video_title(url: str) -> str:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info.get("title", "")


_EP_NUMBER_RE = re.compile(r'\bep(?:isode)?\.?\s*(\d+)\b', re.IGNORECASE)


def _ep_number_score(title: str, ep: int) -> float:
    """Return 0.4 bonus if the title contains 'Ep N' or 'Episode N' matching ep."""
    for m in _EP_NUMBER_RE.finditer(title):
        if int(m.group(1)) == ep:
            return 0.4
    return 0.0


def search_best_episode(show_name: str, season: int, ep: int, min_score: float = 0.30):
    """Search YouTube for a specific episode.

    Returns (result_dict, score) on match, (None, 0.0) for no match,
    (None, -1.0) on search error (caller should not count this as a miss).
    """
    queries = [
        f"{show_name} Ep {ep} Full Episode",
        f"{show_name} Episode {ep}",
        f"{show_name} season {season} episode {ep}",
    ]
    clean_show = clean_title(show_name)
    best_score, best_result = 0.0, None
    any_success = False

    for query in queries:
        try:
            results = search_youtube(query, max_results=5)
            any_success = True
        except Exception:
            continue
        for r in results:
            raw_title = r.get("title", "")
            bonus = _ep_number_score(raw_title, ep)
            # Episode number must appear in the title — no number, no match
            if bonus == 0:
                continue
            base = _similarity(clean_show, clean_title(raw_title))
            score = min(1.0, base + bonus)
            if score > best_score:
                best_score, best_result = score, r
        if best_score >= 0.60:
            break

    if not any_success:
        return None, -1.0  # all queries failed (network error) — not a real miss
    return (best_result, best_score) if best_score >= min_score else (None, 0.0)
