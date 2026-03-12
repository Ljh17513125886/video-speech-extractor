#!/usr/bin/env python3
"""
Convert subtitle files (SRT, VTT) to clean text.
Removes timestamps, sequence numbers, and formatting.
"""

import re
import sys
import argparse
from pathlib import Path


def clean_vtt(content: str) -> str:
    """Convert VTT subtitle format to clean text."""
    lines = content.split('\n')
    text_lines = []

    for line in lines:
        # Skip WEBVTT header
        if line.startswith('WEBVTT'):
            continue
        # Skip NOTE blocks
        if line.startswith('NOTE'):
            continue
        # Skip timestamp lines (00:00:00.000 --> 00:00:00.000)
        if '-->' in line:
            continue
        # Skip lines that are just numbers (sequence numbers)
        if line.strip().isdigit():
            continue
        # Skip empty lines
        if not line.strip():
            continue
        # Skip cue settings (position, align, etc.)
        if re.match(r'^position:\d+', line.strip()):
            continue
        # Remove HTML tags
        line = re.sub(r'<[^>]+>', '', line)
        # Remove voice tags (v name)
        line = re.sub(r'<v\s+[^>]+>', '', line)
        # Clean up whitespace
        line = line.strip()
        if line:
            text_lines.append(line)

    return '\n'.join(text_lines)


def clean_srt(content: str) -> str:
    """Convert SRT subtitle format to clean text."""
    lines = content.split('\n')
    text_lines = []

    for line in lines:
        # Skip timestamp lines (00:00:00,000 --> 00:00:00,000)
        if '-->' in line:
            continue
        # Skip lines that are just numbers (sequence numbers)
        if line.strip().isdigit():
            continue
        # Skip empty lines
        if not line.strip():
            continue
        # Remove HTML tags
        line = re.sub(r'<[^>]+>', '', line)
        # Clean up whitespace
        line = line.strip()
        if line:
            text_lines.append(line)

    return '\n'.join(text_lines)


def clean_ass(content: str) -> str:
    """Convert ASS/SSA subtitle format to clean text."""
    lines = content.split('\n')
    text_lines = []
    in_events = False

    for line in lines:
        line = line.strip()

        # Skip to Events section
        if line.startswith('[Events]'):
            in_events = True
            continue

        if in_events:
            # Skip format line
            if line.startswith('Format:'):
                continue
            # Parse dialogue lines
            if line.startswith('Dialogue:'):
                # ASS format: Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
                parts = line.split(',', 9)
                if len(parts) >= 10:
                    text = parts[9]
                    # Remove ASS formatting codes
                    text = re.sub(r'\{[^}]+\}', '', text)
                    text = re.sub(r'\\[Nn]', '\n', text)
                    text = re.sub(r'\\[^Nn]', '', text)
                    text = text.strip()
                    if text:
                        text_lines.append(text)

    return '\n'.join(text_lines)


def detect_format(content: str, filename: str) -> str:
    """Detect subtitle format from content or filename."""
    filename_lower = filename.lower()

    if filename_lower.endswith('.vtt'):
        return 'vtt'
    elif filename_lower.endswith('.srt'):
        return 'srt'
    elif filename_lower.endswith('.ass') or filename_lower.endswith('.ssa'):
        return 'ass'

    # Try to detect from content
    if content.startswith('WEBVTT'):
        return 'vtt'
    elif '[Script Info]' in content or '[Events]' in content:
        return 'ass'
    else:
        # Default to SRT
        return 'srt'


def convert_subtitle_to_text(input_file: str) -> str:
    """Convert a subtitle file to clean text."""
    path = Path(input_file)

    if not path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {input_file}")

    content = path.read_text(encoding='utf-8')
    format_type = detect_format(content, path.name)

    if format_type == 'vtt':
        return clean_vtt(content)
    elif format_type == 'ass':
        return clean_ass(content)
    else:
        return clean_srt(content)


def main():
    parser = argparse.ArgumentParser(description='Convert subtitle files to clean text')
    parser.add_argument('--input', '-i', required=True, help='Input subtitle file')
    parser.add_argument('--output', '-o', help='Output text file (default: stdout)')

    args = parser.parse_args()

    try:
        text = convert_subtitle_to_text(args.input)

        if args.output:
            Path(args.output).write_text(text, encoding='utf-8')
            print(f"Text saved to: {args.output}")
        else:
            print(text)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
