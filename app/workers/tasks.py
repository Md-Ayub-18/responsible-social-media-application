"""
Celery tasks — run AI moderation, bot detection, and media analysis
outside the request/response cycle so user requests stay fast.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.bot_signal import BotSignal
from app.models.post import Post
from app.models.user import User
from app.workers.celery_app import celery_app


def _run_async(coro):
    """Helper to run async code inside a sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ============================================================
# TEXT MODERATION
# ============================================================

@celery_app.task(name="moderate_post", bind=True, max_retries=2)
def moderate_post(self, post_id: str):
    """Run toxicity + AI-detection on a post's text and update its fields."""
    try:
        _run_async(_moderate_post_async(post_id))
    except Exception as e:
        raise self.retry(exc=e, countdown=5)


async def _moderate_post_async(post_id: str):
    from app.ml.moderation_pipeline import analyze_text

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            return {"status": "not_found", "post_id": post_id}

        verdict = analyze_text(post.text)

        post.moderation_status = verdict["status"]
        post.moderation_reason = verdict["reason"]
        post.ai_generated = verdict["ai_generated"]
        post.ai_label_shown = verdict["ai_generated"]

        await db.commit()
        return {
            "post_id": post_id,
            "status": verdict["status"],
            "reason": verdict["reason"],
        }


# ============================================================
# BOT DETECTION
# ============================================================

@celery_app.task(name="evaluate_bot", bind=True, max_retries=2)
def evaluate_bot(self, user_id: str):
    """Re-evaluate a user's bot score and update their BotSignal row."""
    try:
        _run_async(_evaluate_bot_async(user_id))
    except Exception as e:
        raise self.retry(exc=e, countdown=5)


async def _evaluate_bot_async(user_id: str):
    from app.ml import bot_detector

    async with AsyncSessionLocal() as db:
        user_q = await db.execute(select(User).where(User.id == user_id))
        user = user_q.scalar_one_or_none()
        if not user:
            return {"status": "not_found", "user_id": user_id}

        result = await bot_detector.evaluate_user(db, user)

        existing_q = await db.execute(
            select(BotSignal).where(BotSignal.user_id == user_id)
        )
        signal = existing_q.scalar_one_or_none()

        if signal:
            signal.score = result["score"]
            signal.verdict = result["verdict"]
            signal.reasons = result["reasons"]
            signal.details = result["details"]
            signal.last_evaluated_at = datetime.now(timezone.utc)
        else:
            signal = BotSignal(
                user_id=user_id,
                score=result["score"],
                verdict=result["verdict"],
                reasons=result["reasons"],
                details=result["details"],
                last_evaluated_at=datetime.now(timezone.utc),
            )
            db.add(signal)

        await db.commit()
        return {"user_id": user_id, "score": result["score"], "verdict": result["verdict"]}


# ============================================================
# MEDIA MODERATION (NSFW + AI-image detection)
# ============================================================

@celery_app.task(name="moderate_post_media", bind=True, max_retries=2)
def moderate_post_media(self, post_id: str):
    """Analyze images on a post for NSFW content and AI-generation signals."""
    try:
        _run_async(_moderate_post_media_async(post_id))
    except Exception as e:
        raise self.retry(exc=e, countdown=5)


async def _moderate_post_media_async(post_id: str):
    from app.config import settings
    from app.ml.ai_image_detector import classify_image as detect_ai_image
    from app.ml.ai_image_detector import describe_verdict as describe_ai_verdict
    from app.ml.nsfw_detector import classify_image as detect_nsfw

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            return {"status": "not_found", "post_id": post_id}

        media_urls = post.media_urls or []
        image_urls = [
            u for u in media_urls
            if u.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))
        ]

        if not image_urls:
            post.media_moderation_status = "approved"
            post.media_moderation_reason = None
            await db.commit()
            return {"post_id": post_id, "status": "approved", "reason": "no_images"}

        worst_nsfw = "approved"
        nsfw_reasons: list[str] = []
        ai_image_reasons: list[str] = []
        ai_image_hit = False

        for url in image_urls:
            filename = url.rsplit("/", 1)[-1]

            if "/media/posts/" in url:
                file_path = Path(settings.MEDIA_POSTS_DIR) / filename
            elif "/media/uploads/" in url:
                file_path = Path(settings.MEDIA_UPLOADS_DIR) / filename
            else:
                continue

            nsfw_verdict = detect_nsfw(file_path)
            if nsfw_verdict["is_nsfw"]:
                worst_nsfw = "flagged"
                nsfw_reasons.append(
                    f"NSFW: {filename} (confidence {nsfw_verdict['confidence']})"
                )

            ai_verdict = detect_ai_image(file_path)
            if ai_verdict["is_ai"]:
                ai_image_hit = True
                reason = describe_ai_verdict(ai_verdict)
                if reason:
                    ai_image_reasons.append(reason)

        if worst_nsfw == "flagged":
            post.media_moderation_status = "flagged"
            post.media_moderation_reason = " | ".join(nsfw_reasons)[:500]
        else:
            post.media_moderation_status = "approved"
            post.media_moderation_reason = None

        if ai_image_hit:
            post.ai_generated = True
            post.ai_label_shown = True
            if not post.media_moderation_reason:
                post.media_moderation_reason = " | ".join(ai_image_reasons)[:500]

        await db.commit()

        return {
            "post_id": post_id,
            "media_status": post.media_moderation_status,
            "ai_generated": post.ai_generated,
            "nsfw_reasons": nsfw_reasons,
            "ai_reasons": ai_image_reasons,
        }
