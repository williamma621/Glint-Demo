from __future__ import annotations

import argparse
import json
from pathlib import Path

from glint_harness.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="glint-harness",
        description="Run the Glint matchmaking research harness.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Process transcripts and generate reports.")
    run_parser.add_argument("--input-dir", type=Path, required=True)
    run_parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        result = run_pipeline(input_dir=args.input_dir, output_dir=args.output_dir)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
