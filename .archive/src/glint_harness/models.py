from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TranscriptMessage:
    role: str
    content: str


@dataclass
class TranscriptInput:
    person_id: str
    consent: bool
    chat_history: list[TranscriptMessage]


@dataclass
class BasicProfile:
    age: int | None = None
    gender_identity: str | None = None
    location: str | None = None
    occupation: str | None = None
    lifestyle_tags: list[str] = field(default_factory=list)


@dataclass
class RelationshipIntent:
    looking_for: str | None = None
    timeline: str | None = None


@dataclass
class Constraints:
    age_min: int | None = None
    age_max: int | None = None
    genders: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    max_distance_km: int | None = None
    relationship_intents: list[str] = field(default_factory=list)
    smoking_ok: bool | None = None
    drinking_ok: bool | None = None


@dataclass
class Dealbreakers:
    explicit: list[str] = field(default_factory=list)


@dataclass
class TraitsStructured:
    values: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    personality_traits: list[str] = field(default_factory=list)
    desired_partner_traits: list[str] = field(default_factory=list)


@dataclass
class ExtractedProfile:
    person_id: str
    basic_profile: BasicProfile
    relationship_intent: RelationshipIntent
    constraints: Constraints
    dealbreakers: Dealbreakers
    traits_structured: TraitsStructured
    self_summary: str
    desired_partner_summary: str
    self_vector: list[float]
    desired_vector: list[float]
    extraction_confidence: float
    consent_status: str
    created_at: str
    updated_at: str
    debug_source_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MatchResult:
    person_a_id: str
    person_b_id: str
    hard_filter_pass: bool
    a_wants_b_score: float
    b_wants_a_score: float
    combined_score: float
    top_match_reasons: list[str]
    review_status: str = "pending"
    human_eval_rating: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
