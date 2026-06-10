"""Midnight Telugu CLI — Typer-based command interface."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="midnight-telugu",
    help="Midnight Telugu — AI-assisted Telugu YouTube Shorts draft production system.",
    add_completion=False,
)
console = Console()


@app.command("init-project")
def init_project() -> None:
    """Create required directories and analytics CSV files."""
    from workers.config import (
        ALL_DIRS,
        PERFORMANCE_CSV,
        PERFORMANCE_CSV_HEADERS,
        VIDEOS_CSV,
        VIDEOS_CSV_HEADERS,
    )
    from workers.io_utils import ensure_csv

    console.print("[bold cyan]Initializing Midnight Telugu project...[/bold cyan]")
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        console.print(f"  [green]✓[/green] {d}")

    ensure_csv(VIDEOS_CSV, VIDEOS_CSV_HEADERS)
    console.print(f"  [green]✓[/green] {VIDEOS_CSV}")

    ensure_csv(PERFORMANCE_CSV, PERFORMANCE_CSV_HEADERS)
    console.print(f"  [green]✓[/green] {PERFORMANCE_CSV}")

    console.print("\n[bold green]Project initialized successfully.[/bold green]")
    console.print("Run: [yellow]python -m workers.cli generate-ideas --count 5[/yellow]")


@app.command("generate-ideas")
def generate_ideas(
    count: int = typer.Option(5, "--count", "-n", help="Number of ideas to generate"),
    provider: str | None = typer.Option(None, "--provider", help="AI provider (default: mock)"),
) -> None:
    """Generate original Telugu story ideas with quality scoring."""
    from workers.config import IDEAS_DIR
    from workers.idea_generator import generate_ideas as _gen
    from workers.io_utils import format_datetime, write_json

    console.print(f"[bold cyan]Generating {count} story ideas...[/bold cyan]")
    IDEAS_DIR.mkdir(parents=True, exist_ok=True)

    ideas = _gen(count=count, provider=provider)

    tbl = Table(show_header=True, header_style="bold magenta")
    tbl.add_column("Title", style="cyan", no_wrap=False, max_width=30)
    tbl.add_column("Category", style="yellow", max_width=20)
    tbl.add_column("Score", justify="right")
    tbl.add_column("Grade", justify="center")
    tbl.add_column("Warnings", style="red", max_width=30)

    for idea in ideas:
        filename = f"{idea.id}_{format_datetime(idea.created_at)}.json"
        out_path = IDEAS_DIR / filename
        write_json(out_path, idea)
        warn_str = str(len(idea.repeatability_warnings)) + " warning(s)" if idea.repeatability_warnings else "—"
        grade = idea.score_breakdown.get("grade") if isinstance(idea.score_breakdown, dict) else "?"
        # grade is in the full score dict returned by score_idea.to_dict()
        # score_breakdown on the model is just the sub-scores dict
        from workers.story_scorer import _grade
        grade = _grade(idea.story_score)
        tbl.add_row(idea.title, idea.category, str(idea.story_score), grade, warn_str)

    console.print(tbl)
    console.print(f"\n[bold green]{len(ideas)} ideas saved to content/ideas/[/bold green]")
    console.print("Next: [yellow]python -m workers.cli generate-script[/yellow]")


@app.command("generate-script")
def generate_script(
    idea_path: Path | None = typer.Option(None, "--idea", help="Path to idea JSON file"),
    provider: str | None = typer.Option(None, "--provider", help="AI provider (default: mock)"),
    variants: int = typer.Option(1, "--variants", help="Number of script variants to generate (1–5)"),
) -> None:
    """Generate a Telugu script from a story idea (use --variants N to generate N versions)."""
    from workers.config import IDEAS_DIR, SCRIPTS_DIR
    from workers.idea_generator import generate_ideas as _gen
    from workers.io_utils import format_datetime, latest_file, read_json, write_json
    from workers.models import StoryIdea
    from workers.script_generator import generate_script as _gen_script
    from workers.script_quality import validate_script
    from workers.story_scorer import score_script

    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    if idea_path:
        idea = read_json(idea_path, StoryIdea)
    else:
        found = latest_file(IDEAS_DIR)
        if not found:
            console.print("[yellow]No ideas found. Generating one first...[/yellow]")
            ideas = _gen(count=1)
            idea = ideas[0]
            filename = f"{idea.id}_{format_datetime(idea.created_at)}.json"
            write_json(IDEAS_DIR / filename, idea)
        else:
            idea = read_json(found, StoryIdea)

    variants = max(1, min(5, variants))
    console.print(f"[bold cyan]Generating {variants} script variant(s) for: {idea.title}[/bold cyan]")

    best_script = None
    best_sq_score = -1

    for v in range(variants):
        script = _gen_script(idea, provider=provider)
        score = score_script(script, repeatability_warnings=getattr(idea, "repeatability_warnings", []))
        sq = validate_script(script)

        variant_label = f"Variant {v + 1}" if variants > 1 else "Script"
        console.print(
            f"  {variant_label}: story={score.overall_score}/100 ({score.grade})  "
            f"quality={sq.quality_score}/100  rec={sq.publish_recommendation}"
        )
        if score.improvement_suggestions:
            for s in score.improvement_suggestions[:1]:
                console.print(f"    [dim]💡 {s}[/dim]")
        if sq.issues:
            for issue in sq.issues[:1]:
                console.print(f"    [yellow]⚠ {issue}[/yellow]")

        filename = f"{script.id}_{format_datetime(script.created_at)}.json"
        out_path = SCRIPTS_DIR / filename
        write_json(out_path, script)

        if sq.quality_score > best_sq_score:
            best_sq_score = sq.quality_score
            best_script = script
            best_path = out_path

    script = best_script  # type: ignore[assignment]
    out_path = best_path  # type: ignore[assignment]

    if variants > 1:
        console.print(f"\n  [green]★[/green] Best variant saved → {out_path.name} (quality={best_sq_score}/100)")
    else:
        console.print(f"  [green]✓[/green] Script saved → {out_path.name}")
    console.print(f"  Duration: ~{script.estimated_duration_seconds}s")
    console.print("\nNext: [yellow]python -m workers.cli humanize-script[/yellow]")


@app.command("humanize-script")
def humanize_script(
    script_path: Path | None = typer.Option(None, "--script", help="Path to script JSON file"),
    provider: str | None = typer.Option(None, "--provider", help="AI provider (default: mock)"),
) -> None:
    """Improve Telugu flow and naturalness of a generated script."""
    from workers.config import SCRIPTS_DIR
    from workers.io_utils import format_datetime, latest_file, read_json, write_json
    from workers.models import StoryScript
    from workers.telugu_humanizer import humanize_script as _humanize

    if script_path:
        script = read_json(script_path, StoryScript)
    else:
        found = latest_file(SCRIPTS_DIR)
        if not found:
            console.print("[red]No scripts found. Run generate-script first.[/red]")
            raise typer.Exit(1)
        # Prefer StoryScript (not HumanizedScript which also lives here)
        try:
            script = read_json(found, StoryScript)
        except Exception:  # noqa: BLE001
            console.print("[red]Could not parse latest script file as StoryScript.[/red]")
            raise typer.Exit(1) from None

    console.print(f"[bold cyan]Humanizing script: {script.title}[/bold cyan]")
    humanized = _humanize(script, provider=provider)

    filename = f"{humanized.id}_{format_datetime(humanized.created_at)}.json"
    out_path = SCRIPTS_DIR / filename
    write_json(out_path, humanized)

    console.print(f"  [green]✓[/green] Humanized script saved → {out_path.name}")
    console.print(f"  [dim]{humanized.humanization_notes}[/dim]")
    console.print("\nNext: [yellow]python -m workers.cli plan-scenes[/yellow]")


@app.command("plan-scenes")
def plan_scenes(
    script_path: Path | None = typer.Option(None, "--script", help="Path to script/humanized JSON"),
    num_scenes: int = typer.Option(7, "--scenes", help="Number of scenes (6-10)"),
) -> None:
    """Convert a script into a production-ready scene plan."""
    from workers.config import SCENES_DIR, SCRIPTS_DIR
    from workers.io_utils import format_datetime, latest_file, read_json, write_json
    from workers.models import HumanizedScript, StoryScript
    from workers.scene_planner import plan_scenes as _plan

    SCENES_DIR.mkdir(parents=True, exist_ok=True)

    if script_path:
        try:
            script = read_json(script_path, HumanizedScript)
        except Exception:
            script = read_json(script_path, StoryScript)
    else:
        found = latest_file(SCRIPTS_DIR)
        if not found:
            console.print("[red]No scripts found. Run generate-script first.[/red]")
            raise typer.Exit(1)
        try:
            script = read_json(found, HumanizedScript)
        except Exception:
            script = read_json(found, StoryScript)

    console.print(f"[bold cyan]Planning {num_scenes} scenes for: {script.title}[/bold cyan]")
    scene_plan = _plan(script, num_scenes=num_scenes)

    filename = f"{scene_plan.id}_{format_datetime(scene_plan.created_at)}.json"
    out_path = SCENES_DIR / filename
    write_json(out_path, scene_plan)

    console.print(f"  [green]✓[/green] Scene plan saved → {out_path.name}")
    console.print(f"  Scenes: {scene_plan.total_scenes}")
    console.print("\nNext: [yellow]python -m workers.cli compose-video[/yellow]")


@app.command("compose-video")
def compose_video(
    scene_plan_path: Path | None = typer.Option(None, "--scenes", help="Path to scene plan JSON"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Force dry-run mode"),
) -> None:
    """Compose a draft video from scene plan and assets (dry-run if assets missing)."""
    from workers.config import SCENES_DIR, VIDEOS_OUT_DIR
    from workers.image_generator import generate_images
    from workers.io_utils import format_datetime, latest_file, read_json, write_json
    from workers.models import ScenePlan
    from workers.video_composer import compose_video as _compose

    if scene_plan_path:
        scene_plan = read_json(scene_plan_path, ScenePlan)
    else:
        found = latest_file(SCENES_DIR)
        if not found:
            console.print("[red]No scene plans found. Run plan-scenes first.[/red]")
            raise typer.Exit(1)
        scene_plan = read_json(found, ScenePlan)

    console.print(f"[bold cyan]Composing video for: {scene_plan.title}[/bold cyan]")

    image_assets = generate_images(scene_plan)
    draft = _compose(scene_plan, image_assets, voice_asset=None, dry_run=dry_run)

    filename = f"{draft.id}_{format_datetime(draft.created_at)}.json"
    out_path = VIDEOS_OUT_DIR / filename
    write_json(out_path, draft)

    if draft.is_dry_run:
        console.print("  [yellow]⚡ DRY RUN[/yellow] — no real video rendered (FFmpeg or assets missing)")
        console.print(f"  Draft metadata saved → {out_path.name}")
    else:
        console.print(f"  [green]✓[/green] Video → {draft.video_path}")

    console.print("\nNext: [yellow]python -m workers.cli create-review[/yellow]")


@app.command("create-review")
def create_review(
    title: str | None = typer.Option(None, "--title", help="Override title"),
) -> None:
    """Create a human review package (JSON + Markdown) for the latest draft."""
    from workers.config import SCENES_DIR, SCRIPTS_DIR, VIDEOS_OUT_DIR
    from workers.io_utils import latest_file, read_json
    from workers.models import HumanizedScript, ScenePlan, StoryScript
    from workers.review_queue import create_review as _create_review
    from workers.script_quality import validate_script

    latest_script_path = latest_file(SCRIPTS_DIR)
    latest_scenes_path = latest_file(SCENES_DIR)
    latest_video_path = latest_file(VIDEOS_OUT_DIR)

    draft_title = title
    hook = ""
    category = "midnight_mystery"
    script_text = ""
    youtube_title = ""
    youtube_description = ""
    youtube_hashtags: list[str] = []
    score_breakdown: dict = {}
    repeatability_warnings: list[str] = []

    script_obj = None
    base_script_obj: StoryScript | None = None
    if latest_script_path:
        try:
            script_obj = read_json(latest_script_path, HumanizedScript)
        except Exception:
            try:
                script_obj = read_json(latest_script_path, StoryScript)
            except Exception:
                pass

    if script_obj:
        draft_title = draft_title or script_obj.title
        hook = script_obj.hook_line
        category = script_obj.category if isinstance(script_obj.category, str) else script_obj.category.value
        script_text = script_obj.full_script_telugu
        if hasattr(script_obj, "youtube_title"):
            youtube_title = script_obj.youtube_title  # type: ignore[union-attr]
            youtube_description = script_obj.youtube_description  # type: ignore[union-attr]
            youtube_hashtags = script_obj.youtube_hashtags  # type: ignore[union-attr]

    # If we have a humanized script, also load the original StoryScript for YouTube metadata + scoring
    if isinstance(script_obj, HumanizedScript):
        orig_path = latest_file(SCRIPTS_DIR, pattern="script_*.json")
        if orig_path:
            try:
                base_script_obj = read_json(orig_path, StoryScript)
                if not youtube_title:
                    youtube_title = base_script_obj.youtube_title
                    youtube_description = base_script_obj.youtube_description
                    youtube_hashtags = base_script_obj.youtube_hashtags
            except Exception:
                pass

    if not draft_title:
        draft_title = "Untitled Draft"

    # Build scene table for markdown
    scene_table = ""
    if latest_scenes_path:
        try:
            sp = read_json(latest_scenes_path, ScenePlan)
            rows = ["| # | Timestamp | Location | Mood | Camera |",
                    "|---|-----------|----------|------|--------|"]
            for s in sp.scenes:
                rows.append(
                    f"| {s.scene_number} | {s.timestamp_range} | {s.location} | {s.mood} | {s.camera_angle} |"
                )
            scene_table = "\n".join(rows)
        except Exception:
            pass

    video_path = None
    if latest_video_path:
        try:
            from workers.models import VideoDraft
            vd = read_json(latest_video_path, VideoDraft)
            video_path = vd.video_path
        except Exception:
            pass

    # Score the script and run quality validation
    script_quality_dict: dict = {}
    if script_obj and hasattr(script_obj, "full_script_telugu"):
        from workers.story_scorer import score_script
        sq_result = validate_script(script_obj)
        script_quality_dict = sq_result.to_dict()
        scoring_target = base_script_obj if base_script_obj else (script_obj if isinstance(script_obj, StoryScript) else None)
        if scoring_target:
            sc = score_script(scoring_target, repeatability_warnings=repeatability_warnings)
            score_breakdown = sc.to_dict()["score_breakdown"]

    console.print(f"[bold cyan]Creating review package: {draft_title}[/bold cyan]")

    review, md_path = _create_review(
        title=draft_title,
        category=category,
        hook=hook,
        script_path=str(latest_script_path) if latest_script_path else None,
        scene_plan_path=str(latest_scenes_path) if latest_scenes_path else None,
        video_path=video_path,
        script_text=script_text,
        scene_table=scene_table,
        youtube_title=youtube_title,
        youtube_description=youtube_description,
        youtube_hashtags=youtube_hashtags,
        score_breakdown=score_breakdown,
        repeatability_warnings=repeatability_warnings,
        script_quality=script_quality_dict,
    )

    console.print(f"  [green]✓[/green] JSON  → content/review/{review.id}.json")
    console.print(f"  [green]✓[/green] [bold]Markdown → {md_path}[/bold]")
    console.print(f"  Status: [yellow]{review.status}[/yellow]")

    if script_quality_dict:
        rec = script_quality_dict.get("publish_recommendation", "needs_rewrite")
        sq_score = script_quality_dict.get("quality_score", 0)
        rec_colors = {"approve_candidate": "green", "needs_rewrite": "yellow", "reject": "red"}
        color = rec_colors.get(rec, "white")
        console.print(f"  Script quality: [{color}]{sq_score}/100 — {rec}[/{color}]")

    console.print("\n[bold]Review checklist — complete manually before approving:[/bold]")
    for field, val in review.checklist.model_dump().items():
        icon = "[green]✓[/green]" if val else "[red]✗[/red]"
        console.print(f"  {icon} {field.replace('_', ' ')}")

    console.print(f"\nTo approve: [yellow]python -m workers.cli approve content/review/{review.id}.json[/yellow]")
    console.print(f"Open for review: [cyan]{md_path}[/cyan]")


@app.command("approve")
def approve(
    review_path: Path = typer.Argument(..., help="Path to review JSON file"),
    notes: str = typer.Option("", "--notes", help="Approval notes"),
) -> None:
    """Approve a reviewed draft (does not upload anywhere)."""
    from workers.review_queue import approve_review

    review = approve_review(review_path, notes=notes)
    console.print(f"[bold green]✓ Approved:[/bold green] {review.title}")
    console.print("  Saved to content/approved/")
    console.print("[yellow]NOTE: No upload has occurred. This is draft approval only.[/yellow]")


@app.command("reject")
def reject(
    review_path: Path = typer.Argument(..., help="Path to review JSON file"),
    notes: str = typer.Option("", "--notes", help="Rejection reason"),
) -> None:
    """Reject a reviewed draft."""
    from workers.review_queue import reject_review

    review = reject_review(review_path, notes=notes)
    console.print(f"[bold red]✗ Rejected:[/bold red] {review.title}")
    if notes:
        console.print(f"  Reason: {notes}")


@app.command("record-performance")
def record_performance(
    video_id: str = typer.Argument(..., help="Video ID from analytics/videos.csv"),
    record_date: str = typer.Option(str(date.today()), "--date", help="Date (YYYY-MM-DD)"),
    views: int = typer.Option(0, "--views"),
    likes: int = typer.Option(0, "--likes"),
    comments: int = typer.Option(0, "--comments"),
    shares: int = typer.Option(0, "--shares"),
    avg_duration: float = typer.Option(0.0, "--avg-duration"),
    retention: float = typer.Option(0.0, "--retention"),
    subs_gained: int = typer.Option(0, "--subs"),
    notes: str = typer.Option("", "--notes"),
) -> None:
    """Record manual YouTube performance data."""
    from workers.analytics_tracker import record_performance as _record
    from workers.models import PerformanceRecord

    rec = PerformanceRecord(
        video_id=video_id,
        date=record_date,
        views=views,
        likes=likes,
        comments=comments,
        shares=shares,
        average_view_duration=avg_duration,
        retention_percentage=retention,
        subscribers_gained=subs_gained,
        notes=notes,
    )
    _record(rec)
    console.print(f"[green]✓[/green] Performance recorded for {video_id} on {record_date}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
