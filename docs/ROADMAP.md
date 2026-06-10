# Roadmap — Midnight Telugu

## v1.1 — Content Quality Hardening (Current)

- [x] StoryScorer — 8-dimension scoring (0-100, A-F grade)
- [x] StoryMemory — repeat-pattern detection across all generated content
- [x] Diverse idea generation — all 10 content buckets covered per batch
- [x] Script structure variety — 8 narrative structures (cold_open, object_mystery, etc.)
- [x] Improved Telugu humanizer — pacing, rhythm, AI-ending removal
- [x] Review Markdown — full draft review package in readable format
- [x] 77 passing tests

## v1 — Local Draft System (Current)

- [x] Project structure and configuration
- [x] Pydantic data models
- [x] Mock idea generator (10 content buckets)
- [x] Mock script generator (Telugu templates)
- [x] Telugu humanizer (naturalness improvements)
- [x] Scene planner (6-10 scenes per script)
- [x] Video composer (FFmpeg, dry-run mode)
- [x] Review queue (approve/reject workflow)
- [x] Analytics CSV tracking
- [x] CLI (Typer-based, 10 commands)
- [x] GitHub Actions CI
- [ ] Manual upload after approval

## v2 — Real Provider Integration

- [ ] Claude / OpenAI text generation for story ideas
- [ ] ElevenLabs Telugu voice synthesis
- [ ] Stability AI / SDXL image generation
- [ ] Subtitle generation (auto-sync from script)
- [ ] Background music mixing
- [ ] Branded outro sequence
- [ ] Thumbnail generation pipeline

## v3 — Scaled Production

- [ ] Batch generation (5 drafts/day queue)
- [ ] Review dashboard (simple web UI)
- [ ] Performance analytics visualization
- [ ] A/B testing for hooks and thumbnails
- [ ] Scheduled pipeline (cron/GitHub Actions)

## v4 — Channel Growth

- [ ] YouTube Data API integration (read-only analytics)
- [ ] Top-performing content pattern analysis
- [ ] Audience feedback loop into idea generation
- [ ] Optional semi-automated upload (still requires human approval)

**Auto-upload without human approval is never planned.**
