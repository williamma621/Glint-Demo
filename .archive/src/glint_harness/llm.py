from __future__ import annotations

import hashlib
import json
import math
import os
from abc import ABC, abstractmethod
from typing import Any

from glint_harness.models import TranscriptInput


EXTRACTION_MODEL = "gpt-4.1-mini"
EMBEDDING_MODEL = "text-embedding-3-small"


EXTRACTION_PROMPT = """
You are extracting a normalized matchmaking research profile from a consented intake chat.

Requirements:
- Only include adults. If the user appears under 18, set confidence to 0 and note the issue in dealbreakers.
- Return strict JSON.
- Infer carefully but prefer null over unsupported certainty.
- Produce:
  - basic_profile
  - relationship_intent
  - constraints
  - dealbreakers
  - traits_structured
  - self_summary
  - desired_partner_summary
  - extraction_confidence
""".strip()


class LLMProvider(ABC):
    @abstractmethod
    def extract_profile(self, transcript: TranscriptInput) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError


class DeterministicFallbackProvider(LLMProvider):
    def extract_profile(self, transcript: TranscriptInput) -> dict[str, Any]:
        conversation = "\n".join(
            f"{message.role}: {message.content}" for message in transcript.chat_history
        )
        lowered = conversation.lower()

        def any_keyword(*terms: str) -> bool:
            return any(term in lowered for term in terms)

        age = _find_first_int_after_keywords(lowered, ["i'm ", "i am ", "age ", "turned "])
        age_min, age_max = _find_age_range(lowered)
        relationship = "long_term" if any_keyword("long-term", "long term", "serious relationship") else None
        if relationship is None and any_keyword("casual", "keep it light"):
            relationship = "casual"

        gender_identity = "woman" if any_keyword("i'm a woman", "i am a woman") else None
        if gender_identity is None and any_keyword("i'm a man", "i am a man"):
            gender_identity = "man"

        genders: list[str] = []
        if any_keyword("with a woman", "open to women", "looking for a woman", "looking for women"):
            genders.append("woman")
        if any_keyword("with a man", "open to men", "looking for a man", "looking for men"):
            genders.append("man")
        if not genders and any_keyword("any gender", "open to all genders"):
            genders.append("any")

        values = [
            value
            for value in ["kindness", "ambition", "curiosity", "stability", "humor", "honesty", "empathy"]
            if value in lowered
        ]
        interests = [
            item
            for item in ["hiking", "reading", "travel", "cooking", "music", "gaming", "fitness", "art"]
            if item in lowered
        ]
        personality_traits = [
            item
            for item in ["introverted", "extroverted", "thoughtful", "playful", "calm", "driven", "outgoing"]
            if item in lowered
        ]
        desired_traits = [
            item
            for item in ["emotionally mature", "communicative", "kind", "funny", "ambitious", "stable"]
            if item in lowered
        ]

        explicit: list[str] = []
        if any_keyword("no smokers", "don't want someone who smokes", "do not smoke", "doesn't smoke"):
            explicit.append("no_smoking")
        if age is not None and age < 18:
            explicit.append("underage_flag")

        self_summary = _short_summary(
            lowered,
            default="Adult tester with identifiable relationship preferences and lifestyle traits.",
        )
        desired_summary = _desired_summary(
            lowered,
            default="Seeks a compatible partner aligned on values, lifestyle, and relationship goals.",
        )
        return {
            "basic_profile": {
                "age": age,
                "gender_identity": gender_identity,
                "location": None,
                "occupation": None,
                "lifestyle_tags": interests[:3],
            },
            "relationship_intent": {
                "looking_for": relationship,
                "timeline": None,
            },
            "constraints": {
                "age_min": age_min,
                "age_max": age_max,
                "genders": genders,
                "locations": [],
                "max_distance_km": None,
                "relationship_intents": [relationship] if relationship else [],
                "smoking_ok": False if "no_smoking" in explicit else None,
                "drinking_ok": None,
            },
            "dealbreakers": {
                "explicit": explicit,
            },
            "traits_structured": {
                "values": values,
                "interests": interests,
                "personality_traits": personality_traits,
                "desired_partner_traits": desired_traits,
            },
            "self_summary": self_summary,
            "desired_partner_summary": desired_summary,
            "extraction_confidence": 0.45 if age is None else 0.65,
        }

    def embed_text(self, text: str) -> list[float]:
        return _hash_embedding(text)


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)

    def extract_profile(self, transcript: TranscriptInput) -> dict[str, Any]:
        conversation = "\n".join(
            f"{message.role}: {message.content}" for message in transcript.chat_history
        )
        response = self.client.responses.create(
            model=EXTRACTION_MODEL,
            input=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": conversation},
            ],
            text={"format": {"type": "json_object"}},
        )
        return json.loads(response.output_text)

    def embed_text(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        return response.data[0].embedding


def build_provider() -> LLMProvider:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return OpenAIProvider(api_key=api_key)
    return DeterministicFallbackProvider()


def compute_source_hash(transcript: TranscriptInput) -> str:
    payload = "\n".join(f"{m.role}:{m.content}" for m in transcript.chat_history)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _hash_embedding(text: str, dims: int = 24) -> list[float]:
    vocabulary = [
        "kind",
        "kindness",
        "honesty",
        "humor",
        "emotionally",
        "mature",
        "communicative",
        "ambitious",
        "stable",
        "curious",
        "thoughtful",
        "introverted",
        "outgoing",
        "playful",
        "calm",
        "hiking",
        "reading",
        "cooking",
        "music",
        "travel",
        "fitness",
        "art",
        "long-term",
        "casual",
    ]
    lowered = text.lower()
    keyword_features = [1.0 if token in lowered else 0.0 for token in vocabulary]

    digest = hashlib.sha256(text.encode("utf-8")).digest()
    noise = []
    for index in range(max(0, dims - len(keyword_features))):
        byte = digest[index % len(digest)]
        angle = (byte / 255.0) * math.pi * 2
        noise.append(round(math.sin(angle) * 0.05, 6))
    return keyword_features + noise


def _find_first_int_after_keywords(text: str, keywords: list[str]) -> int | None:
    for keyword in keywords:
        idx = text.find(keyword)
        if idx == -1:
            continue
        digits = []
        for ch in text[idx + len(keyword) : idx + len(keyword) + 3]:
            if ch.isdigit():
                digits.append(ch)
            elif digits:
                break
        if digits:
            return int("".join(digits))
    return None


def _find_age_range(text: str) -> tuple[int | None, int | None]:
    for marker in ["between ", "around ", "from "]:
        idx = text.find(marker)
        if idx == -1:
            continue
        tail = text[idx : idx + 30]
        digits = [int(token) for token in tail.replace("-", " ").split() if token.isdigit()]
        if len(digits) >= 2:
            ordered = sorted(digits[:2])
            return ordered[0], ordered[1]
    return None, None


def _short_summary(text: str, default: str) -> str:
    for sentence in text.split("."):
        sentence = sentence.strip()
        if len(sentence) > 30:
            return sentence[:220].strip().capitalize()
    return default


def _desired_summary(text: str, default: str) -> str:
    markers = ["looking for", "want someone", "i want", "my ideal partner"]
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            return text[idx : idx + 220].strip().capitalize()
    return default
