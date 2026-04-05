---
name: video-speech-extractor
description: |
  Extract subtitles or speech transcripts from video URLs and produce Markdown transcript documents. Use when a user asks to turn a video into text, fetch subtitles, summarize spoken content from a URL, or generate a Chinese bilingual transcript from YouTube, Bilibili, Vimeo, TikTok, X/Twitter, and similar platforms. Prefer direct subtitle download with yt-dlp; if the extracted transcript is not Chinese, automatically translate it to Chinese in interleaved original-plus-Chinese paragraphs. If YouTube blocks anonymous access, retry with browser cookies such as `--cookies-from-browser chrome`.
---

# Video Speech Extractor

Extract transcript text from a video URL and save Markdown output.

## Use the scripted workflow

1. Inspect available subtitles first.

```bash
python3 scripts/extract_subtitles.py --list "<video_url>"
```

2. If YouTube blocks anonymous access, retry with a logged-in browser session.

```bash
python3 scripts/extract_subtitles.py --cookies-from-browser chrome --list "<video_url>"
```

3. Download the best subtitle track and generate Markdown.

```bash
python3 scripts/extract_subtitles.py "<video_url>"
```

4. Pin a preferred subtitle language when the user asks for one.

```bash
python3 scripts/extract_subtitles.py --language en "<video_url>"
python3 scripts/extract_subtitles.py --language zh-Hans --cookies-from-browser chrome "<video_url>"
```

## Follow the extraction order

1. Detect the platform and try direct subtitles first.
2. Prefer manual subtitles over automatic subtitles.
3. Prefer the requested language when available.
4. Otherwise fall back to the best available language using the built-in priority.
5. Convert the subtitle file to clean text.
6. Save the original-language transcript as Markdown.

## Handle YouTube auth failures explicitly

Treat `Sign in to confirm you’re not a bot` as a standard failure mode.

- Retry with `--cookies-from-browser chrome` first.
- Retry with `--cookies <cookies.txt>` when browser cookies are unavailable.
- Do not pretend extraction succeeded when yt-dlp cannot access the video.

## Translate non-Chinese transcripts to Chinese by default

If the extracted transcript language is not Chinese:

1. Keep the original transcript file intact.
2. Translate the transcript to Chinese with the active Codex model in the current session.
3. Save a bilingual Markdown file named `{title}_transcript_bilingual.md`.
4. Format the bilingual file as interleaved paragraphs: one original paragraph, then one Chinese paragraph.

Do not call an external translation API unless the user explicitly asks for one. The default translation path is the current model that is already executing the skill.

If the extracted transcript is already Chinese, do not generate a Chinese translation copy unless the user asks for another target language or another format.

## Output contract

- Original transcript: `{title}_transcript.md`
- Bilingual transcript: `{title}_transcript_bilingual.md`
- Raw subtitle file: keep the downloaded `.vtt`, `.srt`, `.ass`, or `.ssa` file next to the Markdown output

Use this Markdown shape for the original transcript:

```markdown
# [Video Title]

> Source: [video URL]
> Duration: [HH:MM:SS]
> Subtitle language: [language code]
> Subtitle source: [manual|automatic]
> Extracted at: [timestamp]

## Transcript

[clean transcript text]
```

Use this Markdown shape for a non-Chinese bilingual transcript:

```markdown
# [Video Title]

> Source: [video URL]
> Duration: [HH:MM:SS]
> Subtitle language: [language code]
> Subtitle source: [manual|automatic]
> Extracted at: [timestamp]

## Bilingual Transcript

[original paragraph 1]

[中文翻译段落 1]

[original paragraph 2]

[中文翻译段落 2]
```

## Use the text-cleaning helper when needed

If a subtitle file already exists, convert it directly:

```bash
python3 scripts/subtitle_to_text.py --input "<subtitle_file>"
```

Use the helper for `.vtt`, `.srt`, `.ass`, and `.ssa`.
