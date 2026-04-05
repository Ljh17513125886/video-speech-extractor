#!/usr/bin/env python3
"""
Extract subtitles from video URLs via the yt-dlp CLI and write a Markdown transcript.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from subtitle_to_text import SUPPORTED_EXTENSIONS, convert_subtitle_to_text

LANGUAGE_PRIORITY = ["zh-Hans", "zh-Hant", "zh", "en", "zh-CN", "zh-TW"]
AUTH_ERROR_PATTERNS = (
    "sign in to confirm you’re not a bot",
    "sign in to confirm you're not a bot",
    "use --cookies-from-browser or --cookies for the authentication",
    "video unavailable. this content isn't available",
)


@dataclass
class VideoInfo:
    title: str
    url: str
    duration: Optional[int]
    manual_subtitles: list[str]
    automatic_subtitles: list[str]


class YtDlpError(RuntimeError):
    """Wrap yt-dlp failures with stdout/stderr for user-friendly handling."""

    def __init__(self, message: str, stderr: str = "", stdout: str = "") -> None:
        super().__init__(message)
        self.stderr = stderr
        self.stdout = stdout


def check_yt_dlp_installed() -> bool:
    """Return True if yt-dlp is available on PATH."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def run_command(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Execute a subprocess and always capture text output."""
    return subprocess.run(args, capture_output=True, text=True, check=False)


def build_cookie_args(
    cookies_from_browser: Optional[str],
    cookies_file: Optional[str],
) -> list[str]:
    """Build yt-dlp cookie arguments."""
    cookie_args: list[str] = []
    if cookies_from_browser:
        cookie_args.extend(["--cookies-from-browser", cookies_from_browser])
    if cookies_file:
        cookie_args.extend(["--cookies", cookies_file])
    return cookie_args


def extract_video_info(
    url: str,
    cookies_from_browser: Optional[str] = None,
    cookies_file: Optional[str] = None,
) -> VideoInfo:
    """Fetch video metadata, including available subtitles."""
    cmd = [
        "yt-dlp",
        *build_cookie_args(cookies_from_browser, cookies_file),
        "--dump-single-json",
        "--no-warnings",
        "--skip-download",
        url,
    ]
    result = run_command(cmd)
    if result.returncode != 0:
        raise YtDlpError("Failed to fetch video info.", stderr=result.stderr, stdout=result.stdout)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise YtDlpError(f"Failed to parse yt-dlp JSON output: {exc}") from exc

    return VideoInfo(
        title=payload.get("title") or "video",
        url=payload.get("webpage_url") or url,
        duration=payload.get("duration"),
        manual_subtitles=sorted((payload.get("subtitles") or {}).keys()),
        automatic_subtitles=sorted((payload.get("automatic_captions") or {}).keys()),
    )


