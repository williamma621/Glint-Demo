from __future__ import annotations

import json
from pathlib import Path

from glint_harness.models import TranscriptInput, TranscriptMessage


def load_transcripts(input_dir: Path) -> list[TranscriptInput]:
    transcripts: list[TranscriptInput] = []
    for path in sorted(input_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        messages = [
            TranscriptMessage(role=item["role"], content=item["content"])
            for item in data["chat_history"]
        ]
        transcripts.append(
            TranscriptInput(
                person_id=data["person_id"],
                consent=bool(data.get("consent", False)),
                chat_history=messages,
            )
        )
    return transcripts
