# Midnight Telugu

AI-assisted Telugu YouTube Shorts draft production system for mystery, crime, horror, strange events, and psychological twist stories.

> **v1 does not upload to YouTube. Human review is mandatory. Generated videos are drafts only.**

---

## What This Does

1. Generates original Telugu story ideas
2. Writes a natural Telugu narration script
3. Improves the script's Telugu flow (humanizer)
4. Plans 6–10 cinematic scenes
5. Composes a draft vertical video (FFmpeg)
6. Creates a review package for Kishore to inspect
7. Approves or rejects after human review
8. Tracks performance manually

**No auto-upload. No YouTube API. No paid API keys required in v1.**

---

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/kishorekrrish/midnight-telugu.git
cd midnight-telugu

# 2. Create virtual environment
python -m venv .venv

# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env
# Edit .env if you want to add real API keys later
# All providers default to mock — no keys needed for v1

# 5. Initialize project directories
python -m workers.cli init-project
```

---

## Generate Your First Draft

Run these commands in order:

```bash
# Step 1: Generate 5 story ideas
python -m workers.cli generate-ideas --count 5

# Step 2: Generate a script from the latest idea
python -m workers.cli generate-script

# Step 3: Humanize the script (improve Telugu naturalness)
python -m workers.cli humanize-script

# Step 4: Plan 7 cinematic scenes
python -m workers.cli plan-scenes

# Step 5: Compose the video (dry-run if FFmpeg/assets missing)
python -m workers.cli compose-video

# Step 6: Create the review package
python -m workers.cli create-review
```

Your review package will be at: **`content/review/<review_id>.json`**

---

## Review and Approve

Open `content/review/<review_id>.json` and check against `docs/REVIEW_CHECKLIST.md`.

```bash
# Approve a draft (does NOT upload anywhere)
python -m workers.cli approve content/review/<review_id>.json --notes "Approved"

# Reject a draft
python -m workers.cli reject content/review/<review_id>.json --notes "Script feels robotic"
```

Approved drafts go to `content/approved/`. **Upload to YouTube manually.**

---

## Record Performance (After Manual Upload)

```bash
python -m workers.cli record-performance <video_id> \
  --date 2026-01-01 \
  --views 5000 \
  --likes 300 \
  --comments 45 \
  --retention 72.5
```

---

## Requirements

- Python 3.11+
- FFmpeg (optional for v1 dry-run; required for real video rendering)
  - Linux: `sudo apt install ffmpeg`
  - Mac: `brew install ffmpeg`
  - Windows: Download from https://ffmpeg.org/

---

## API Keys (Optional in v1)

Copy `.env.example` to `.env`. All providers default to `mock`.

| Key | Provider | Status |
|-----|----------|--------|
| `ANTHROPIC_API_KEY` | Claude text generation | Optional |
| `OPENAI_API_KEY` | OpenAI text generation | Optional |
| `ELEVENLABS_API_KEY` | Telugu voice synthesis | Optional |
| `IMAGE_PROVIDER_API_KEY` | Image generation | Optional |

Without keys, the system uses template-based mock generation and all commands still work.

---

## Project Structure

```
content/ideas/      ← Generated story ideas (JSON)
content/scripts/    ← Scripts and humanized scripts (JSON)
content/scenes/     ← Scene plans (JSON)
content/review/     ← Draft review packages (JSON)
content/approved/   ← Approved drafts (JSON)
outputs/videos/     ← Draft video metadata (JSON) / real MP4s
analytics/          ← videos.csv, performance.csv
workers/            ← Python modules
docs/               ← Documentation
prompts/            ← Prompt templates
```

---

## Running Tests

```bash
pytest -v
```

## Linting

```bash
ruff check .
```

---

## Important: No YouTube Auto-Upload

v1 intentionally has **no upload capability**. After approval, upload manually via YouTube Studio. This is a deliberate product decision — see `docs/MONETIZATION_SAFETY.md`.

---

## Documentation

- [Project Architecture](docs/PROJECT.md)
- [Content Strategy](docs/CONTENT_STRATEGY.md)
- [Telugu Style Guide](docs/STYLE_GUIDE.md)
- [Voice Guide](docs/VOICE_GUIDE.md)
- [Monetization Safety](docs/MONETIZATION_SAFETY.md)
- [Automation Plan](docs/AUTOMATION_PLAN.md)
- [Review Checklist](docs/REVIEW_CHECKLIST.md)
- [Roadmap](docs/ROADMAP.md)
