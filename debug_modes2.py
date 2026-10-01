import asyncio
from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal
from app.models.focus_mode import FocusMode


async def main():
    async with AsyncSessionLocal() as db:
        print("=== RAW ROWS ===")
        rows = (await db.execute(text(
            "SELECT id, user_id, name FROM focus_modes"
        ))).fetchall()
        for r in rows:
            print(f"  id={r[0]!r}")
            print(f"  user_id={r[1]!r}")
            print(f"  name={r[2]!r}")
            print()

        print("=== ORM QUERY WITHOUT FILTER ===")
        all_modes = (await db.execute(select(FocusMode))).scalars().all()
        for m in all_modes:
            print(f"  ORM: id={m.id!r} user_id={m.user_id!r} name={m.name!r}")

        print("\n=== ORM QUERY WITH FILTER ===")
        study_id = "71a9a831-643e-455f-9a15-d2277df48600"
        user_id = "06292ab1-f93d-48b8-a4c5-8cc96b0a99b2"
        result = await db.execute(
            select(FocusMode).where(FocusMode.id == study_id)
        )
        m = result.scalar_one_or_none()
        print(f"  With id filter only: {m}")
        print(f"  Stored user_id: {m.user_id if m else 'N/A'!r}")
        print(f"  Requested user_id: {user_id!r}")
        print(f"  Match: {m.user_id == user_id if m else 'N/A'}")


asyncio.run(main())