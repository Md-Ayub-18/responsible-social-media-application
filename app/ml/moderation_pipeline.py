"""
Combines toxicity + AI-detection + spam signals into a single moderation decision.

Decision output feeds directly into the Post.moderation_status field.
"""

import re

from app.ml import ai_text_detector, toxicity


# Decision values match the Post model's moderation_status column
STATUS_APPROVED = "approved"
STATUS_FLAGGED = "flagged"
STATUS_REMOVED = "removed"


# Simple promotional patterns — cheap heuristic, catches obvious spam.
SPAM_PATTERNS = [
    r"\bbuy now\b",
    r"\bclick (the |this )?link\b",
    r"\blimited time\b",
    r"\bspecial offer\b",
    r"\b(100|99)% (free|guaranteed)\b",
    r"\bmake \$?\d+ (a|per) (day|hour)\b",
    r"\bact now\b",
    r"\bdon'?t miss out\b",
    r"\blink in (my |the )?bio\b",
]


def _spam_signal(text: str) -> tuple[float, list[str]]:
    """Return (score, reasons). Score 0.0–1.0."""
    hits = [p for p in SPAM_PATTERNS if re.search(p, text, re.IGNORECASE)]
    if len(hits) >= 2:
        return 0.8, ["spam-like promotional language"]
    if len(hits) == 1:
        return 0.4, ["possible promotional content"]
    return 0.0, []


def analyze_text(text: str) -> dict:
    """
    Run the full moderation pipeline on a piece of text.

    Returns:
        {
            "status": "approved" | "flagged" | "removed",
            "reason": str | None,
            "ai_generated": bool,
            "signals": {
                "toxicity": {...},
                "ai_detection": {...},
                "spam": {...},
            },
        }
    """
    tox = toxicity.classify(text)
    ai = ai_text_detector.detect(text)
    spam_score, spam_reasons = _spam_signal(text)

    reasons: list[str] = []
    status = STATUS_APPROVED

    # --- toxicity decision ---
    if tox["is_toxic"]:
        hits_desc = toxicity.describe_hits(tox["hits"])
        if "severe_toxic" in tox["hits"] or "threat" in tox["hits"]:
            status = STATUS_REMOVED
            reasons.append(f"Auto-removed: {hits_desc} (score {tox['max_score']})")
        else:
            status = STATUS_FLAGGED
            reasons.append(f"Flagged for review: {hits_desc} (score {tox['max_score']})")

    # --- spam decision ---
    if spam_score >= 0.7:
        if status == STATUS_APPROVED:
            status = STATUS_FLAGGED
        reasons.append(
            f"Spam flagged: {', '.join(spam_reasons)} (score {spam_score})"
        )
    elif spam_score >= 0.4 and status == STATUS_APPROVED:
        # borderline — flag only if nothing else has
        status = STATUS_FLAGGED
        reasons.append(
            f"Spam flagged: {', '.join(spam_reasons)} (score {spam_score})"
        )

    # --- AI-generated decision ---
    if ai["is_ai"]:
        if status == STATUS_APPROVED:
            status = STATUS_FLAGGED
        reasons.append(f"Possible AI-generated: {'; '.join(ai['reasons'])}")

    reason_str = " | ".join(reasons) if reasons else None

    return {
        "status": status,
        "reason": reason_str,
        "ai_generated": ai["is_ai"],
        "signals": {
            "toxicity": tox,
            "ai_detection": ai,
            "spam": {"score": spam_score, "reasons": spam_reasons},
        },
    }