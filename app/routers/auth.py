from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security import verify_telegram_login, create_access_token
from app.models import User, Transaction, TransactionType
from app.schemas import TelegramLoginData, TokenResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram-login", response_model=TokenResponse)
async def telegram_login(data: TelegramLoginData, db: AsyncSession = Depends(get_db)):
    if not verify_telegram_login(data.model_dump(exclude_none=True)):
        raise HTTPException(status_code=401, detail="دیتای ورود از تلگرام نامعتبر است")

    result = await db.execute(select(User).where(User.telegram_id == data.id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=data.id,
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            photo_url=data.photo_url,
            is_admin=data.id in settings.ADMIN_TELEGRAM_IDS,
            balance=settings.STARTING_BALANCE,
        )
        db.add(user)
        await db.flush()

        if settings.STARTING_BALANCE > 0:
            db.add(
                Transaction(
                    user_id=user.id,
                    amount=settings.STARTING_BALANCE,
                    type=TransactionType.signup_bonus,
                    balance_after=user.balance,
                    note="هدیه ثبت‌نام",
                )
            )
        await db.commit()
    else:
        # هر بار لاگین، اطلاعات پروفایل رو به‌روز کن
        user.username = data.username
        user.first_name = data.first_name
        user.last_name = data.last_name
        user.photo_url = data.photo_url
        await db.commit()

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        is_admin=user.is_admin,
        balance=user.balance,
    )
