"""
Toxicity classifier wrapper around HuggingFace's `unitary/toxic-bert`.

The model is lazily loaded on first use and cached for subsequent calls.
Multi-label — returns scores for toxic, severe_toxic, obscene, threat, insult, identity_hate.
"""

from functools import lru_cache

from transformers import pipeline

# Thresholds per label. Anything above triggers a hit.
# Tuned conservatively — we prefer false positives we can review over false negatives.
THRESHOLDS = {
    "toxic": 0.75,
    "severe_toxic": 0.55,
    "obscene": 0.75,
    "threat": 0.65,
    "insult": 0.75,
    "identity_hate": 0.65,
}

# Human-readable labels for the moderation reason
LABEL_FRIENDLY = {
    "toxic": "toxic language",
    "severe_toxic": "severe toxicity",
    "obscene": "obscene language",
    "threat": "threatening language",
    "insult": "insulting language",
    "identity_hate": "identity-based hate",
}


@lru_cache(maxsize=1)
def _get_classifier():
    """Load and cache the classifier. Downloads model on first call (~420 MB)."""
    return pipeline(
        "text-classification",
        model="unitary/toxic-bert",
        top_k=None,  # return scores for all labels
        truncation=True,
        max_length=512,
    )


def classify(text: str) -> dict:
    """
    Run toxicity classification on the given text.

    Returns:
        {
            "scores": {"toxic": 0.12, "insult": 0.05, ...},
            "hits": ["toxic", "insult"],       # labels above threshold
            "max_score": 0.85,
            "is_toxic": True,                  # True if any hit
        }
    """
    if not text or not text.strip():
        return {"scores": {}, "hits": [], "max_score": 0.0, "is_toxic": False}

    classifier = _get_classifier()

    # top_k=None returns a list of dicts: [{"label": "...", "score": ...}, ...]
    raw = classifier(text)[0]
    scores = {item["label"].lower(): float(item["score"]) for item in raw}

    hits = [
        label for label, score in scores.items()
        if label in THRESHOLDS and score >= THRESHOLDS[label]
    ]
    max_score = max(scores.values()) if scores else 0.0

    return {
        "scores": scores,
        "hits": hits,
        "max_score": round(max_score, 4),
        "is_toxic": len(hits) > 0,
    }


def describe_hits(hits: list[str]) -> str:
    """Turn a list of label hits into a human-readable phrase."""
    if not hits:
        return ""
    return ", ".join(LABEL_FRIENDLY.get(h, h) for h in hits)
