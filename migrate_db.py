import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.models import Base, User
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CONFIGURATION - Update these if necessary
OLD_DB_URL = "postgresql+asyncpg://neondb_owner:npg_7HZhkTGpV6qm@ep-fancy-paper-ai5kwohx-pooler.c-4.us-east-1.aws.neon.tech/neondb?ssl=require"
NEW_DB_URL = "postgresql+asyncpg://ramazon:ramazon_pass@localhost:5432/ramazon_db"

async def migrate():
    logger.info("Starting migration from Neon to Local Docker DB...")
    
    # Engines
    old_engine = create_async_engine(OLD_DB_URL)
    new_engine = create_async_engine(NEW_DB_URL)
    
    # Sessions
    old_session_maker = sessionmaker(old_engine, class_=AsyncSession, expire_on_commit=False)
    new_session_maker = sessionmaker(new_engine, class_=AsyncSession, expire_on_commit=False)
    
    # 1. Create tables in new DB if they don't exist
    async with new_engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Dangerous, uncomment only if you want fresh start
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Fetch users from OLD
    async with old_session_maker() as old_session:
        result = await old_session.execute(select(User))
        users = result.scalars().all()
        logger.info(f"Found {len(users)} users in old database.")

    # 3. Push to NEW
    async with new_session_maker() as new_session:
        count = 0
        for user in users:
            # Check if user already exists in new DB to avoid unique constraints
            exists_stmt = select(User).where(User.telegram_id == user.telegram_id)
            exists_res = await new_session.execute(exists_stmt)
            if exists_res.scalar_one_or_none():
                continue
            
            # Create a new instance for the new session (detached from old session)
            new_user = User(
                telegram_id=user.telegram_id,
                full_name=user.full_name,
                username=user.username,
                region=user.region,
                created_at=user.created_at
            )
            new_session.add(new_user)
            count += 1
            
            if count % 50 == 0:
                await new_session.commit()
                logger.info(f"Migrated {count} users...")
        
        await new_session.commit()
        logger.info(f"Successfully migrated {count} new users to local DB.")

    await old_engine.dispose()
    await new_engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except Exception as e:
        logger.error(f"Migration failed: {e}")
