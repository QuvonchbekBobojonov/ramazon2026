from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, Prayer
from utils.cache import delete_cache

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
    await delete_cache(f"user:{telegram_id}")

async def update_user_subscription(session: AsyncSession, telegram_id: int, is_subscribed: bool):
    stmt = update(User).where(User.telegram_id == telegram_id).values(is_subscribed=is_subscribed)
    await session.execute(stmt)
    await session.commit()
    await delete_cache(f"user:{telegram_id}")

async def update_user_blocked(session: AsyncSession, telegram_id: int, is_blocked: bool):
    stmt = update(User).where(User.telegram_id == telegram_id).values(is_blocked=is_blocked)
    await session.execute(stmt)
    await session.commit()
    await delete_cache(f"user:{telegram_id}")

async def get_all_users(session: AsyncSession):
    stmt = select(User)
    result = await session.execute(stmt)
    return result.scalars().all()

async def add_prayer(session: AsyncSession, user_id: int, author_name: str, content: str, is_anonymous: bool):
    # Check for duplicate content from the same user
    stmt = select(Prayer).where(Prayer.user_id == user_id, Prayer.content == content)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        return None # Duplicate
        
    prayer = Prayer(user_id=user_id, author_name=author_name, content=content, is_anonymous=is_anonymous)
    session.add(prayer)
    await session.commit()
    await session.refresh(prayer)
    return prayer

async def get_prayers(session: AsyncSession, limit: int = 20, offset: int = 0):
    stmt = select(Prayer).order_by(Prayer.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

async def increment_amen(session: AsyncSession, prayer_id: int, user_id: int):
    from .models import PrayerAmen
    
    # Check if user already said Amen for this prayer
    stmt = select(PrayerAmen).where(PrayerAmen.prayer_id == prayer_id, PrayerAmen.user_id == user_id)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    # Get prayer to get current count and author_id
    stmt = select(Prayer).where(Prayer.id == prayer_id)
    result = await session.execute(stmt)
    prayer = result.scalar_one_or_none()
    
    if not prayer:
        return 0, 0, False

    if existing:
        # Already voted, just return current count
        return prayer.amen_count, prayer.user_id, False
    
    # Add new Amen record
    new_amen = PrayerAmen(prayer_id=prayer_id, user_id=user_id)
    session.add(new_amen)
    
    # Increment count
    prayer.amen_count += 1
    await session.commit()
    
    return prayer.amen_count, prayer.user_id, True

async def get_user_amens(session: AsyncSession, user_id: int):
    from .models import PrayerAmen
    stmt = select(PrayerAmen.prayer_id).where(PrayerAmen.user_id == user_id)
    result = await session.execute(stmt)
    return set(result.scalars().all())

async def delete_prayer(session: AsyncSession, prayer_id: int):
    from sqlalchemy import delete
    from .models import PrayerAmen
    
    # First delete associated amens
    await session.execute(delete(PrayerAmen).where(PrayerAmen.prayer_id == prayer_id))
    # Then delete the prayer
    await session.execute(delete(Prayer).where(Prayer.id == prayer_id))
    await session.commit()
