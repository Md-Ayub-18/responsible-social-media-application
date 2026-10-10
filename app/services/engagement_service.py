from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.engagement_detector import evaluate_post
from app.models.engagement_signal import EngagementSignal
from app.models.post import Post


class EngagementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_and_store(self, post_id: str) -> EngagementSignal:
        """Run analysis on a post and upsert its EngagementSignal row."""
        post_q = await self.db.execute(select(Post).where(Post.id == post_id))
        post = post_q.scalar_one_or_none()
        if not post:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

        result = await evaluate_post(self.db, post)

        existing_q = await self.db.execute(
            select(EngagementSignal).where(EngagementSignal.post_id == post_id)
        )
        signal = existing_q.scalar_one_or_none()

        if signal:
            signal.score = result["score"]
            signal.verdict = result["verdict"]
            signal.reasons = result["reasons"]
            signal.details = result["details"]
        else:
            signal = EngagementSignal(
                post_id=post_id,
                score=result["score"],
                verdict=result["verdict"],
                reasons=result["reasons"],
                details=result["details"],
            )
            self.db.add(signal)

        await self.db.commit()
        await self.db.refresh(signal)
        return signal

    async def list_suspicious(self, limit: int = 50) -> list[tuple[EngagementSignal, Post]]:
        """Return signals with suspicious or manipulated verdicts."""
        stmt = (
            select(EngagementSignal, Post)
            .join(Post, Post.id == EngagementSignal.post_id)
            .where(EngagementSignal.verdict.in_(("suspicious", "manipulated")))
            .order_by(EngagementSignal.score.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.all())

    async def scan_recent_posts(self, limit: int = 50) -> int:
        """
        Scan the N most recent posts with at least 5 likes.
        Used by a periodic Celery task.
        """
        from sqlalchemy import func
        from app.models.reaction import Reaction

        # Find posts with >=5 likes
        stmt = (
            select(Post.id, func.count(Reaction.id).label("like_count"))
            .join(Reaction, Reaction.post_id == Post.id)
            .where(Reaction.kind == "like")
            .group_by(Post.id)
            .having(func.count(Reaction.id) >= 5)
            .order_by(Post.created_at.desc())
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).all()

        count = 0
        for post_id, _ in rows:
            try:
                await self.evaluate_and_store(post_id)
                count += 1
            except Exception:
                continue
        return count
