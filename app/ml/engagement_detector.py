"""
Manipulated engagement detector.

Analyzes the pattern of likes on a single post to detect:
  - Velocity attacks (mass likes in a short window)
  - Fake account farms (many new accounts liking the same post)
  - Incomplete profiles (no display name → likely throwaway)
  - Synchronized timing (likes 5+ within 2 seconds)
  - Suspicious source networks (same accounts boosting many posts)

Returns a 0–1 manipulation score with human-readable reasons.

No ML — this is a signal-based detector. The signals are explainable and
match what real platforms use in their first-pass anti-manipulation filters.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.reaction import Reaction
from app.models.user import User


# ---------- thresholds ----------
VELOCITY_WINDOW_SECONDS = 60
VELOCITY_CRITICAL = 20        # ≥ this many likes in window → high signal
VELOCITY_WARNING = 10         # ≥ this many → moderate

SYNC_WINDOW_SECONDS = 2
SYNC_CRITICAL = 5             # 5+ likes in a 2-second window

NEW_ACCOUNT_HOURS = 24
NEW_ACCOUNT_RATIO_CRITICAL = 0.7
NEW_ACCOUNT_RATIO_WARNING = 0.4

INCOMPLETE_PROFILE_RATIO_CRITICAL = 0.6
INCOMPLETE_PROFILE_RATIO_WARNING = 0.3

# Overall verdict thresholds
SUSPICIOUS_THRESHOLD = 0.5
MANIPULATED_THRESHOLD = 0.75


async def evaluate_post(db: AsyncSession, post: Post) -> dict:
    """
    Analyze a post's engagement pattern.

    Returns:
        {
            "post_id": str,
            "score": float,         # 0.0 – 1.0
            "verdict": str,         # clean | suspicious | manipulated
            "reasons": list[str],
            "details": dict,
        }
    """

    # Load all likes for this post
    likes_q = await db.execute(
        select(Reaction).where(
            Reaction.post_id == post.id,
            Reaction.kind == "like",
        ).order_by(Reaction.created_at.asc())
    )
    likes = list(likes_q.scalars().all())

    total_likes = len(likes)

    # Not enough data to judge
    if total_likes < 5:
        return {
            "post_id": post.id,
            "score": 0.0,
            "verdict": "clean",
            "reasons": [],
            "details": {"total_likes": total_likes, "reason": "too_few_likes"},
        }

    # Load liker users
    liker_ids = [lk.user_id for lk in likes]
    users_q = await db.execute(
        select(User).where(User.id.in_(liker_ids))
    )
    users = {u.id: u for u in users_q.scalars().all()}

    score = 0.0
    reasons: list[str] = []
    details: dict = {"total_likes": total_likes}

    # ---------- Signal 1: Velocity ----------
    velocity_hit, velocity_detail = _velocity_signal(likes)
    if velocity_hit:
        score += velocity_detail["weight"]
        reasons.append(velocity_detail["reason"])
        details["velocity"] = velocity_detail

    # ---------- Signal 2: Synchronized timing ----------
    sync_hit, sync_detail = _sync_signal(likes)
    if sync_hit:
        score += sync_detail["weight"]
        reasons.append(sync_detail["reason"])
        details["sync"] = sync_detail

    # ---------- Signal 3: New accounts ----------
    new_hit, new_detail = _new_accounts_signal(likes, users)
    if new_hit:
        score += new_detail["weight"]
        reasons.append(new_detail["reason"])
        details["new_accounts"] = new_detail

    # ---------- Signal 4: Incomplete profiles ----------
    incomp_hit, incomp_detail = _incomplete_profiles_signal(users, liker_ids)
    if incomp_hit:
        score += incomp_detail["weight"]
        reasons.append(incomp_detail["reason"])
        details["incomplete_profiles"] = incomp_detail

    # ---------- Signal 5: Same-account boosting ----------
    # Only computed if post is in a list context; skipped here for single-post analysis.
    # (In a batch scan, we can compare across posts.)

    score = min(score, 1.0)

    if score >= MANIPULATED_THRESHOLD:
        verdict = "manipulated"
    elif score >= SUSPICIOUS_THRESHOLD:
        verdict = "suspicious"
    else:
        verdict = "clean"

    return {
        "post_id": post.id,
        "score": round(score, 3),
        "verdict": verdict,
        "reasons": reasons,
        "details": details,
    }


# ============================================================
# Individual signals
# ============================================================

def _velocity_signal(likes: list[Reaction]) -> tuple[bool, dict]:
    """
    Count the max number of likes within any sliding window of
    VELOCITY_WINDOW_SECONDS seconds.
    """
    if len(likes) < VELOCITY_WARNING:
        return False, {}

    times = sorted(lk.created_at for lk in likes)
    max_in_window = 0
    window_start_idx = 0

    for i, t in enumerate(times):
        cutoff = t - timedelta(seconds=VELOCITY_WINDOW_SECONDS)
        while times[window_start_idx] < cutoff:
            window_start_idx += 1
        window_count = i - window_start_idx + 1
        if window_count > max_in_window:
            max_in_window = window_count

    if max_in_window >= VELOCITY_CRITICAL:
        return True, {
            "weight": 0.4,
            "count": max_in_window,
            "window_seconds": VELOCITY_WINDOW_SECONDS,
            "reason": f"{max_in_window} likes in {VELOCITY_WINDOW_SECONDS}s window",
        }
    if max_in_window >= VELOCITY_WARNING:
        return True, {
            "weight": 0.2,
            "count": max_in_window,
            "window_seconds": VELOCITY_WINDOW_SECONDS,
            "reason": f"{max_in_window} likes in {VELOCITY_WINDOW_SECONDS}s window",
        }
    return False, {}


def _sync_signal(likes: list[Reaction]) -> tuple[bool, dict]:
    """
    Count the max number of likes in any sliding SYNC_WINDOW_SECONDS-second window.
    A tight cluster suggests scripted interactions.
    """
    if len(likes) < SYNC_CRITICAL:
        return False, {}

    times = sorted(lk.created_at for lk in likes)
    max_in_window = 0
    window_start_idx = 0

    for i, t in enumerate(times):
        cutoff = t - timedelta(seconds=SYNC_WINDOW_SECONDS)
        while times[window_start_idx] < cutoff:
            window_start_idx += 1
        window_count = i - window_start_idx + 1
        if window_count > max_in_window:
            max_in_window = window_count

    if max_in_window >= SYNC_CRITICAL:
        return True, {
            "weight": 0.35,
            "count": max_in_window,
            "window_seconds": SYNC_WINDOW_SECONDS,
            "reason": f"{max_in_window} likes within {SYNC_WINDOW_SECONDS}s",
        }
    return False, {}


def _new_accounts_signal(
    likes: list[Reaction], users: dict[str, User]
) -> tuple[bool, dict]:
    """
    Percentage of likers whose account is younger than NEW_ACCOUNT_HOURS.
    """
    if not users:
        return False, {}

    cutoff = datetime.now(timezone.utc) - timedelta(hours=NEW_ACCOUNT_HOURS)
    total = len(likes)
    new_count = 0

    for like in likes:
        u = users.get(like.user_id)
        if not u:
            continue
        if u.created_at and u.created_at >= cutoff:
            new_count += 1

    ratio = new_count / total if total else 0.0

    if ratio >= NEW_ACCOUNT_RATIO_CRITICAL:
        return True, {
            "weight": 0.4,
            "new_ratio": round(ratio, 3),
            "new_count": new_count,
            "total": total,
            "reason": f"{int(ratio * 100)}% of likers are new accounts (<{NEW_ACCOUNT_HOURS}h old)",
        }
    if ratio >= NEW_ACCOUNT_RATIO_WARNING:
        return True, {
            "weight": 0.2,
            "new_ratio": round(ratio, 3),
            "new_count": new_count,
            "total": total,
            "reason": f"{int(ratio * 100)}% of likers are new accounts",
        }
    return False, {}


def _incomplete_profiles_signal(
    users: dict[str, User], liker_ids: list[str]
) -> tuple[bool, dict]:
    """
    Percentage of likers with no display_name set (or equal to username).
    """
    if not users:
        return False, {}

    total = len(liker_ids)
    incomplete = 0
    for uid in liker_ids:
        u = users.get(uid)
        if not u:
            continue
        if not u.display_name or u.display_name == u.username:
            incomplete += 1

    ratio = incomplete / total if total else 0.0

    if ratio >= INCOMPLETE_PROFILE_RATIO_CRITICAL:
        return True, {
            "weight": 0.3,
            "incomplete_ratio": round(ratio, 3),
            "incomplete": incomplete,
            "total": total,
            "reason": f"{int(ratio * 100)}% of likers have incomplete profiles",
        }
    if ratio >= INCOMPLETE_PROFILE_RATIO_WARNING:
        return True, {
            "weight": 0.15,
            "incomplete_ratio": round(ratio, 3),
            "incomplete": incomplete,
            "total": total,
            "reason": f"{int(ratio * 100)}% of likers have incomplete profiles",
        }
    return False, {}
