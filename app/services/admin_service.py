from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bot_signal import BotSignal
from app.models.moderation_log import ModerationLog
from app.models.post import Post
from app.models.report import Report
from app.models.stitch_project import Contribution, StitchProject
from app.models.user import User


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def dashboard(self) -> dict:
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(hours=24)

        async def count(model, *conditions) -> int:
            stmt = select(func.count()).select_from(model)
            for c in conditions:
                stmt = stmt.where(c)
            return (await self.db.execute(stmt)).scalar_one()

        pending_reports = await count(Report, Report.status == "open")
        flagged_posts = await count(Post, Post.moderation_status == "flagged")
        removed_posts = await count(Post, Post.moderation_status == "removed")
        suspicious_accounts = await count(
            BotSignal, BotSignal.verdict.in_(("suspicious", "confirmed_bot"))
        )
        pending_contributions = await count(
            Contribution, Contribution.status == "pending"
        )
        open_stitch_projects = await count(
            StitchProject, StitchProject.status.in_(("open", "in_review"))
        )
        total_users = await count(User)
        total_posts = await count(Post)

        # activity last 24h
        posts_24h = await count(Post, Post.created_at >= day_ago)
        reports_24h = await count(Report, Report.created_at >= day_ago)

        # last 10 moderation actions
        recent_logs = (await self.db.execute(
            select(ModerationLog)
            .order_by(ModerationLog.created_at.desc())
            .limit(10)
        )).scalars().all()

        return {
            "counts": {
                "pending_reports": pending_reports,
                "flagged_posts": flagged_posts,
                "removed_posts": removed_posts,
                "suspicious_accounts": suspicious_accounts,
                "pending_contributions": pending_contributions,
                "open_stitch_projects": open_stitch_projects,
                "total_users": total_users,
                "total_posts": total_posts,
            },
            "activity_24h": {
                "posts": posts_24h,
                "reports": reports_24h,
            },
            "recent_actions": [
                {
                    "action": log.action,
                    "actor": log.actor_username,
                    "target": f"{log.target_type}:{log.target_id}",
                    "reason": log.reason,
                    "at": log.created_at.isoformat(),
                }
                for log in recent_logs
            ],
            "generated_at": now.isoformat(),
        }
