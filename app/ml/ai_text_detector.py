"""
AI-generated text detector.

Two signals:
1. HF model: `openai-community/roberta-base-openai-detector` — trained on GPT-2 outputs.
2. Heuristics: LLM-typical markers (specific phrases).

Combined into a single confidence score with conservative thresholds to
avoid false positives on normal writing.
"""

import logging
import re
from functools import lru_cache

from transformers import pipeline

# Silence the "Some weights were not used" HuggingFace warning on every load.
logging.getLogger("transformers").setLevel(logging.ERROR)


# Strong signals — phrases that appear in AI writing but rarely in human writing.
LLM_MARKERS = [
    r"\bas an ai\b",
    r"\bit('s| is) important to note\b",
    r"\bdelve into\b",
    r"\bnavigate the complexities\b",
    r"\bin today('s| is) fast-paced world\b",
    r"\bunlock the potential\b",
    r"\btapestry\b",
    r"\bmultifaceted\b",
    r"\brich tapestry\b",
    r"\belevate your\b",
    r"\bembark on a journey\b",
]

MODEL_THRESHOLD = 0.95      # HF model must be very confident to be trusted alone
STRONG_MODEL_THRESHOLD = 0.98
HEURISTIC_THRESHOLD = 2     # distinct markers required


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
        variance = sum((n - mean) ** 2 for n in lengths) / len(lengths)
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
            "model_label": str,         # "Real" or "Fake"
            "model_score": float,
            "heuristics": {...},
            "reasons": [str, ...],
        }
    """
    # Too short for meaningful analysis
    if not text or len(text.strip()) < 40:
        return {
            "is_ai": False,
            "confidence": 0.0,
            "model_label": "unknown",
            "model_score": 0.0,
            "heuristics": {},
            "reasons": [],
        }

    # --- Model signal ---
    detector = _get_detector()
    result = detector(text)[0]
    model_label = result["label"]
    model_score = float(result["score"])

    # --- Heuristic signal ---
    heur = _heuristic_signals(text)

    # --- Decision logic ---
        # --- Decision logic ---
    reasons: list[str] = []

    marker_count = heur["marker_count"]

    model_says_ai = (
        model_label.lower() in ("fake", "ai", "generated")
        and model_score >= MODEL_THRESHOLD
    )
    strong_model_says_ai = (
        model_label.lower() in ("fake", "ai", "generated")
        and model_score >= STRONG_MODEL_THRESHOLD
    )
    heuristic_strong = marker_count >= 3
    heuristic_moderate = marker_count >= 2

    # Flag as AI if:
    #   (a) 3+ strong heuristic markers alone, OR
    #   (b) 2+ heuristic markers AND model agrees, OR
    #   (c) model is extremely confident (>= 0.98) alone
    is_ai = (
        heuristic_strong
        or (heuristic_moderate and model_says_ai)
        or strong_model_says_ai
    )

    # Build human-readable reasons
    if heuristic_strong:
        reasons.append(f"Multiple LLM-typical phrases detected ({marker_count})")
    elif heuristic_moderate and model_says_ai:
        reasons.append(
            f"LLM-typical phrases ({marker_count}) and AI-detector confidence {model_score:.2f}"
        )
    if strong_model_says_ai and not heuristic_moderate:
        reasons.append(f"AI-detector model confidence {model_score:.2f}")

    # Confidence score
    if heuristic_strong:
        confidence = min(0.6 + marker_count * 0.08, 0.95)
    elif strong_model_says_ai:
        confidence = model_score
    elif is_ai:
        confidence = max(model_score, 0.6)
    else:
        confidence = 0.0
    confidence = round(min(confidence, 1.0), 3)

    return {
        "is_ai": is_ai,
        "confidence": confidence,
        "model_label": model_label,
        "model_score": round(model_score, 3),
        "heuristics": heur,
        "reasons": reasons,
    }
