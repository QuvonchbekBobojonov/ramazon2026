import asyncio
from db.base import async_session_maker
from sqlalchemy import func, select
from db.models import User

async def check():
    async with async_session_maker() as session:
        result = await session.execute(select(func.count(User.id)))
        count = result.scalar()
        print(f"BAZADAGI JAMI FOYDALANUVCHILAR: {count}")
        
        # Check blocked vs active if column exists
        try:
            active_res = await session.execute(select(func.count(User.id)).where(User.is_blocked == False))
            print(f"FAOL: {active_res.scalar()}")
            blocked_res = await session.execute(select(func.count(User.id)).where(User.is_blocked == True))
            print(f"BLOKLANGAN: {blocked_res.scalar()}")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(check())
