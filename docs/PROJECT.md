# Midnight Telugu — Project Documentation

## Purpose

Midnight Telugu is a local-first, AI-assisted Telugu YouTube Shorts draft production system. It generates original, cinematic Telugu short story drafts for mystery, crime, horror, and psychological twist content.

**This system creates drafts for human review — it does not auto-publish to YouTube.**

## Architecture

```
Idea Generation → Script Generation → Telugu Humanization
       ↓                  ↓                    ↓
  StoryIdea JSON    StoryScript JSON    HumanizedScript JSON
                                               ↓
                                       Scene Planning
                                               ↓
                                         ScenePlan JSON (6-10 scenes)
                                               ↓
                             Voice Generation    Image Generation
                                    ↓                   ↓
                              VoiceAsset           ImageAsset[]
                                               ↓
                                       Video Composition (FFmpeg)
                                               ↓
                                         VideoDraft JSON
                                               ↓
                                       Review Package Creation
                                               ↓
                                        ReviewStatus JSON
                                               ↓
                                    Human Review → Approve / Reject
```

## Provider Abstraction

Each worker module accepts a `provider` parameter:
- `"mock"` — uses local templates (v1 default, no API keys needed)
- `"openai"` — plug in OpenAI (future)
- `"anthropic"` — plug in Claude (future)
- `"elevenlabs"` — plug in ElevenLabs voice (future)
- `"stability"` — plug in Stability AI images (future)

Set in `.env` via `DEFAULT_TEXT_PROVIDER`, `DEFAULT_VOICE_PROVIDER`, `DEFAULT_IMAGE_PROVIDER`.

## Key Design Decisions

1. **No auto-publish in v1** — Human review is mandatory.
2. **Mock-first** — Every module works without paid API keys.
3. **Telugu-first** — All content is written in natural Telugu.
4. **Original stories only** — No copied Reddit/news/film plots.
5. **FFmpeg for video** — Industry-standard, local, no cloud dependency.
6. **Pydantic models** — All data is strongly typed and JSON-serializable.
