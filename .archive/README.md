# Glint Matchmaking Research Harness

This repository contains a minimal Python research harness for validating an LLM-first matchmaking pipeline.

The harness focuses on:

- guided intake conversations from trusted testers
- structured extraction into normalized profile data
- embeddings for self and desired-partner summaries
- hard constraint filtering before semantic scoring
- reciprocal compatibility scoring
- lightweight explanation generation
- research-facing report output for manual evaluation

## What it is

This is not a production dating app. It is a local validation tool for answering:

1. Can an LLM-guided intake produce stable profile representations?
2. Do the resulting top-ranked matches make sense to humans?

## Setup

```bash
pip install -e .
```

To enable live OpenAI extraction and embeddings, set:

```bash
set OPENAI_API_KEY=your_key_here
```

If no API key is provided, the harness uses deterministic local fallbacks so the pipeline can still be tested.

## Run the sample pipeline

```bash
glint-harness run --input-dir sample_data/transcripts --output-dir outputs
```
