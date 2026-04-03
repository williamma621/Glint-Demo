import json
import shutil
import unittest
from pathlib import Path

from glint_harness.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_run_pipeline_creates_outputs(self) -> None:
        root = Path(__file__).resolve().parents[1]
        input_dir = root / "sample_data" / "transcripts"
        output_dir = root / "test_outputs"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        self.addCleanup(lambda: shutil.rmtree(output_dir, ignore_errors=True))

        result = run_pipeline(input_dir=input_dir, output_dir=output_dir)
        report_path = Path(result["report_path"])
        self.assertEqual(result["profiles_processed"], 3)
        self.assertEqual(result["matches_generated"], 3)
        self.assertTrue(report_path.exists())
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(len(report), 3)


if __name__ == "__main__":
    unittest.main()
