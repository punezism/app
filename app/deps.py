from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security import decode_access_token
from app.models import User


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="توکن احراز هویت ارسال نشده است")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        user_id = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="توکن نامعتبر یا منقضی شده است")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="کاربر یافت نشد")
    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="این عملیات فقط برای مدیر مجاز است")
    return current_user
