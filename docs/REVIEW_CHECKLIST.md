# Human Review Checklist — Midnight Telugu

Before any draft is considered upload-ready, Kishore must manually verify:

## Story Quality
- [ ] Strong first 3 seconds — the hook immediately creates curiosity
- [ ] Original story — no copied plot from films, Reddit, news, or other channels
- [ ] No copied plot elements — verify the premise is not from known Telugu content
- [ ] Natural Telugu — the script sounds like a real storyteller, not a robot
- [ ] Tone matches the category (mystery feels mysterious, horror feels tense)

## Content Safety
- [ ] Family-safe — appropriate for all ages
- [ ] Monetization-safe — passes YouTube advertiser guidelines
- [ ] No graphic violence
- [ ] No political or religious controversy
- [ ] No real-person impersonation or celebrity references
- [ ] No medical/legal/financial misinformation

## Production Quality
- [ ] Visual consistency — scene images (if present) match the story mood
- [ ] Audio quality — voice narration is clear and properly paced
- [ ] Subtitles accurate (if present)
- [ ] Video dimensions: 1080x1920 (vertical Shorts format)
- [ ] Duration: 45–60 seconds

## Final Gates
- [ ] Final human review completed by Kishore
- [ ] **No auto-publish** — manual upload only after approval

## How to Approve

```bash
python -m workers.cli approve content/review/<review_id>.json --notes "Approved after review"
```

## How to Reject

```bash
python -m workers.cli reject content/review/<review_id>.json --notes "Reason for rejection"
```

Approved drafts move to `content/approved/`. Nothing is uploaded automatically.
