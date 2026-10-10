"""
Celery tasks — run AI moderation, bot detection, and duration probing
outside the request/response cycle so user requests stay fast.
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from pathlib import Path
from app.db.session import AsyncSessionLocal
from app.models.bot_signal import BotSignal
from app.models.post import Post
from app.models.user import User
from app.workers.celery_app import celery_app


def _run_async(coro):
    """Helper to run async code inside a sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="moderate_post_media", bind=True, max_retries=2)
def moderate_post_media(self, post_id: str):
    """Analyze any image media on a post for NSFW content."""
    try:
        _run_async(_moderate_post_media_async(post_id))
    except Exception as e:
        raise self.retry(exc=e, countdown=5)


async def _moderate_post_media_async(post_id: str):
    from app.ml.nsfw_detector import classify_image
    from app.models.post import Post

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
            # No images to check — approve immediately
            post.media_moderation_status = "approved"
            post.media_moderation_reason = None
            await db.commit()
            return {"post_id": post_id, "status": "approved", "reason": "no_images"}

        # Analyze each image (usually 1)
        worst_case = None  # "approved" | "flagged"
        reasons = []

        for url in image_urls:
            # url looks like "/media/posts/abc123.png" → resolve to local file
            filename = url.rsplit("/", 1)[-1]

            # Determine folder from the URL
            if "/media/posts/" in url:
                from app.config import settings
                file_path = Path(settings.MEDIA_POSTS_DIR) / filename
            elif "/media/uploads/" in url:
                from app.config import settings
                file_path = Path(settings.MEDIA_UPLOADS_DIR) / filename
            else:
                continue

            verdict = classify_image(file_path)
            if verdict["is_nsfw"]:
                worst_case = "flagged"
                reasons.append(
                    f"Image {filename}: NSFW detected (confidence {verdict['confidence']})"
                )

        if worst_case == "flagged":
            post.media_moderation_status = "flagged"
            post.media_moderation_reason = " | ".join(reasons)[:500]
        else:
            post.media_moderation_status = "approved"
            post.media_moderation_reason = None

        await db.commit()

        return {
            "post_id": post_id,
            "status": post.media_moderation_status,
            "reason": post.media_moderation_reason,
        }


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
