import asyncio
from sqlalchemy import text
from db.base import engine

async def fix_schema():
    print("Checking database schema...")
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='is_subscribed';"
        ))
        column_exists = result.fetchone() is not None
        
        if not column_exists:
            print("Adding 'is_subscribed' column to 'users' table...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_subscribed BOOLEAN DEFAULT FALSE;"))
            print("Column added successfully.")
        else:
            print("'is_subscribed' column already exists.")

        # Check if is_blocked column exists
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='is_blocked';"
        ))
        column_exists = result.fetchone() is not None
        
        if not column_exists:
            print("Adding 'is_blocked' column to 'users' table...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE;"))
            print("Column added successfully.")
        else:
            print("'is_blocked' column already exists.")

        # Create prayer_amens table if not exists
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prayer_amens (
                id SERIAL PRIMARY KEY,
                prayer_id INTEGER NOT NULL,
                user_id BIGINT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_prayer_amens_prayer_id ON prayer_amens(prayer_id);
            CREATE INDEX IF NOT EXISTS idx_prayer_amens_user_id ON prayer_amens(user_id);
        """))
        print("Ensured 'prayer_amens' table exists.")


if __name__ == "__main__":
    asyncio.run(fix_schema())
