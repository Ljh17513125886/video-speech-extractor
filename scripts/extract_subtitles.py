#!/usr/bin/env python3
"""
Extract subtitles from video URLs using yt-dlp Python API.
This script can be used as an alternative to the command-line approach.
"""

import sys
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Any
import re

# Language priority for subtitle selection
LANGUAGE_PRIORITY = ['zh-Hans', 'zh-Hant', 'zh', 'en', 'zh-CN', 'zh-TW']


def check_yt_dlp_installed() -> bool:
    """Check if yt-dlp is available (either as module or command)."""
    try:
        import yt_dlp
        return True
    except ImportError:
        pass

    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_yt_dlp() -> bool:
    """Try to install yt-dlp via pip."""
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'],
                      check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def get_video_info(url: str) -> Dict[str, Any]:
    """Get video information including available subtitles."""
    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except ImportError:
        # Fallback to command line
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-download', url],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        raise RuntimeError(f"Failed to get video info: {result.stderr}")


def list_available_subtitles(url: str) -> Dict[str, List[str]]:
    """List all available subtitles for a video."""
    info = get_video_info(url)

    manual_subs = list(info.get('subtitles', {}).keys())
    auto_subs = list(info.get('automatic_captions', {}).keys())

    return {
        'manual': manual_subs,
        'auto': auto_subs
    }


def select_best_language(available: List[str], preferred: Optional[str] = None) -> Optional[str]:
    """Select the best available subtitle language."""
    if preferred and preferred in available:
        return preferred

    for lang in LANGUAGE_PRIORITY:
        # Check exact match
        if lang in available:
            return lang
        # Check partial match (e.g., 'zh-Hans' matches 'zh-Hans.en')
        for avail in available:
            if avail.startswith(lang) or lang in avail:
                return avail

    # Return first available if any
    return available[0] if available else None


def clean_subtitle_text(content: str) -> str:
    """Convert subtitle content to clean text (handles VTT, SRT, ASS)."""
    lines = content.split('\n')
    text_lines = []

    for line in lines:
        line = line.strip()

        # Skip WEBVTT header
        if line.startswith('WEBVTT'):
            continue
        # Skip NOTE blocks
        if line.startswith('NOTE'):
            continue
        # Skip timestamp lines (VTT and SRT formats)
        if '-->' in line:
            continue
        # Skip lines that are just numbers (sequence numbers in SRT)
        if line.isdigit():
            continue
        # Skip empty lines
        if not line:
            continue
        # Skip cue settings (position, align, etc.)
        if re.match(r'^(position|align|line|region):', line):
            continue
        # Skip ASS/SSA format headers
        if line.startswith('[') or line.startswith('Format:') or line.startswith('Dialogue:'):
            continue
        # Remove HTML tags
        line = re.sub(r'<[^>]+>', '', line)
        # Remove voice tags
        line = re.sub(r'<v\s+[^>]+>', '', line)
        # Clean up whitespace
        line = line.strip()
        if line:
            text_lines.append(line)

    return '\n'.join(text_lines)


def download_subtitles(url: str, language: Optional[str] = None,
                       output_dir: Optional[str] = None) -> Optional[str]:
    """Download subtitles from video URL."""
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(tempfile.mkdtemp())

    # Get available subtitles
    available = list_available_subtitles(url)
    all_subs = available['manual'] + available['auto']

    if not all_subs:
        return None

    # Select best language
    selected_lang = select_best_language(all_subs, language)
    if not selected_lang:
        return None

    # Download using yt-dlp
    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [selected_lang],
            'skip_download': True,
            'outtmpl': str(output_path / '%(title)s'),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the downloaded subtitle file
        for ext in ['.vtt', '.srt', '.ass']:
            files = list(output_path.glob(f'*{selected_lang}*{ext}'))
            if files:
                return str(files[0])
            files = list(output_path.glob(f'*{ext}'))
            if files:
                return str(files[0])

        return None
    except ImportError:
        # Fallback to command line
        cmd = [
            'yt-dlp',
            '--write-subs',
            '--write-auto-subs',
            '--sub-langs', selected_lang,
            '--skip-download',
            '-o', str(output_path / '%(title)s'),
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to download subtitles: {result.stderr}")

        # Find the downloaded subtitle file
        for ext in ['.vtt', '.srt', '.ass']:
            files = list(output_path.glob(f'*{selected_lang}*{ext}'))
            if files:
                return str(files[0])
            files = list(output_path.glob(f'*{ext}'))
            if files:
                return str(files[0])

        return None


def main():
    parser = argparse.ArgumentParser(
        description='Extract subtitles from video URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://www.youtube.com/watch?v=VIDEO_ID"
  %(prog)s --language zh-Hans "https://www.youtube.com/watch?v=VIDEO_ID"
  %(prog)s --list "https://www.youtube.com/watch?v=VIDEO_ID"
        """
    )
    parser.add_argument('url', help='Video URL to extract subtitles from')
    parser.add_argument('--language', '-l', help='Preferred subtitle language')
    parser.add_argument('--list', action='store_true', help='List available subtitles')
    parser.add_argument('--output', '-o', help='Output file path')

    args = parser.parse_args()

    # Check yt-dlp availability
    if not check_yt_dlp_installed():
        print("yt-dlp not found. Installing...")
        if not install_yt_dlp():
            print("Failed to install yt-dlp. Please install manually: pip install yt-dlp",
                  file=sys.stderr)
            sys.exit(1)

    try:
        if args.list:
            available = list_available_subtitles(args.url)
            print("Available subtitles:")
            print(f"  Manual: {', '.join(available['manual']) or 'None'}")
            print(f"  Auto:   {', '.join(available['auto']) or 'None'}")
        else:
            subtitle_file = download_subtitles(args.url, args.language, args.output)
            if subtitle_file:
                print(f"Subtitles saved to: {subtitle_file}")
                # Read and print content
                content = Path(subtitle_file).read_text(encoding='utf-8')
                clean_text = clean_subtitle_text(content)
                print("\n--- Transcript ---")
                print(clean_text)
            else:
                print("No subtitles available for this video.", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
