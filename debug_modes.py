import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        # 1. Show raw rows from focus_modes
        rows = (await db.execute(text(
            "SELECT id, user_id, name, is_default FROM focus_modes"
        ))).fetchall()
        print("--- focus_modes rows ---")
        for r in rows:
            print(repr(r))

        # 2. Show schema
        cols = (await db.execute(text("PRAGMA table_info(focus_modes)"))).fetchall()
        print("\n--- focus_modes columns ---")
        for c in cols:
            print(c)

        # 3. Show users.active_focus_mode_id column exists
        ucols = (await db.execute(text("PRAGMA table_info(users)"))).fetchall()
        print("\n--- users columns ---")
        for c in ucols:
            print(c)


asyncio.run(main())