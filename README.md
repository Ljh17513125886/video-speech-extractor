# Video Speech Extractor

Extract subtitles from video URLs with `yt-dlp`, clean them into transcript text, and write Markdown transcript files.

## What this repo provides

- A reusable `video-speech-extractor` skill
- A CLI-first subtitle extraction script
- A subtitle-to-text cleaner for `.vtt`, `.srt`, `.ass`, and `.ssa`
- A YouTube auth fallback that tells users to retry with browser cookies

## Dependencies

Required:

```bash
brew install yt-dlp
```

Optional for skill development and validation:

```bash
python3 -m venv /tmp/video-speech-extractor-skill-venv
/tmp/video-speech-extractor-skill-venv/bin/pip install pyyaml
```

## CLI usage

List available subtitles:

```bash
python3 scripts/extract_subtitles.py --list "https://www.youtube.com/watch?v=VIDEO_ID"
```

Retry YouTube with Chrome cookies:

```bash
python3 scripts/extract_subtitles.py --cookies-from-browser chrome --list "https://www.youtube.com/watch?v=VIDEO_ID"
python3 scripts/extract_subtitles.py --cookies-from-browser chrome "https://www.youtube.com/watch?v=VIDEO_ID"
```

Pin a preferred language:

```bash
python3 scripts/extract_subtitles.py --language en "https://www.youtube.com/watch?v=VIDEO_ID"
```

Use an exported cookies file instead of browser cookies:

```bash
python3 scripts/extract_subtitles.py --cookies /path/to/cookies.txt "https://www.youtube.com/watch?v=VIDEO_ID"
```

Change the output directory:

```bash
python3 scripts/extract_subtitles.py --output ./output "https://www.youtube.com/watch?v=VIDEO_ID"
```

Convert an existing subtitle file to plain text:

```bash
python3 scripts/subtitle_to_text.py --input subtitle.vtt --output transcript.txt
```

## Output files

The extractor writes:

- A raw subtitle file such as `.vtt`, `.srt`, `.ass`, or `.ssa`
- A Markdown transcript file named `{title}_transcript.md`

Translation is a skill-layer step, not a CLI feature. If the extracted transcript is not Chinese, the skill should automatically create `{title}_transcript_bilingual.md` using the current Codex model, with each original paragraph followed by its Chinese translation.

## YouTube behavior

For some YouTube videos, anonymous `yt-dlp` requests fail with:

`Sign in to confirm you’re not a bot`

That is expected. The supported recovery path is:

1. Retry with `--cookies-from-browser chrome`
2. If needed, retry with `--cookies /path/to/cookies.txt`

The script detects this case and prints the next suggested command instead of showing a Python traceback.
