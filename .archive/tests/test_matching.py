import unittest

from glint_harness.matching import cosine_similarity, generate_matches, passes_hard_filters
from glint_harness.models import (
    BasicProfile,
    Constraints,
    Dealbreakers,
    ExtractedProfile,
    RelationshipIntent,
    TraitsStructured,
)


def make_profile(
    person_id: str,
    *,
    age: int,
    gender: str,
    looking_for: str,
    age_min: int | None = None,
    age_max: int | None = None,
    genders: list[str] | None = None,
    relationship_intents: list[str] | None = None,
    lifestyle_tags: list[str] | None = None,
    values: list[str] | None = None,
    interests: list[str] | None = None,
    personality_traits: list[str] | None = None,
    desired_partner_traits: list[str] | None = None,
    self_vector: list[float] | None = None,
    desired_vector: list[float] | None = None,
) -> ExtractedProfile:
    return ExtractedProfile(
        person_id=person_id,
        basic_profile=BasicProfile(
            age=age,
            gender_identity=gender,
            lifestyle_tags=lifestyle_tags or [],
        ),
        relationship_intent=RelationshipIntent(looking_for=looking_for),
        constraints=Constraints(
            age_min=age_min,
            age_max=age_max,
            genders=genders or [],
            relationship_intents=relationship_intents or [],
        ),
        dealbreakers=Dealbreakers(),
        traits_structured=TraitsStructured(
            values=values or [],
            interests=interests or [],
            personality_traits=personality_traits or [],
            desired_partner_traits=desired_partner_traits or [],
        ),
        self_summary="self",
        desired_partner_summary="desired",
        self_vector=self_vector or [1.0, 0.0],
        desired_vector=desired_vector or [1.0, 0.0],
        extraction_confidence=0.9,
        consent_status="consented",
        created_at="now",
        updated_at="now",
        debug_source_hash="hash",
    )


class MatchingTests(unittest.TestCase):
    def test_cosine_similarity_exact_match(self) -> None:
        self.assertEqual(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)

    def test_hard_filter_rejects_age_mismatch(self) -> None:
        left = make_profile("a", age=30, gender="woman", looking_for="long_term", age_min=28, age_max=35)
        right = make_profile("b", age=40, gender="man", looking_for="long_term")
        passed, reasons = passes_hard_filters(left, right)
        self.assertFalse(passed)
        self.assertIn("Age preferences are incompatible.", reasons)

    def test_hard_filter_rejects_gender_mismatch(self) -> None:
        left = make_profile("a", age=30, gender="woman", looking_for="long_term", genders=["man"])
        right = make_profile("b", age=31, gender="woman", looking_for="long_term", genders=["woman"])
        passed, reasons = passes_hard_filters(left, right)
        self.assertFalse(passed)
        self.assertIn("Gender preference is incompatible or unknown.", reasons)

    def test_generate_matches_prefers_reciprocal_alignment(self) -> None:
        strong_a = make_profile(
            "a",
            age=30,
            gender="woman",
            looking_for="long_term",
            genders=["man"],
            relationship_intents=["long_term"],
            values=["kindness"],
            personality_traits=["communicative"],
            desired_partner_traits=["kindness", "communicative"],
            self_vector=[0.9, 0.1],
            desired_vector=[0.9, 0.1],
        )
        strong_b = make_profile(
            "b",
            age=31,
            gender="man",
            looking_for="long_term",
            genders=["woman"],
            relationship_intents=["long_term"],
            values=["kindness"],
            personality_traits=["communicative"],
            desired_partner_traits=["kindness"],
            self_vector=[0.88, 0.12],
            desired_vector=[0.88, 0.12],
        )
        weak_c = make_profile(
            "c",
            age=31,
            gender="man",
            looking_for="casual",
            genders=["woman"],
            relationship_intents=["casual"],
            self_vector=[0.0, 1.0],
            desired_vector=[0.0, 1.0],
        )

        matches = generate_matches([strong_a, strong_b, weak_c])
        self.assertEqual(matches[0].person_a_id, "a")
        self.assertEqual(matches[0].person_b_id, "b")
        self.assertGreater(matches[0].combined_score, matches[-1].combined_score)


if __name__ == "__main__":
    unittest.main()
