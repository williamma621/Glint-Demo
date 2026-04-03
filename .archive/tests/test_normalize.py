import unittest

from glint_harness.models import TranscriptInput, TranscriptMessage
from glint_harness.normalize import normalize_extracted_profile


class NormalizeTests(unittest.TestCase):
    def test_normalize_coerces_types_and_clamps_confidence(self) -> None:
        transcript = TranscriptInput(
            person_id="alice",
            consent=True,
            chat_history=[TranscriptMessage(role="user", content="hello")],
        )
        extracted = {
            "basic_profile": {"age": "29", "gender_identity": "woman", "lifestyle_tags": ["hiking", "hiking"]},
            "relationship_intent": {"looking_for": "long_term"},
            "constraints": {"age_min": "27", "age_max": "35", "genders": ["man"], "smoking_ok": "false"},
            "dealbreakers": {"explicit": ["no_smoking"]},
            "traits_structured": {"values": ["kindness"], "desired_partner_traits": ["honesty"]},
            "self_summary": "A thoughtful designer.",
            "desired_partner_summary": "Wants a kind partner.",
            "extraction_confidence": 1.5,
        }

        profile = normalize_extracted_profile(
            transcript=transcript,
            extracted=extracted,
            self_vector=[0.1],
            desired_vector=[0.2],
        )

        self.assertEqual(profile.basic_profile.age, 29)
        self.assertEqual(profile.constraints.age_min, 27)
        self.assertFalse(profile.constraints.smoking_ok)
        self.assertEqual(profile.basic_profile.lifestyle_tags, ["hiking"])
        self.assertEqual(profile.extraction_confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
