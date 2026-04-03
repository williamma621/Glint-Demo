from __future__ import annotations

from pathlib import Path

from glint_harness.intake import load_transcripts
from glint_harness.llm import build_provider
from glint_harness.matching import generate_matches
from glint_harness.normalize import normalize_extracted_profile
from glint_harness.storage import write_match_report, write_profiles


def run_pipeline(input_dir: Path, output_dir: Path) -> dict[str, object]:
    provider = build_provider()
    transcripts = load_transcripts(input_dir)

    profiles = []
    for transcript in transcripts:
        extracted = provider.extract_profile(transcript)
        self_vector = provider.embed_text(extracted.get("self_summary", ""))
        desired_vector = provider.embed_text(extracted.get("desired_partner_summary", ""))
        profile = normalize_extracted_profile(
            transcript=transcript,
            extracted=extracted,
            self_vector=self_vector,
            desired_vector=desired_vector,
        )
        profiles.append(profile)

    matches = generate_matches(profiles)
    write_profiles(profiles, output_dir)
    report_path = write_match_report(matches, output_dir)

    return {
        "profiles_processed": len(profiles),
        "matches_generated": len(matches),
        "report_path": str(report_path),
    }
