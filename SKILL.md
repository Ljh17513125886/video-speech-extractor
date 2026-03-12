---
name: video-speech-extractor
description: |
  从视频 URL 提取语音文字/字幕，输出为 Markdown 讲稿文档。

  支持场景：
  - 用户给视频链接，想要获取文字版讲稿/字幕
  - 外语视频需要翻译成中文
  - 支持中英日韩等主流语言

  触发短语："提取视频字幕"、"视频转文字"、"get transcript from video"、"把视频转成文字"、"帮我提取这个视频的内容"、"视频讲稿"、"字幕提取"。

  支持平台：YouTube、Bilibili、Twitter/X、TikTok、Vimeo 等 1800+ 视频平台。
---

# Video Speech Extractor

从视频链接提取语音文字，生成 Markdown 格式的讲稿文档。

## 工作流程

### 1. 分析视频链接

首先确认视频平台和可用的字幕/转录选项：

```bash
# 查看可用的字幕列表
yt-dlp --list-subs "<video_url>"
```

### 2. 获取讲稿内容

**优先级策略：**

1. **优先下载现成字幕**（质量最高）
   - 手动上传的字幕 > 自动生成的字幕
   - 原语言字幕 > 翻译字幕

2. **无字幕时提取音频转录**（备选方案）
   - 使用 whisper 或类似工具

### 3. 下载字幕命令

```bash
# 下载所有可用字幕
yt-dlp --write-subs --write-auto-subs --skip-download --sub-lang all -o "%(title)s" "<video_url>"

# 下载特定语言字幕（如中文）
yt-dlp --write-subs --skip-download --sub-lang zh-Hans -o "%(title)s" "<video_url>"

# 下载英文字幕
yt-dlp --write-subs --write-auto-subs --skip-download --sub-lang en -o "%(title)s" "<video_url>"
```

### 4. 字幕格式转换

下载的字幕通常是 `.vtt` 或 `.srt` 格式，需要转换为纯文本：

```bash
# 清理时间戳，提取纯文本
sed 's/<[^>]*>//g' input.vtt | sed '/^[0-9]/d' | sed '/^$/d' > output.txt
```

### 5. 翻译处理

**如果是外语视频：**

1. 保留原语言讲稿
2. 使用 LLM 翻译成中文
3. 两个版本都输出到 Markdown

## 输出格式

生成的 Markdown 文件结构：

```markdown
# [视频标题]

> 来源：[视频链接]
> 时长：[视频时长]
> 提取时间：[日期]

## 讲稿内容

[原语言讲稿内容]

---

## 中文翻译

[中文翻译内容，仅外语视频需要]
```

## 文件命名

- 原语言版：`{视频标题}_transcript.md`
- 双语版：`{视频标题}_transcript_bilingual.md`

## 错误处理

| 情况 | 处理方式 |
|------|----------|
| 视频不可访问 | 提示用户检查链接或网络 |
| 无字幕可用 | 询问是否需要音频转录（需要额外工具） |
| 字幕语言不匹配 | 下载最接近的语言，说明情况 |

## 依赖

- `yt-dlp`：视频下载和字幕提取
- `ffmpeg`（可选）：音频提取
- `whisper`（可选）：无字幕时的语音识别

## 示例用法

用户输入：
> 帮我提取这个视频的字幕：https://www.youtube.com/watch?v=xxxxx

用户输入：
> 这个 B站视频讲的是什么？把内容转成文字给我

用户输入：
> Extract the transcript from this video: https://vimeo.com/xxxxx
