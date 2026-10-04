from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml import bot_detector
from app.models.bot_signal import BotSignal
from app.models.user import User


class BotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_and_store(self, user_id: str) -> BotSignal:
        user_q = await self.db.execute(select(User).where(User.id == user_id))
        user = user_q.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        result = await bot_detector.evaluate_user(self.db, user)

        existing_q = await self.db.execute(
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
            self.db.add(signal)

        await self.db.commit()
        await self.db.refresh(signal)
        return signal

    async def list_suspicious(self, limit: int = 50) -> list[tuple[BotSignal, User]]:
        """Return suspicious + confirmed accounts, sorted by score desc."""
        stmt = (
            select(BotSignal, User)
            .join(User, User.id == BotSignal.user_id)
            .where(BotSignal.verdict.in_(("suspicious", "confirmed_bot")))
            .order_by(BotSignal.score.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.all())
