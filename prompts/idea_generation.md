# Prompt: Story Idea Generation — Midnight Telugu

## Task

Generate an original Telugu YouTube Shorts story idea for the Midnight Telugu channel.

## Requirements

- **Original**: Not inspired by any known film, Reddit post, news story, or other Telugu channel.
- **Hook-first**: The idea must start with a single sentence that creates an immediate question in the viewer's mind.
- **Category**: One of: midnight_mystery, village_mystery, family_suspense, psychological_twist, strange_event, soft_horror, crime_no_violence, emotional_suspense, karma_justice, poor_vs_rich.
- **Twist**: Every story must have an unexpected ending or reveal.
- **Telugu-appropriate**: Set in recognizable Telugu cultural context (AP/Telangana villages, cities, families).
- **Family-safe**: No graphic violence, sexual content, or hate speech.
- **Monetization-safe**: No political/religious controversy, no medical misinformation.
- **45–60 seconds when narrated**: Premise should be concise enough to tell in one Short.

## Output Format (JSON)

```json
{
  "id": "idea_<8-char-hex>",
  "title": "Telugu title",
  "category": "midnight_mystery",
  "hook": "Single gripping sentence in Telugu",
  "premise": "2-3 sentence setup",
  "twist": "The unexpected reveal",
  "tone": "e.g. suspenseful, eerie, emotional",
  "estimated_duration_seconds": 55,
  "originality_notes": "Why this is original",
  "safety_notes": "Why this is safe"
}
```

## Anti-patterns to Avoid

- "ఒకానొక రోజు..." openings
- Cheap moral lessons ("నీతి ఏమిటంటే")
- Celebrity or film references
- Real locations (use unnamed "ఒక ఊరు" or "హైదరాబాద్ శివార్లు")
- Predictable twists (lover returns, it was a dream)
