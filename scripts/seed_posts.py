import asyncio
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.post import Post
from app.models.user import User

SEED_POSTS = [
    ("giri2", "learning", "Just finished a great tutorial on async Python. The `asyncio.gather` pattern finally clicked."),
    ("giri2", "learning", "Reading 'Designing Data-Intensive Applications' — chapter 3 on storage engines is gold."),
    ("giri2", "technology", "Built my first FastAPI app today. The dependency injection system is elegant."),
    ("giri2", "technology", "SQLAlchemy 2.0's typed ORM is a huge upgrade over 1.4."),
    ("giri2", "art", "Sketching a new poster concept in Procreate. Warm tones this time."),
    ("giri2", "art", "Color theory is basically cheating once you get it."),
    ("giri2", "sports", "Watched an incredible comeback last night. Down 20 in the fourth quarter."),
    ("giri2", "sports", "Training for a 10K. Week 3 is where the real work begins."),
    ("giri2", "entertainment", "Rewatched Blade Runner 2049. The cinematography holds up perfectly."),
    ("giri2", "entertainment", "Started a new sci-fi series. Three episodes in and I'm hooked."),
    ("giri2", "personal", "Two years ago today I decided to learn to code. Best decision I ever made."),
    ("giri2", "personal", "Small win: shipped a feature I'd been procrastinating on for weeks."),
    ("giri2", "social_causes", "Volunteered at a local cleanup this weekend. 40 lbs of trash collected."),
    ("giri2", "social_causes", "If you haven't read about community-supported agriculture, it's worth 10 minutes."),
]


async def main():
    async with AsyncSessionLocal() as db:
        # find the user
        user = (await db.execute(
            select(User).where(User.username == "giri2")
        )).scalar_one_or_none()
        if not user:
            print("User 'giri2' not found. Register first.")
            return

        # skip if posts already exist
        existing = (await db.execute(
            select(Post).where(Post.author_id == user.id).limit(1)
        )).scalar_one_or_none()
        if existing:
            print("Posts already seeded. Skipping.")
            return

        posts = [
            Post(
                author_id=user.id,
                text=text,
                interest_slug=slug,
                media_urls=[],
                moderation_status="approved",
            )
            for username, slug, text in SEED_POSTS
        ]
        db.add_all(posts)
        await db.commit()
        print(f"Seeded {len(posts)} posts for {user.username}")


asyncio.run(main())