def select_best_language(
    manual_subtitles: list[str],
    automatic_subtitles: list[str],
    preferred: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Select the best available subtitle language, preferring manual captions."""

    def pick(available: list[str], requested: Optional[str]) -> Optional[str]:
        if requested:
            if requested in available:
                return requested
            for candidate in available:
                if candidate.startswith(requested) or requested in candidate:
                    return candidate

        for priority in LANGUAGE_PRIORITY:
            if priority in available:
                return priority
            for candidate in available:
                if candidate.startswith(priority) or priority in candidate:
                    return candidate

        return available[0] if available else None

    selected = pick(manual_subtitles, preferred)
    if selected:
        return selected, "manual"

    selected = pick(automatic_subtitles, preferred)
    if selected:
        return selected, "automatic"

    return None, None


def slugify_filename(title: str) -> str:
    """Create a stable filesystem-friendly base filename."""
    cleaned = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "", title).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned or "video_transcript"


def format_duration(seconds: Optional[int]) -> str:
    """Format a duration in seconds as HH:MM:SS."""
    if seconds is None:
        return "Unknown"

    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def is_auth_error(message: str) -> bool:
    """Return True when yt-dlp likely hit a YouTube authentication wall."""
    lowered = message.lower()
    return any(pattern in lowered for pattern in AUTH_ERROR_PATTERNS)


def build_auth_guidance(
    url: str,
    list_mode: bool,
    preferred_language: Optional[str],
) -> str:
    """Build the next-step guidance for auth failures."""
    command = ["python3", "scripts/extract_subtitles.py", "--cookies-from-browser", "chrome"]
    if list_mode:
        command.append("--list")
    if preferred_language:
        command.extend(["--language", preferred_language])
    command.append(url)

    cookie_file_command = ["python3", "scripts/extract_subtitles.py", "--cookies", "/path/to/cookies.txt"]
    if list_mode:
        cookie_file_command.append("--list")
    if preferred_language:
        cookie_file_command.extend(["--language", preferred_language])
    cookie_file_command.append(url)

    return (
        "YouTube blocked anonymous access for this video.\n"
        "Retry with a logged-in browser session, for example:\n"
        f"  {' '.join(command)}\n"
        "Or use an exported cookies file:\n"
        f"  {' '.join(cookie_file_command)}"
    )


def find_downloaded_subtitle(
    output_dir: Path,
    base_name: str,
    selected_language: str,
) -> Optional[Path]:
    """Locate the downloaded subtitle file for the selected language."""
    candidates: list[Path] = []

    for extension in SUPPORTED_EXTENSIONS:
        candidates.extend(output_dir.glob(f"{base_name}*{selected_language}*{extension}"))
        candidates.extend(output_dir.glob(f"{base_name}*{extension}"))

    if not candidates:
        return None

    unique_candidates = {path.resolve(): path for path in candidates}
    return max(unique_candidates.values(), key=lambda path: path.stat().st_mtime)


def download_subtitles(
    url: str,
    output_dir: Path,
    base_name: str,
    selected_language: str,
    cookies_from_browser: Optional[str] = None,
    cookies_file: Optional[str] = None,
) -> Path:
    """Download subtitles for the selected language and return the saved file path."""
    cmd = [
        "yt-dlp",
        *build_cookie_args(cookies_from_browser, cookies_file),
        "--write-subs",
        "--write-auto-subs",
        "--skip-download",
        "--sub-langs",
        selected_language,
        "--output",
        str(output_dir / base_name),
        url,
    ]
    result = run_command(cmd)
    if result.returncode != 0:
        raise YtDlpError("Failed to download subtitles.", stderr=result.stderr, stdout=result.stdout)

    subtitle_file = find_downloaded_subtitle(output_dir, base_name, selected_language)
    if not subtitle_file:
        raise YtDlpError("yt-dlp completed without producing a subtitle file.")
    return subtitle_file


def build_transcript_markdown(
    title: str,
    url: str,
    duration: Optional[int],
    transcript_text: str,
    subtitle_language: str,
    subtitle_source: str,
) -> str:
    """Render the transcript Markdown document."""
    extracted_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    return (
        f"# {title}\n\n"
        f"> Source: {url}\n"
        f"> Duration: {format_duration(duration)}\n"
        f"> Subtitle language: {subtitle_language}\n"
        f"> Subtitle source: {subtitle_source}\n"
        f"> Extracted at: {extracted_at}\n\n"
        "## Transcript\n\n"
        f"{transcript_text}\n"
    )


def write_transcript_markdown(
    output_dir: Path,
    base_name: str,
    markdown: str,
) -> Path:
    """Write transcript Markdown to the output directory."""
    markdown_path = output_dir / f"{base_name}_transcript.md"
    markdown_path.write_text(markdown, encoding="utf-8")
    return markdown_path


def print_available_subtitles(video_info: VideoInfo) -> None:
    """Print subtitle language availability for the video."""
    print(f"Title: {video_info.title}")
    print(f"URL: {video_info.url}")
    print(f"Duration: {format_duration(video_info.duration)}")
    print(f"Manual subtitles: {', '.join(video_info.manual_subtitles) or 'None'}")
    print(f"Automatic subtitles: {', '.join(video_info.automatic_subtitles) or 'None'}")


def handle_yt_dlp_error(
    error: YtDlpError,
    url: str,
    list_mode: bool,
    preferred_language: Optional[str],
) -> int:
    """Print a user-friendly yt-dlp error and return the exit code."""
    detail = error.stderr.strip() or error.stdout.strip() or str(error)

    if is_auth_error(detail):
        print(build_auth_guidance(url, list_mode, preferred_language), file=sys.stderr)
        return 1

    print(detail, file=sys.stderr)
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract subtitles from video URLs and generate a Markdown transcript.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --list https://www.youtube.com/watch?v=VIDEO_ID\n"
            "  %(prog)s --cookies-from-browser chrome https://www.youtube.com/watch?v=VIDEO_ID\n"
            "  %(prog)s --language zh-Hans --cookies cookies.txt https://www.youtube.com/watch?v=VIDEO_ID"
        ),
    )
    parser.add_argument("url", help="Video URL to extract subtitles from")
    parser.add_argument("--language", "-l", help="Preferred subtitle language")
    parser.add_argument("--list", action="store_true", help="List available subtitles and exit")
    parser.add_argument(
        "--cookies-from-browser",
        help="Load cookies directly from a local browser profile, for example: chrome",
    )
    parser.add_argument("--cookies", help="Path to an exported cookies.txt file")
    parser.add_argument(
        "--output",
        "-o",
        default="output",
        help="Directory to save subtitle files and transcript Markdown (default: ./output)",
    )

    args = parser.parse_args()

    if not check_yt_dlp_installed():
        print("yt-dlp not found on PATH. Install it first, for example: brew install yt-dlp", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        video_info = extract_video_info(
            args.url,
            cookies_from_browser=args.cookies_from_browser,
            cookies_file=args.cookies,
        )
    except YtDlpError as exc:
        sys.exit(handle_yt_dlp_error(exc, args.url, args.list, args.language))

    if args.list:
        print_available_subtitles(video_info)
        sys.exit(0)

    selected_language, subtitle_source = select_best_language(
        video_info.manual_subtitles,
        video_info.automatic_subtitles,
        args.language,
    )
    if not selected_language or not subtitle_source:
        print("No subtitles available for this video.", file=sys.stderr)
        sys.exit(1)

    base_name = slugify_filename(video_info.title)

    try:
        subtitle_file = download_subtitles(
            args.url,
            output_dir=output_dir,
            base_name=base_name,
            selected_language=selected_language,
            cookies_from_browser=args.cookies_from_browser,
            cookies_file=args.cookies,
        )
    except YtDlpError as exc:
        sys.exit(handle_yt_dlp_error(exc, args.url, False, args.language))

    transcript_text = convert_subtitle_to_text(str(subtitle_file))
    markdown = build_transcript_markdown(
        title=video_info.title,
        url=video_info.url,
        duration=video_info.duration,
        transcript_text=transcript_text,
        subtitle_language=selected_language,
        subtitle_source=subtitle_source,
    )
    markdown_path = write_transcript_markdown(output_dir, base_name, markdown)

    if args.language and args.language != selected_language:
        print(f"Requested subtitle language '{args.language}' was unavailable; used '{selected_language}' instead.")

    print(f"Subtitle file: {subtitle_file}")
    print(f"Transcript Markdown: {markdown_path}")


if __name__ == "__main__":
    main()
