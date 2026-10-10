"""
Image NSFW (Not Safe For Work) detector.

Uses HuggingFace's Falconsai/nsfw_image_detection model, which classifies
images as either 'normal' or 'nsfw'.

The model is lazily loaded on first call and cached for subsequent calls.
Downloads ~500 MB on first use.
"""

from functools import lru_cache
from pathlib import Path

from transformers import pipeline


# Confidence threshold above which we trust an 'nsfw' classification
NSFW_CONFIDENCE_THRESHOLD = 0.75


@lru_cache(maxsize=1)
def _get_classifier():
    """Load and cache the NSFW classifier. Downloads on first call (~500 MB)."""
    return pipeline(
        "image-classification",
        model="Falconsai/nsfw_image_detection",
    )


def classify_image(file_path: str | Path) -> dict:
    """
    Classify an image file.

    Args:
        file_path: local path to the image file.

    Returns:
        {
            "is_nsfw": bool,
            "label": "normal" | "nsfw" | "unknown",
            "confidence": float,
            "scores": {"normal": ..., "nsfw": ...},
            "error": None | str,
        }
    """
    path = Path(file_path)
    if not path.exists():
        return {
            "is_nsfw": False,
            "label": "unknown",
            "confidence": 0.0,
            "scores": {},
            "error": f"File not found: {file_path}",
        }

    try:
        classifier = _get_classifier()
        # The pipeline accepts a path or PIL image. Path is simplest.
        results = classifier(str(path))
        # results is a list of dicts like:
        #   [{"label": "nsfw", "score": 0.98}, {"label": "normal", "score": 0.02}]
        scores = {r["label"].lower(): float(r["score"]) for r in results}
    except Exception as e:
        return {
            "is_nsfw": False,
            "label": "unknown",
            "confidence": 0.0,
            "scores": {},
            "error": f"Classification failed: {e}",
        }

    # Pick the highest-scoring label
    if not scores:
        return {
            "is_nsfw": False,
            "label": "unknown",
            "confidence": 0.0,
            "scores": {},
            "error": "Empty classifier output",
        }

    top_label = max(scores, key=scores.get)
    confidence = scores[top_label]

    is_nsfw = top_label == "nsfw" and confidence >= NSFW_CONFIDENCE_THRESHOLD

    return {
        "is_nsfw": is_nsfw,
        "label": top_label,
        "confidence": round(confidence, 3),
        "scores": {k: round(v, 3) for k, v in scores.items()},
        "error": None,
    }
