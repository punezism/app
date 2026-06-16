from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, get_current_admin
from app.models import User, Transaction, TransactionType
from app.schemas import TransactionOut, AdminGrantRequest
from app.crud import credit_wallet

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/me")
async def my_wallet(current_user: User = Depends(get_current_user)):
    return {"user_id": current_user.id, "balance": current_user.balance}


@router.get("/transactions", response_model=List[TransactionOut])
async def my_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
    )
    return result.scalars().all()


@router.post("/admin-grant")
async def admin_grant(
    payload: AdminGrantRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """ادمین می‌تواند سکه‌ی خیالی به هر کاربری هدیه بدهد (مثلاً برای تست یا جایزه)"""
    target = await db.get(User, payload.user_id)
    if not target:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")

    await credit_wallet(
        db, target.id, payload.amount, TransactionType.admin_grant, note=payload.note
    )
    await db.commit()
    return {"ok": True, "user_id": target.id, "new_balance": target.balance}
