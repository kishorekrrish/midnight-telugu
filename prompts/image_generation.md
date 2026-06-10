# Prompt: Image Generation — Midnight Telugu

## Style Guidelines

### Visual Identity
- Cinematic Indian/Telugu aesthetic
- Warm color palette for emotional scenes, cold/desaturated for horror/mystery
- Photorealistic — not illustrated, not animated
- Vertical 9:16 frame (1080x1920)

### Character Consistency
- Describe characters with consistent features across all scene prompts
- Use generic descriptors: "middle-aged Telugu man with dark kurta", "young woman with long hair in saree"
- Never reference real people or celebrities
- Never reference copyrighted characters

### Environment
- South Indian architecture: tile-roof houses, village wells, paddy fields, city apartments
- Authentic props: brass vessels, old calendars, kerosene lamps, smartphones
- Time of day must match the scene mood

### Lighting
- Night mystery: moonlight, single lamp light, shadows
- Village: natural daylight, harsh summer, monsoon grey
- Family drama: warm indoor tungsten, soft curtain light
- Psychological: high contrast, dutch angles, desaturated color

### Negative Prompts (Always Include)
```
blurry, low quality, distorted face, extra limbs, watermark, text overlay,
anime style, cartoon, 3D render, Western appearance, copyrighted characters,
celebrity likeness, nudity, gore, political imagery
```

## Provider Notes (Future)

When using Stability AI / SDXL:
- Model: stable-diffusion-xl-1024-v1-0 or similar
- Sampler: DPM++ 2M Karras
- Steps: 30–40
- CFG: 7–9
- Aspect ratio: 9:16 (1080x1920)
