"""
Heuristic bot / fake-account detector.

Each check contributes a weighted score (0–1). If the total crosses
SUSPICIOUS_THRESHOLD, the account is added to the moderation review list.

Deliberately rule-based: real platforms start here, because heuristics are
explainable and don't require labeled training data. The output interface
(score + reasons) is designed so an ML model could replace this later
without changing any downstream code.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.user import User


SUSPICIOUS_THRESHOLD = 0.60
CONFIRMED_THRESHOLD = 0.85


# ---------- individual signals ----------

def _signal_account_age(user: User) -> tuple[float, str | None]:
    if not user.created_at:
        return 0.0, None
    age_hours = (datetime.now(timezone.utc) - user.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
    if age_hours < 1:
        return 0.35, f"Account is less than 1 hour old"
    if age_hours < 24:
        return 0.20, f"Account is less than 24 hours old"
    return 0.0, None


def _signal_post_velocity(recent_posts: int) -> tuple[float, str | None]:
    if recent_posts >= 30:
        return 0.40, f"{recent_posts} posts in the last hour"
    if recent_posts >= 10:
        return 0.25, f"{recent_posts} posts in the last hour"
    if recent_posts >= 5:
        return 0.10, f"{recent_posts} posts in the last hour"
    return 0.0, None


def _signal_duplicate_text(posts_text: list[str]) -> tuple[float, str | None]:
    if len(posts_text) < 3:
        return 0.0, None
    counts = Counter(posts_text)
    dup_ratio = sum(c - 1 for c in counts.values() if c > 1) / len(posts_text)
    if dup_ratio >= 0.5:
        return 0.35, f"{int(dup_ratio * 100)}% duplicate content"
    if dup_ratio >= 0.2:
        return 0.15, f"{int(dup_ratio * 100)}% duplicate content"
    return 0.0, None


def _signal_username_pattern(user: User) -> tuple[float, str | None]:
    import re
    u = user.username
    if re.match(r"^user\d{4,}$", u):
        return 0.15, "Username follows default generator pattern"
    if re.search(r"\d{5,}$", u):
        return 0.10, "Username ends with long digit sequence"
    return 0.0, None


def _signal_profile_incomplete(user: User) -> tuple[float, str | None]:
    if not user.display_name or user.display_name == user.username:
        return 0.10, "Profile display name not set"
    return 0.0, None


# ---------- orchestrator ----------

async def evaluate_user(db: AsyncSession, user: User) -> dict:
    """Compute bot score for one user."""
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    # recent posts in the last hour
    recent_q = await db.execute(
        select(Post).where(Post.author_id == user.id).where(Post.created_at >= one_hour_ago)
    )
    recent_posts = list(recent_q.scalars().all())

    # all their posts (cap for perf)
    all_q = await db.execute(
        select(Post.text).where(Post.author_id == user.id).limit(200)
    )
    all_texts = list(all_q.scalars().all())

    signals = [
        _signal_account_age(user),
        _signal_post_velocity(len(recent_posts)),
        _signal_duplicate_text(all_texts),
        _signal_username_pattern(user),
        _signal_profile_incomplete(user),
    ]

    score = min(sum(s for s, _ in signals), 1.0)
    reasons = [r for _, r in signals if r]

    if score >= CONFIRMED_THRESHOLD:
        verdict = "confirmed_bot"
    elif score >= SUSPICIOUS_THRESHOLD:
        verdict = "suspicious"
    else:
        verdict = "clean"

    return {
        "user_id": user.id,
        "score": round(score, 3),
        "reasons": reasons,
        "verdict": verdict,
        "details": {
            "recent_posts_last_hour": len(recent_posts),
            "total_posts_sampled": len(all_texts),
        },
    }