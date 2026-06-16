from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wcbet"

    BOT_TOKEN: str = "CHANGE_ME"

    JWT_SECRET: str = "CHANGE_ME_TOO_PLEASE"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # یک هفته

    # تعداد سکه‌ی هدیه‌ی شروع برای کاربر تازه‌وارد
    STARTING_BALANCE: int = 100

    # آیدی عددی تلگرام ادمین‌ها - این کاربرها دسترسی به پنل مدیریت دارند
    ADMIN_TELEGRAM_IDS: List[int] = []

    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("DATABASE_URL")
    @classmethod
    def fix_driver_scheme(cls, v: str) -> str:
        """
        ریلوی (و خیلی از پلتفرم‌های هاستینگ) آدرس دیتابیس رو با
        postgres:// یا postgresql:// می‌دن، ولی ما برای async نیاز به
        postgresql+asyncpg:// داریم. این تابع خودکار درستش می‌کند.
        """
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
