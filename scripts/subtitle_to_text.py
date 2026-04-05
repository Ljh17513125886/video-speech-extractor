#!/usr/bin/env python3
"""
Convert subtitle files (VTT, SRT, ASS/SSA) to clean text.
"""

import argparse
import re
import sys
from pathlib import Path

SUPPORTED_EXTENSIONS = (".vtt", ".srt", ".ass", ".ssa")

TIMESTAMP_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}[.,]\d{3}")
CUE_SETTING_PATTERN = re.compile(r"^(position|align|line|region|size|vertical):", re.IGNORECASE)
VTT_METADATA_PATTERN = re.compile(r"^(kind|language):", re.IGNORECASE)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
VOICE_TAG_PATTERN = re.compile(r"</?v(?:\s+[^>]+)?>", re.IGNORECASE)
ASS_FORMATTING_PATTERN = re.compile(r"\{[^}]+\}")


def strip_common_markup(line: str) -> str:
    """Remove common subtitle markup without changing spoken text."""
    line = HTML_TAG_PATTERN.sub("", line)
    line = VOICE_TAG_PATTERN.sub("", line)
    return line.strip()


def clean_vtt(content: str) -> str:
    """Convert VTT subtitle format to clean text."""
    text_lines = []
    in_note_block = False

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if line.startswith("WEBVTT"):
            continue
        if VTT_METADATA_PATTERN.match(line):
            continue
        if line.startswith("NOTE"):
            in_note_block = True
            continue
        if in_note_block:
            if not line:
                in_note_block = False
            continue
        if "-->" in line or TIMESTAMP_PATTERN.match(line):
            continue
        if line.isdigit():
            continue
        if not line:
            continue
        if CUE_SETTING_PATTERN.match(line):
            continue

        line = strip_common_markup(line)
        if line:
            text_lines.append(line)

    return "\n".join(text_lines)


def clean_srt(content: str) -> str:
    """Convert SRT subtitle format to clean text."""
    text_lines = []

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if "-->" in line or TIMESTAMP_PATTERN.match(line):
            continue
        if line.isdigit():
            continue
        if not line:
            continue

        line = strip_common_markup(line)
        if line:
            text_lines.append(line)

    return "\n".join(text_lines)


def clean_ass(content: str) -> str:
    """Convert ASS/SSA subtitle format to clean text."""
    text_lines = []
    in_events = False

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if line.startswith("[Events]"):
            in_events = True
            continue

        if not in_events:
            continue

        if not line or line.startswith("Format:"):
            continue

        if line.startswith("Dialogue:"):
            payload = line[len("Dialogue:"):].lstrip()
            parts = payload.split(",", 9)
            if len(parts) < 10:
                continue
            text = parts[9]
            text = ASS_FORMATTING_PATTERN.sub("", text)
            text = text.replace(r"\N", "\n").replace(r"\n", "\n")
            text = text.replace(r"\h", " ")
            text = re.sub(r"\\[A-Za-z]+", "", text)
            for text_line in text.splitlines():
                cleaned = text_line.strip()
                if cleaned:
                    text_lines.append(cleaned)

    return "\n".join(text_lines)


def detect_format(content: str, filename: str) -> str:
    """Detect subtitle format from content or filename."""
    filename_lower = filename.lower()

    if filename_lower.endswith(".vtt"):
        return "vtt"
    if filename_lower.endswith(".srt"):
        return "srt"
    if filename_lower.endswith(".ass") or filename_lower.endswith(".ssa"):
        return "ass"

    if content.startswith("WEBVTT"):
        return "vtt"
    if "[Script Info]" in content or "[Events]" in content:
        return "ass"
    return "srt"


def clean_subtitle_content(content: str, filename: str = "") -> str:
    """Convert raw subtitle content to clean text."""
    format_type = detect_format(content, filename)

    if format_type == "vtt":
        return clean_vtt(content)
    if format_type == "ass":
        return clean_ass(content)
    return clean_srt(content)


def convert_subtitle_to_text(input_file: str) -> str:
    """Convert a subtitle file to clean text."""
    path = Path(input_file)

    if not path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {input_file}")

    content = path.read_text(encoding="utf-8")
    return clean_subtitle_content(content, path.name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert subtitle files to clean text")
    parser.add_argument("--input", "-i", required=True, help="Input subtitle file")
    parser.add_argument("--output", "-o", help="Output text file (default: stdout)")

    args = parser.parse_args()

    try:
        text = convert_subtitle_to_text(args.input)

        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
            print(f"Text saved to: {args.output}")
        else:
            print(text)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
