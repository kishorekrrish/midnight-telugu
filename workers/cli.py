"""Midnight Telugu CLI — Typer-based command interface."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import typer
from rich.console import Console

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
    """Generate original Telugu story ideas."""
    from workers.config import IDEAS_DIR
    from workers.idea_generator import generate_ideas as _gen
    from workers.io_utils import format_datetime, write_json

    console.print(f"[bold cyan]Generating {count} story ideas...[/bold cyan]")
    IDEAS_DIR.mkdir(parents=True, exist_ok=True)

    ideas = _gen(count=count, provider=provider)
    for idea in ideas:
        filename = f"{idea.id}_{format_datetime(idea.created_at)}.json"
        out_path = IDEAS_DIR / filename
        write_json(out_path, idea)
        console.print(f"  [green]✓[/green] {idea.title} → {out_path.name}")

    console.print(f"\n[bold green]{len(ideas)} ideas saved to content/ideas/[/bold green]")
    console.print("Next: [yellow]python -m workers.cli generate-script[/yellow]")


@app.command("generate-script")
def generate_script(
    idea_path: Path | None = typer.Option(None, "--idea", help="Path to idea JSON file"),
    provider: str | None = typer.Option(None, "--provider", help="AI provider (default: mock)"),
) -> None:
    """Generate a Telugu script from a story idea."""
    from workers.config import IDEAS_DIR, SCRIPTS_DIR
    from workers.idea_generator import generate_ideas as _gen
    from workers.io_utils import format_datetime, latest_file, read_json, write_json
    from workers.models import StoryIdea
    from workers.script_generator import generate_script as _gen_script

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

    console.print(f"[bold cyan]Generating script for: {idea.title}[/bold cyan]")
    script = _gen_script(idea, provider=provider)

    filename = f"{script.id}_{format_datetime(script.created_at)}.json"
    out_path = SCRIPTS_DIR / filename
    write_json(out_path, script)

    console.print(f"  [green]✓[/green] Script saved → {out_path}")
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
        script = read_json(found, StoryScript)

    console.print(f"[bold cyan]Humanizing script: {script.title}[/bold cyan]")
    humanized = _humanize(script, provider=provider)

    filename = f"{humanized.id}_{format_datetime(humanized.created_at)}.json"
    out_path = SCRIPTS_DIR / filename
    write_json(out_path, humanized)

    console.print(f"  [green]✓[/green] Humanized script saved → {out_path}")
    console.print(f"  Notes: {humanized.humanization_notes}")
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
        # Try HumanizedScript first, fall back to StoryScript
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

    console.print(f"  [green]✓[/green] Scene plan saved → {out_path}")
    console.print(f"  Scenes: {scene_plan.total_scenes}")
    console.print("\nNext: [yellow]python -m workers.cli compose-video[/yellow]")


@app.command("compose-video")
def compose_video(
    scene_plan_path: Path | None = typer.Option(None, "--scenes", help="Path to scene plan JSON"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Force dry-run mode"),
) -> None:
    """Compose a draft video from scene plan and assets (dry-run if assets missing)."""
    from workers.config import SCENES_DIR
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

    # Generate mock assets
    image_assets = generate_images(scene_plan)
    voice_asset = None  # no real voice in mock mode

    draft = _compose(scene_plan, image_assets, voice_asset=voice_asset, dry_run=dry_run)

    from workers.config import VIDEOS_OUT_DIR
    filename = f"{draft.id}_{format_datetime(draft.created_at)}.json"
    out_path = VIDEOS_OUT_DIR / filename
    write_json(out_path, draft)

    if draft.is_dry_run:
        console.print("  [yellow]⚡ DRY RUN[/yellow] — no real video rendered (FFmpeg or assets missing)")
        console.print(f"  Draft metadata saved → {out_path}")
        if draft.ffmpeg_command:
            console.print("\n  [dim]FFmpeg command (for reference):[/dim]")
            console.print(f"  [dim]{draft.ffmpeg_command[:120]}...[/dim]")
    else:
        console.print(f"  [green]✓[/green] Video → {draft.video_path}")

    console.print("\nNext: [yellow]python -m workers.cli create-review[/yellow]")


@app.command("create-review")
def create_review(
    title: str | None = typer.Option(None, "--title", help="Override title"),
) -> None:
    """Create a human review package for the latest draft."""
    from workers.config import SCENES_DIR, SCRIPTS_DIR, VIDEOS_OUT_DIR
    from workers.io_utils import latest_file, read_json
    from workers.models import StoryScript
    from workers.review_queue import create_review as _create_review

    # Gather latest assets
    latest_script = latest_file(SCRIPTS_DIR)
    latest_scenes = latest_file(SCENES_DIR)
    latest_video = latest_file(VIDEOS_OUT_DIR)

    draft_title = title
    hook = ""
    category = "midnight_mystery"

    if latest_script:
        try:
            from workers.models import HumanizedScript
            s = read_json(latest_script, HumanizedScript)
        except Exception:
            s = read_json(latest_script, StoryScript)
        draft_title = draft_title or s.title
        hook = s.hook_line
        category = s.category if isinstance(s.category, str) else s.category.value

    if not draft_title:
        draft_title = "Untitled Draft"

    video_path = None
    if latest_video:
        try:
            from workers.models import VideoDraft
            vd = read_json(latest_video, VideoDraft)
            video_path = vd.video_path
        except Exception:
            pass

    console.print(f"[bold cyan]Creating review package: {draft_title}[/bold cyan]")

    review = _create_review(
        title=draft_title,
        category=category,
        hook=hook,
        script_path=str(latest_script) if latest_script else None,
        scene_plan_path=str(latest_scenes) if latest_scenes else None,
        video_path=video_path,
    )

    console.print(f"  [green]✓[/green] Review created → content/review/{review.id}.json")
    console.print(f"  Status: [yellow]{review.status}[/yellow]")
    console.print("\n[bold]Review checklist — complete manually before approving:[/bold]")
    for field, val in review.checklist.model_dump().items():
        icon = "[green]✓[/green]" if val else "[red]✗[/red]"
        console.print(f"  {icon} {field.replace('_', ' ')}")

    console.print(f"\nTo approve: [yellow]python -m workers.cli approve --review content/review/{review.id}.json[/yellow]")


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
