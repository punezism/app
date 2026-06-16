from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_admin
from app.models import Match, MatchStatus, Bet, BetStatus, User
from app.schemas import MatchCreate, MatchUpdate, MatchResultPayload, MatchOut
from app.crud import settle_bet

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/", response_model=List[MatchOut])
async def list_matches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).order_by(Match.start_time))
    return result.scalars().all()


@router.get("/{match_id}", response_model=MatchOut)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="مسابقه یافت نشد")
    return match


@router.post("/", response_model=MatchOut)
async def create_match(
    payload: MatchCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    match = Match(**payload.model_dump())
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


@router.put("/{match_id}", response_model=MatchOut)
async def update_match(
    match_id: int,
    payload: MatchUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="مسابقه یافت نشد")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(match, field, value)

    await db.commit()
    await db.refresh(match)
    return match


@router.post("/{match_id}/result")
async def set_match_result(
    match_id: int,
    payload: MatchResultPayload,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    ادمین نتیجه‌ی نهایی مسابقه رو ثبت می‌کند.
    این کار باعث می‌شود همه‌ی شرط‌های باز مربوط به این مسابقه به‌صورت خودکار تسویه شوند:
    - برنده: کل استخر (منهای کارمزد) واریز می‌شود
    - مساوی / بدون برنده مشخص: مبلغ به همه‌ی شرکت‌کننده‌ها برمی‌گردد
    """
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="مسابقه یافت نشد")

    match.result = payload.result
    match.status = MatchStatus.finished
    await db.flush()

    result = await db.execute(
        select(Bet)
        .options(selectinload(Bet.participants))
        .where(Bet.match_id == match.id, Bet.status == BetStatus.open)
    )
    open_bets = result.scalars().all()

    for bet in open_bets:
        await settle_bet(db, bet, match)

    await db.commit()
    return {"ok": True, "match_id": match.id, "result": match.result, "settled_bets": len(open_bets)}
