# 🎬 Day 17 — Task 1: YouTube Emotion Analysis Tool

## 📋 Overview

A Python tool that downloads YouTube videos and analyzes emotions using [Hume.ai](https://hume.ai)'s multimodal emotion AI. The tool detects emotions from **facial expressions**, **vocal prosody**, **non-verbal bursts**, and **spoken language**.

---

## 🧠 How It Works

```
YouTube URL → yt-dlp Download → Hume.ai Batch API → Emotion Report
```

| Step | Description |
|------|-------------|
| **1. Download** | Uses `yt-dlp` to download the YouTube video locally as MP4 |
| **2. Upload & Analyze** | Sends the video to Hume.ai's Batch API for emotion analysis |
| **3. Report** | Parses predictions and generates a detailed emotion breakdown |

### Emotion Models

| Model | What It Detects |
|-------|----------------|
| **Face** | Facial expressions and muscle movements (FACS-based) |
| **Prosody** | Tone, pitch, and rhythm of the speaker's voice |
| **Burst** | Non-verbal sounds — laughs, sighs, gasps, grunts |
| **Language** | Sentiment and meaning of spoken words |

---

## 🚀 Setup

### 1. Prerequisites

- Python 3.8+
- [Hume.ai account](https://beta.hume.ai) with API key
- `ffmpeg` installed (for `yt-dlp` media merging)

### 2. Install Dependencies

```bash
# From the eytraining root directory
pip install -r requirements.txt

# Or install only task-specific packages
pip install yt-dlp hume python-dotenv
```

### 3. Configure API Key

**Option A: `.env` file** (Recommended)

Edit the `.env` file in this directory:
```env
HUME_API_KEY=your-actual-api-key-here
```

**Option B: Environment Variable**

```bash
# PowerShell (Windows)
$env:HUME_API_KEY = "your-api-key-here"

# Bash (Linux/macOS)
export HUME_API_KEY="your-api-key-here"
```

**Option C: Command-line Argument**

```bash
python main.py "VIDEO_URL" --api-key "your-api-key"
```

---

## 💻 Usage

### Basic Usage

```bash
python main.py "https://www.youtube.com/shorts/kpQsboueyFI"
```

### With Custom Options

```bash
# Specify models and save JSON report
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" \
    --models "face,prosody,burst,language" \
    --save-json \
    --output-dir "./results"
```

### Check Previous Job

```bash
python main.py "https://www.youtube.com/shorts/kpQsboueyFI" \
    --job-id "job_12345abcde"
```

### Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `url` | *(required)* | YouTube video URL to analyze |
| `--api-key` | `HUME_API_KEY` env | Hume.ai API key |
| `--output-dir` | `./results` | Directory for downloads and reports |
| `--models` | `face,prosody,burst,language` | Comma-separated model list |
| `--save-json` | `false` | Save detailed results as JSON |
| `--job-id` | `None` | Check an existing Hume.ai job |

---

## 📊 Sample Output

```
======================================================================
📊 YOUTUBE EMOTION ANALYSIS REPORT
======================================================================
  Video:     sample_video.mp4
  Job ID:    sim_20260619_093000
  Status:    completed
  Timestamp: 2026-06-19T09:30:00
  Models:    face, prosody, burst, language
----------------------------------------------------------------------

  🎯 Model: FACE
  ----------------------------------------
  Top Emotions:
    Joy                       ██████████████████████░░░░░░░░░  75.2%
    Amusement                 ████████████████████░░░░░░░░░░░  68.5%
    Interest                  ████████████████░░░░░░░░░░░░░░░  55.7%

  🎯 Model: BURST
  ----------------------------------------
  Top Emotions:
    Laugh                     ████████████████████████░░░░░░░  82.1%
    Sigh (of relief)          ████░░░░░░░░░░░░░░░░░░░░░░░░░░  15.3%

======================================================================
```

---

## 🗂 Project Structure

```
day17/task1/
├── main.py          # Main analyzer script (YouTubeEmotionAnalyzer class)
├── .env             # API key configuration (not committed to git)
├── README.md        # This documentation
└── results/         # Generated output directory
    ├── downloads/   # Downloaded YouTube videos
    └── *.json       # Emotion analysis reports
```

---

## 🔧 Python API Usage

You can also import and use the analyzer as a library:

```python
import asyncio
from main import YouTubeEmotionAnalyzer

# Initialize
analyzer = YouTubeEmotionAnalyzer(
    api_key="your-api-key",
    output_dir="./results"
)

# Run full pipeline
results = analyzer.run(
    url="https://www.youtube.com/shorts/kpQsboueyFI",
    models=["face", "prosody", "burst", "language"],
    save_json=True,
)

# Access specific results
for model, data in results["predictions"].items():
    print(f"\n{model}: {data['top_emotions']}")
```

---

## ⚠️ Notes

- **Rate Limits**: Hume.ai has API rate limits. For batch processing, implement delays between requests.
- **Video Size**: Large videos take longer to upload and analyze. Consider trimming first.
- **Simulation Mode**: If the `hume` SDK is not installed, the tool runs in simulation mode with sample data for testing.
- **Privacy**: Downloaded videos and analysis results are stored locally. Clean up `results/` as needed.

---

## 📚 Resources

- [Hume.ai Documentation](https://dev.hume.ai/docs)
- [Hume.ai Python SDK](https://github.com/HumeAI/hume-python-sdk)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
