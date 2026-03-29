from __future__ import annotations

import json
from pathlib import Path

from glint_harness.models import ExtractedProfile, MatchResult


def ensure_output_dirs(output_dir: Path) -> tuple[Path, Path]:
    profiles_dir = output_dir / "profiles"
    reports_dir = output_dir / "reports"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    return profiles_dir, reports_dir


def write_profiles(profiles: list[ExtractedProfile], output_dir: Path) -> None:
    profiles_dir, _ = ensure_output_dirs(output_dir)
    for profile in profiles:
        path = profiles_dir / f"{profile.person_id}.json"
        path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")


def write_match_report(matches: list[MatchResult], output_dir: Path) -> Path:
    _, reports_dir = ensure_output_dirs(output_dir)
    path = reports_dir / "match_report.json"
    path.write_text(
        json.dumps([match.to_dict() for match in matches], indent=2),
        encoding="utf-8",
    )
    return path
