from __future__ import annotations

import math
from itertools import combinations

from glint_harness.models import ExtractedProfile, MatchResult


def generate_matches(profiles: list[ExtractedProfile]) -> list[MatchResult]:
    results: list[MatchResult] = []
    for left, right in combinations(profiles, 2):
        hard_pass, reasons = passes_hard_filters(left, right)
        if not hard_pass:
            results.append(
                MatchResult(
                    person_a_id=left.person_id,
                    person_b_id=right.person_id,
                    hard_filter_pass=False,
                    a_wants_b_score=0.0,
                    b_wants_a_score=0.0,
                    combined_score=0.0,
                    top_match_reasons=reasons,
                    review_status="blocked",
                )
            )
            continue

        a_wants_b = cosine_similarity(left.desired_vector, right.self_vector)
        b_wants_a = cosine_similarity(right.desired_vector, left.self_vector)
        combined = round((a_wants_b + b_wants_a) / 2, 4)
        explanation = explain_match(left, right, a_wants_b, b_wants_a)
        results.append(
            MatchResult(
                person_a_id=left.person_id,
                person_b_id=right.person_id,
                hard_filter_pass=True,
                a_wants_b_score=round(a_wants_b, 4),
                b_wants_a_score=round(b_wants_a, 4),
                combined_score=combined,
                top_match_reasons=explanation,
            )
        )
    return sorted(results, key=lambda item: (item.hard_filter_pass, item.combined_score), reverse=True)


def passes_hard_filters(left: ExtractedProfile, right: ExtractedProfile) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if left.consent_status != "consented" or right.consent_status != "consented":
        reasons.append("Missing tester consent.")
    if "underage_flag" in left.dealbreakers.explicit or "underage_flag" in right.dealbreakers.explicit:
        reasons.append("At least one profile appears underage.")
    if not _age_compatible(left, right):
        reasons.append("Age preferences are incompatible.")
    if not _relationship_intent_compatible(left, right):
        reasons.append("Relationship intent does not align.")
    if not _smoking_compatible(left, right):
        reasons.append("Smoking preference is incompatible.")
    if not _gender_compatible(left, right):
        reasons.append("Gender preference is incompatible or unknown.")

    return not reasons, reasons


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def explain_match(
    left: ExtractedProfile, right: ExtractedProfile, a_wants_b: float, b_wants_a: float
) -> list[str]:
    reasons: list[str] = []
    shared_values = sorted(
        set(left.traits_structured.values).intersection(right.traits_structured.values)
    )
    if shared_values:
        reasons.append(f"Shared values: {', '.join(shared_values[:3])}.")

    shared_interests = sorted(
        set(left.traits_structured.interests).intersection(right.traits_structured.interests)
    )
    if shared_interests:
        reasons.append(f"Shared interests: {', '.join(shared_interests[:3])}.")

    desired_hits_left = sorted(
        set(left.traits_structured.desired_partner_traits).intersection(
            right.traits_structured.personality_traits + right.traits_structured.values
        )
    )
    if desired_hits_left:
        reasons.append(
            f"{left.person_id} seeks traits that {right.person_id} appears to show: "
            f"{', '.join(desired_hits_left[:3])}."
        )

    desired_hits_right = sorted(
        set(right.traits_structured.desired_partner_traits).intersection(
            left.traits_structured.personality_traits + left.traits_structured.values
        )
    )
    if desired_hits_right:
        reasons.append(
            f"{right.person_id} seeks traits that {left.person_id} appears to show: "
            f"{', '.join(desired_hits_right[:3])}."
        )

    reasons.append(
        f"Reciprocal semantic fit is {round((a_wants_b + b_wants_a) / 2, 3)} "
        f"(A->B {round(a_wants_b, 3)}, B->A {round(b_wants_a, 3)})."
    )
    return reasons[:5]


def _age_compatible(left: ExtractedProfile, right: ExtractedProfile) -> bool:
    return _fits_age(left, right) and _fits_age(right, left)


def _fits_age(seeker: ExtractedProfile, candidate: ExtractedProfile) -> bool:
    age = candidate.basic_profile.age
    if age is None:
        return True
    minimum = seeker.constraints.age_min
    maximum = seeker.constraints.age_max
    if minimum is not None and age < minimum:
        return False
    if maximum is not None and age > maximum:
        return False
    return True


def _relationship_intent_compatible(left: ExtractedProfile, right: ExtractedProfile) -> bool:
    left_allowed = set(left.constraints.relationship_intents)
    right_allowed = set(right.constraints.relationship_intents)
    left_actual = right.relationship_intent.looking_for
    right_actual = left.relationship_intent.looking_for
    if left_allowed and left_actual and left_actual not in left_allowed:
        return False
    if right_allowed and right_actual and right_actual not in right_allowed:
        return False
    return True


def _smoking_compatible(left: ExtractedProfile, right: ExtractedProfile) -> bool:
    left_no_smoking = left.constraints.smoking_ok is False or "no_smoking" in left.dealbreakers.explicit
    right_no_smoking = right.constraints.smoking_ok is False or "no_smoking" in right.dealbreakers.explicit
    left_smoker = "smoker" in left.basic_profile.lifestyle_tags
    right_smoker = "smoker" in right.basic_profile.lifestyle_tags
    if left_no_smoking and right_smoker:
        return False
    if right_no_smoking and left_smoker:
        return False
    return True


def _gender_compatible(left: ExtractedProfile, right: ExtractedProfile) -> bool:
    return _fits_gender(left, right) and _fits_gender(right, left)


def _fits_gender(seeker: ExtractedProfile, candidate: ExtractedProfile) -> bool:
    genders = seeker.constraints.genders
    if not genders or "any" in genders:
        return True
    if candidate.basic_profile.gender_identity is None:
        return False
    normalized = candidate.basic_profile.gender_identity.lower()
    return normalized in {item.lower() for item in genders}
