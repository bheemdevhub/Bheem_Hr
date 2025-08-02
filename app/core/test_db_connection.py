import asyncio
from .database import AsyncSessionLocal
from sqlalchemy import text

def print_db_status():
    async def inner():
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Database connected: {version}")
                return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    asyncio.run(inner())

if __name__ == "__main__":
    print_db_status()
