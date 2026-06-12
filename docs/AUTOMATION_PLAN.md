# Automation Plan — Midnight Telugu

## v1: Local Draft Automation (Current)

All operations run locally. No external API required.

```
python -m workers.cli generate-ideas --count 5
python -m workers.cli generate-script
python -m workers.cli humanize-script
python -m workers.cli direct-script
python -m workers.cli plan-scenes
python -m workers.cli compose-video
python -m workers.cli create-review
```

All outputs go to `content/` and `outputs/`. Human reviews and approves. No upload.
If a DirectedScript exists and fails approval, `plan-scenes` stops by default unless `--allow-unapproved` is used for testing.

## v2: Real Provider Integration (Planned)

### Text Generation
Set `DEFAULT_TEXT_PROVIDER=anthropic` in `.env` and provide `ANTHROPIC_API_KEY`.
Workers will call Claude API for better story quality.

### Voice Generation
Set `DEFAULT_VOICE_PROVIDER=elevenlabs` and provide `ELEVENLABS_API_KEY`.
Workers will call ElevenLabs Telugu voice endpoint.

### Image Generation
Set `DEFAULT_IMAGE_PROVIDER=stability` and provide `IMAGE_PROVIDER_API_KEY`.
Workers will call Stability AI / SDXL for scene images.

### Video Composition
FFmpeg is already real in v1. In v2, improve with:
- Real subtitle overlay (`.srt` from script)
- Music bed from `assets/music/`
- Branded outro sequence

## v3: Semi-Automated Pipeline (Future)

- Scheduled daily idea generation
- Auto-queue for review
- Slack/email notification when draft is ready
- One-click upload after human approval

**Auto-upload will be opt-in and always require explicit human approval first.**
