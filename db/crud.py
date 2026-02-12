from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User

async def add_user(session: AsyncSession, telegram_id: int, full_name: str, username: str = None):
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    is_new = False
    if not user:
        user = User(telegram_id=telegram_id, full_name=full_name, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        is_new = True
    return user, is_new



async def get_user(session: AsyncSession, telegram_id: int):
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_user_region(session: AsyncSession, telegram_id: int, region: str):
    stmt = update(User).where(User.telegram_id == telegram_id).values(region=region)
    await session.execute(stmt)
    await session.commit()

async def get_all_users(session: AsyncSession):
    stmt = select(User)
    result = await session.execute(stmt)
    return result.scalars().all()

