"""
AI-generated text detector.

Two signals:
1. HF model: `openai-community/roberta-base-openai-detector` — trained on GPT-2 outputs.
2. Heuristics: LLM-typical markers (uniform sentence length, specific phrases, low burstiness).

Combined into a single confidence score.
"""

import re
from functools import lru_cache

from transformers import pipeline


# Common LLM stock phrases — weak signal each, but together they add up
LLM_MARKERS = [
    r"\bas an ai\b",
    r"\bit('s| is) important to note\b",
    r"\bin conclusion\b",
    r"\bfurthermore,?\b",
    r"\bmoreover,?\b",
    r"\bhowever,? it('s| is) worth\b",
    r"\bdelve into\b",
    r"\bnavigate the complexities\b",
    r"\bin today('s| is) fast-paced world\b",
    r"\bunlock the potential\b",
    r"\btapestry\b",
    r"\bmultifaceted\b",
]

MODEL_THRESHOLD = 0.85   # HF model confidence required
HEURISTIC_THRESHOLD = 3  # number of distinct markers required


@lru_cache(maxsize=1)
def _get_detector():
    """Load and cache the AI-text detector. Downloads on first call (~500 MB)."""
    return pipeline(
        "text-classification",
        model="openai-community/roberta-base-openai-detector",
        truncation=True,
        max_length=512,
    )


def _heuristic_signals(text: str) -> dict:
    """Non-ML signals for AI-generated text."""
    lower = text.lower()

    markers_found = [pat for pat in LLM_MARKERS if re.search(pat, lower, re.IGNORECASE)]

    # Sentence length uniformity (LLMs tend to produce uniform-length sentences)
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    lengths = [len(s.split()) for s in sentences]
    length_variance = 0.0
    if len(lengths) >= 4:
        mean = sum(lengths) / len(lengths)
        variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
        length_variance = variance

    return {
        "marker_count": len(markers_found),
        "markers": markers_found,
        "length_variance": round(length_variance, 2),
        "sentences": len(sentences),
    }


def detect(text: str) -> dict:
    """
    Detect whether text is likely AI-generated.

    Returns:
        {
            "is_ai": bool,
            "confidence": float,        # 0-1
            "model_label": str,         # "Real" or "Fake" (HF model output)
            "model_score": float,
            "heuristics": {...},
            "reasons": [str, ...],      # human-readable reasons
        }
    """
    if not text or len(text.strip()) < 40:
        # Too short for meaningful analysis
        return {
            "is_ai": False, "confidence": 0.0,
            "model_label": "unknown", "model_score": 0.0,
            "heuristics": {}, "reasons": [],
        }

    # Model signal
    detector = _get_detector()
    result = detector(text)[0]
    model_label = result["label"]       # typically "Real" or "Fake"
    model_score = float(result["score"])

    # Heuristic signal
    heur = _heuristic_signals(text)

    # Decide
    reasons = []
    model_says_ai = model_label.lower() in ("fake", "ai", "generated") and model_score >= MODEL_THRESHOLD
    if model_says_ai:
        reasons.append(f"AI-detector model confidence {model_score:.2f}")

    heuristic_says_ai = heur["marker_count"] >= HEURISTIC_THRESHOLD
    if heuristic_says_ai:
        reasons.append(f"LLM-typical phrases detected ({heur['marker_count']})")

    is_ai = model_says_ai or heuristic_says_ai
    confidence = model_score if model_says_ai else (0.5 + heur["marker_count"] * 0.1 if heuristic_says_ai else 0.0)
    confidence = min(confidence, 1.0)

    return {
        "is_ai": is_ai,
        "confidence": round(confidence, 3),
        "model_label": model_label,
        "model_score": round(model_score, 3),
        "heuristics": heur,
        "reasons": reasons,
    }