from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    """Dependency برای گرفتن یک سشن دیتابیس در هر ریکوئست"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """
    برای محیط تست/توسعه: جدول‌ها رو مستقیم از روی مدل‌ها می‌سازه.
    در پروداکشن بهتره به جای این از Alembic برای مایگریشن استفاده کنیم.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
