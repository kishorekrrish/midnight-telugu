# Story Lab Phase 1A

Midnight Telugu should optimize story quality before media automation.

Primary flow:

```bash
python -m workers.cli generate-story-lab-package chandra-last-train --ideas 10 --top-blueprints 3 --scripts-per-blueprint 3 --max-candidates 5
```

This creates:

```text
stories/<slug>/
  story_brief.json
  idea_bank/ideas.json
  blueprints/blueprint_01.json
  blueprints/blueprint_02.json
  blueprints/blueprint_03.json
  script_candidates/
    bp01_candidate_01.txt
    bp01_candidate_01.meta.json
    ...
  script_review.md
  script.txt        # only when a candidate clears the best-in-class gate
  script_draft.txt  # highest-ranked draft when nothing clears the gate
```

The Story Lab loop is:

```text
Story brief
→ generate 10 ideas
→ score ideas with viral metrics
→ select top 3 ideas
→ build advanced blueprints
→ generate scripts through the Story Lab creative-director prompt
→ stop at the candidate budget, 5 by default
→ ruthless Shorts editor critique
→ rewrite loop
→ deterministic best-in-class editorial gate
→ script review package
→ manual approval
```

Viral scoring includes:

```text
scroll-stop hook
freshness
emotional punch
twist surprise
twist fairness
replay clue
visual simplicity
production feasibility
shareability
comment potential
```

Advanced blueprints include:

```text
opening_image
first_3_seconds_hook
protagonist_desire
hidden_truth
early_clue
misdirection
midpoint_turn
reveal_mechanism
final_recontextualization
replay_value_clue
emotional_aftertaste
```

Best-in-class approval requires all gates to pass:

```text
no narrative hard failures
script quality >= 92
Telugu authenticity >= 96
continuity >= 90
editor critique >= 88
editorial gate >= 88
no editorial blockers
```

The editorial gate checks hook strength, atmosphere, narrative drive, twist fairness, emotional aftertaste, Telugu voice, visual clarity, weak phrasing, word count, visible clue payoff, and generic-summary language.

Candidate budget:

```text
--max-candidates defaults to 5 and cannot exceed 5 from the CLI.
This protects OpenAI token usage and downstream provider credits.
```

Only approve after reading `script_review.md`:

```bash
python -m workers.cli approve-script stories/chandra-last-train --candidate <candidate_id> --notes "Approved from Story Lab"
```

Mocks are test-only. Production Story Lab generation uses OpenAI by default.
