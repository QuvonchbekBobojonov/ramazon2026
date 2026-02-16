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

if __name__ == "__main__":
    asyncio.run(fix_schema())
