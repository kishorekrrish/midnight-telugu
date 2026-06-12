# Prompt: Script Generation — Midnight Telugu

## Task

Convert a StoryIdea into a full Telugu narration script for a YouTube Short (45–60 seconds).

## Script Structure

1. **Hook (0–3s)** — The single most gripping sentence. Must make the viewer stop scrolling.
2. **Setup (3–15s)** — Brief context: who, where, what's wrong.
3. **Build-up (15–40s)** — Rising tension. Each sentence adds to the mystery/suspense.
4. **Twist/Reveal (40–52s)** — The unexpected turn. Delivered clearly, not rushed.
5. **Closing line (52–60s)** — A cinematic final line tied to the clue/twist, not an audience question.

## Language Rules

- Write in natural spoken Telugu — Andhra + Telangana neutral mix
- Short sentences for tension, longer sentences for description
- Use em-dashes (—) for dramatic pauses
- No textbook Telugu ("వారు నిష్క్రమించారు" → "వాళ్ళు వెళ్ళిపోయారు")
- No raw English phrases unless they are truly unavoidable in spoken Telugu
- No "ఒకానొక రోజు", no "నీతి ఏమిటంటే"

## Word Count Target

120–160 words at 130 wpm ≈ 55–75 seconds. Aim for tighter delivery.

## Output Format (JSON)

```json
{
  "hook_line": "Opening hook in Telugu",
  "full_script_telugu": "Full narration text with paragraph breaks for breathing",
  "youtube_title": "Telugu title | Midnight Telugu | Telugu Short Story",
  "youtube_description": "Telugu desc + hashtags",
  "youtube_hashtags": ["MidnightTelugu", "TeluguShorts", ...]
}
```

## Quality Checklist

- [ ] First line creates an immediate question
- [ ] Story is told, not summarized
- [ ] Twist is earned — not random
- [ ] Closing line is cinematic, clear, and connected to the reveal
- [ ] Reads naturally when spoken aloud
