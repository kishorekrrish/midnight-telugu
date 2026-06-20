"""Per-story workspace helpers for stories/<slug> production packages."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from workers.production_models import ScriptApproval, now_iso

APPROVAL_ERROR = "Script is not approved. Run approve-script before production."


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "untitled-story"


def story_dir_from_arg(story: str | Path) -> Path:
    path = Path(story)
    if path.parts and path.parts[0] == "stories":
        return path
    if len(path.parts) > 1:
        return path
    return Path("stories") / slugify(str(story))


class StoryWorkspace:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.slug = root.name

    @classmethod
    def from_arg(cls, story: str | Path, create: bool = False) -> StoryWorkspace:
        ws = cls(story_dir_from_arg(story))
        if create:
            ws.ensure()
        return ws

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "script_candidates").mkdir(exist_ok=True)
        (self.root / "clips").mkdir(exist_ok=True)

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    def read_json(self, name: str) -> dict[str, Any]:
        return json.loads(self.path(name).read_text(encoding="utf-8"))

    def write_json(self, name: str, data: Any) -> Path:
        path = self.path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(data, "model_dump"):
            payload = data.model_dump(mode="json")
        else:
            payload = data
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def approval(self) -> ScriptApproval | None:
        path = self.path("script_approval.json")
        if not path.exists():
            return None
        return ScriptApproval.model_validate_json(path.read_text(encoding="utf-8"))

    def require_approved_script(self) -> ScriptApproval:
        approval = self.approval()
        script_path = self.path("script.txt")
        if not approval or not approval.approved or not script_path.exists():
            raise RuntimeError(APPROVAL_ERROR)
        return approval

    def copy_into(self, source: Path, target_name: str, overwrite: bool = True) -> Path:
        target = self.path(target_name)
        if target.exists() and not overwrite:
            raise FileExistsError(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return target

    def write_rejection(self, candidate: str, notes: str) -> Path:
        existing: list[dict[str, Any]]
        path = self.path("script_rejections.json")
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        existing.append(
            {
                "story_slug": self.slug,
                "candidate": candidate,
                "approved": False,
                "rejected_at": now_iso(),
                "notes": notes,
            }
        )
        path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
