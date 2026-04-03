from __future__ import annotations

from glint_harness.llm import compute_source_hash
from glint_harness.models import (
    BasicProfile,
    Constraints,
    Dealbreakers,
    ExtractedProfile,
    RelationshipIntent,
    TraitsStructured,
    TranscriptInput,
    utc_now_iso,
)


def normalize_extracted_profile(
    transcript: TranscriptInput,
    extracted: dict,
    self_vector: list[float],
    desired_vector: list[float],
) -> ExtractedProfile:
    timestamp = utc_now_iso()
    confidence = _clamp(float(extracted.get("extraction_confidence", 0.0)))
    consent_status = "consented" if transcript.consent else "missing_consent"

    basic_profile = BasicProfile(
        age=_optional_int(extracted.get("basic_profile", {}).get("age")),
        gender_identity=_optional_str(extracted.get("basic_profile", {}).get("gender_identity")),
        location=_optional_str(extracted.get("basic_profile", {}).get("location")),
        occupation=_optional_str(extracted.get("basic_profile", {}).get("occupation")),
        lifestyle_tags=_str_list(extracted.get("basic_profile", {}).get("lifestyle_tags")),
    )
    constraints = Constraints(
        age_min=_optional_int(extracted.get("constraints", {}).get("age_min")),
        age_max=_optional_int(extracted.get("constraints", {}).get("age_max")),
        genders=_str_list(extracted.get("constraints", {}).get("genders")),
        locations=_str_list(extracted.get("constraints", {}).get("locations")),
        max_distance_km=_optional_int(extracted.get("constraints", {}).get("max_distance_km")),
        relationship_intents=_str_list(extracted.get("constraints", {}).get("relationship_intents")),
        smoking_ok=_optional_bool(extracted.get("constraints", {}).get("smoking_ok")),
        drinking_ok=_optional_bool(extracted.get("constraints", {}).get("drinking_ok")),
    )
    relationship_intent = RelationshipIntent(
        looking_for=_optional_str(extracted.get("relationship_intent", {}).get("looking_for")),
        timeline=_optional_str(extracted.get("relationship_intent", {}).get("timeline")),
    )
    dealbreakers = Dealbreakers(
        explicit=_str_list(extracted.get("dealbreakers", {}).get("explicit")),
    )
    traits = TraitsStructured(
        values=_str_list(extracted.get("traits_structured", {}).get("values")),
        interests=_str_list(extracted.get("traits_structured", {}).get("interests")),
        personality_traits=_str_list(extracted.get("traits_structured", {}).get("personality_traits")),
        desired_partner_traits=_str_list(
            extracted.get("traits_structured", {}).get("desired_partner_traits")
        ),
    )

    return ExtractedProfile(
        person_id=transcript.person_id,
        basic_profile=basic_profile,
        relationship_intent=relationship_intent,
        constraints=constraints,
        dealbreakers=dealbreakers,
        traits_structured=traits,
        self_summary=_optional_str(extracted.get("self_summary")) or "",
        desired_partner_summary=_optional_str(extracted.get("desired_partner_summary")) or "",
        self_vector=self_vector,
        desired_vector=desired_vector,
        extraction_confidence=confidence,
        consent_status=consent_status,
        created_at=timestamp,
        updated_at=timestamp,
        debug_source_hash=compute_source_hash(transcript),
    )


def _optional_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            text = _optional_str(item)
            if text and text not in result:
                result.append(text)
        return result
    text = _optional_str(value)
    return [text] if text else []


def _optional_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "yes", "1"}:
        return True
    if text in {"false", "no", "0"}:
        return False
    return None


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
