# Midnight Telugu

AI-assisted Telugu YouTube Shorts draft production system for mystery, crime, horror, strange events, and psychological twist stories.

> **v1 does not upload to YouTube. Human review is mandatory. Generated videos are drafts only.**

---

## What This Does (v1.3 — Blueprint-First Story Engine)

New in v1.3:
- **Blueprint-first pipeline** — ideas now become a locked `StoryBlueprint` before script generation.
- **Narrative gate** — Script Director validates protagonist, POV, device/clue payoff, reveal clarity, twist connection, and location discipline before scene planning.
- **Blueprint artifacts** — approved blueprints are saved under `content/blueprints/`.
- **Provider abstraction** — `mock` (no API keys) and `openai` providers. Default is always `mock`.
- **Strict approval thresholds** — narrative ≥ 90, quality ≥ 88, Telugu authenticity ≥ 90, continuity ≥ 90, zero hard failures.
- **Directed Script JSON** — saved under `content/scripts/directed/`. Plan-scenes prefers approved directed scripts.
- **Enhanced Review Markdown** — includes Script Director section, Script Source, and Final Publish Recommendation.

## What This Does (v1.1)

Quality additions over v1:
- **Story Scorer** — every idea and script is scored 0-100 across 8 dimensions (hook strength, twist quality, originality, monetization safety, etc.)
- **Repeat Pattern Detector** — scans all prior content to warn when you're repeating twist types, categories, or locations
- **Diverse Idea Generation** — all 10 content buckets are covered in every batch (no category spam)
- **8 Script Structures** — cold open, object mystery, unreliable narrator, emotional reveal, etc.
- **Idea-grounded Script Builder** — generated scripts now pull directly from each idea's hook, premise, and twist instead of relying on generic template beats
- **Stronger Humanizer** — removes AI endings, splits long sentences, adds voiceover pacing
- **Markdown Review Package** — every draft generates a human-readable `.md` file with full script, scene table, YouTube metadata, and approve/reject commands

## What This Does

1. Generates original Telugu story ideas
2. Converts the idea into a locked story blueprint
3. Writes a natural Telugu narration script from that blueprint
4. Improves the script's Telugu flow (humanizer)
5. Runs Script Director + narrative gate
6. Plans 6–10 cinematic scenes
7. Composes a draft vertical video (FFmpeg)
8. Creates a review package for Kishore to inspect
9. Approves or rejects after human review
10. Tracks performance manually

### Script Director Gate

The `direct-script` command runs an automated improvement loop:
1. Validates the script against the approved blueprint and all quality thresholds
2. Builds a director prompt with found issues and the `prompts/script_director.md` system prompt
3. Calls a text provider (default: `mock`, optional: `openai`) to rewrite the script
4. Re-validates and retries up to `--max-attempts` times (default: 3)
5. Saves the best result as a `DirectedScript` JSON under `content/scripts/directed/`
6. Sets `approved_for_scene_planning` only if the blueprint passes, hard failures are zero, and all score thresholds are met

Plan-scenes automatically uses an approved DirectedScript when one exists. Use `--allow-unapproved` to bypass.
If a DirectedScript exists but is not approved, `plan-scenes` now stops by default instead of silently falling back.

```bash
# Basic usage (uses mock provider, no API keys needed)
python -m workers.cli direct-script

# With OpenAI (requires OPENAI_API_KEY in .env)
python -m workers.cli direct-script --provider openai

# Fail pipeline if thresholds not met
python -m workers.cli direct-script --strict

# Scene planning blocks on failed DirectedScript unless explicitly overridden
python -m workers.cli plan-scenes
python -m workers.cli plan-scenes --allow-unapproved
```

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

# Step 2: Build a locked story blueprint from the latest idea
python -m workers.cli build-blueprint

# Step 3: Generate a script from the latest blueprint
python -m workers.cli generate-script

# Step 4: Humanize the script (improve Telugu naturalness)
python -m workers.cli humanize-script

# Step 5: Run the Script Director gate (automated quality improvement)
python -m workers.cli direct-script

# Step 6: Plan 7 cinematic scenes
python -m workers.cli plan-scenes

# Step 7: Compose the video (dry-run if FFmpeg/assets missing)
python -m workers.cli compose-video

# Step 8: Create the review package
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
content/blueprints/ ← Locked story blueprints (JSON)
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
