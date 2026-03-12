# Video Speech Extractor

从视频链接提取语音文字/字幕，生成 Markdown 格式的讲稿文档。

## 功能特点

- 支持 1800+ 视频平台（YouTube、Bilibili、Twitter/X、TikTok、Vimeo 等）
- 自动选择最佳字幕（手动字幕 > 自动字幕）
- 支持多语言（中英日韩等主流语言）
- 可选的语音识别转录（无字幕时）
- 输出格式化的 Markdown 文档

## 安装

### 依赖

```bash
# 使用 Homebrew 安装（推荐）
brew install yt-dlp

# 或使用 pip
pip install yt-dlp
```

### 可选依赖

```bash
# 音频提取（无字幕时需要）
brew install ffmpeg

# 语音识别（无字幕时需要）
pip install openai-whisper
```

## 使用方法

### 作为 Claude Code Skill 使用

将此仓库克隆到 Claude Code skills 目录：

```bash
git clone https://github.com/yourusername/video-speech-extractor.git \
  ~/.claude/skills/video-speech-extractor
```

然后在 Claude Code 中使用触发短语：

- "提取视频字幕"
- "视频转文字"
- "get transcript from video"

### 命令行使用

```bash
# 查看可用字幕
python scripts/extract_subtitles.py --list "https://www.youtube.com/watch?v=VIDEO_ID"

# 下载字幕
python scripts/extract_subtitles.py "https://www.youtube.com/watch?v=VIDEO_ID"

# 指定语言
python scripts/extract_subtitles.py --language zh-Hans "https://www.youtube.com/watch?v=VIDEO_ID"

# 转换字幕文件为纯文本
python scripts/subtitle_to_text.py --input subtitle.vtt --output transcript.txt
```

## 项目结构

```
video-speech-extractor/
├── SKILL.md                    # Claude Code Skill 定义
├── README.md                   # 本文档
├── scripts/
│   ├── extract_subtitles.py   # 字幕提取工具
│   └── subtitle_to_text.py    # 字幕格式转换工具
└── evals/
    └── evals.json             # 测试用例
```

## 输出格式

生成的 Markdown 文件：

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

## 错误处理

| 情况 | 处理方式 |
|------|----------|
| 视频不可访问 | 提示用户检查链接或网络 |
| 无字幕可用 | 询问是否需要音频转录 |
| 字幕语言不匹配 | 下载最接近的语言 |

## 许可证

MIT License
