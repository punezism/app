from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Bet, BetParticipant, BetStatus, Match, MatchStatus, User, TransactionType
from app.schemas import BetCreate, BetJoin, BetOut
from app.crud import debit_wallet, credit_wallet, InsufficientBalanceError

router = APIRouter(prefix="/bets", tags=["bets"])


@router.post("/", response_model=BetOut)
async def create_bet(
    payload: BetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await db.get(Match, payload.match_id)
    if not match or match.status != MatchStatus.scheduled:
        raise HTTPException(status_code=400, detail="این مسابقه برای شرط‌بندی باز نیست")

    try:
        await debit_wallet(
            db, current_user, payload.stake_amount, TransactionType.bet_stake,
            note="ایجاد شرط جدید"
        )
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))

    bet = Bet(match_id=match.id, title=payload.title, created_by=current_user.id)
    db.add(bet)
    await db.flush()

    participant = BetParticipant(
        bet_id=bet.id,
        user_id=current_user.id,
        choice=payload.choice,
        stake_amount=payload.stake_amount,
    )
    db.add(participant)
    await db.commit()

    result = await db.execute(
        select(Bet).options(selectinload(Bet.participants)).where(Bet.id == bet.id)
    )
    return result.scalar_one()


@router.post("/{bet_id}/join", response_model=BetOut)
async def join_bet(
    bet_id: int,
    payload: BetJoin,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bet).options(selectinload(Bet.participants)).where(Bet.id == bet_id)
    )
    bet = result.scalar_one_or_none()
    if not bet or bet.status != BetStatus.open:
        raise HTTPException(status_code=400, detail="این شرط برای پیوستن باز نیست")

    if any(p.user_id == current_user.id for p in bet.participants):
        raise HTTPException(status_code=400, detail="شما قبلاً در این شرط شرکت کرده‌اید")

    try:
        await debit_wallet(
            db, current_user, payload.stake_amount, TransactionType.bet_stake,
            ref_bet_id=bet.id, note="پیوستن به شرط"
        )
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))

    participant = BetParticipant(
        bet_id=bet.id,
        user_id=current_user.id,
        choice=payload.choice,
        stake_amount=payload.stake_amount,
    )
    db.add(participant)
    await db.commit()
    await db.refresh(bet)
    return bet


@router.post("/{bet_id}/cancel")
async def cancel_bet(
    bet_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bet).options(selectinload(Bet.participants)).where(Bet.id == bet_id)
    )
    bet = result.scalar_one_or_none()
    if not bet:
        raise HTTPException(status_code=404, detail="شرط یافت نشد")
    if bet.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="فقط سازنده‌ی شرط می‌تواند آن را لغو کند")
    if bet.status != BetStatus.open:
        raise HTTPException(status_code=400, detail="این شرط دیگر باز نیست")
    if len(bet.participants) > 1:
        raise HTTPException(status_code=400, detail="نمی‌توان شرطی را که فرد دیگری به آن پیوسته لغو کرد")

    bet.status = BetStatus.cancelled
    creator_participant = bet.participants[0]
    await credit_wallet(
        db, creator_participant.user_id, creator_participant.stake_amount,
        TransactionType.bet_refund, ref_bet_id=bet.id, note="لغو شرط توسط سازنده"
    )
    await db.commit()
    return {"ok": True}


@router.get("/mine", response_model=List[BetOut])
async def my_bets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bet)
        .join(BetParticipant)
        .options(selectinload(Bet.participants))
        .where(BetParticipant.user_id == current_user.id)
        .order_by(Bet.created_at.desc())
    )
    return result.scalars().unique().all()


@router.get("/{bet_id}", response_model=BetOut)
async def get_bet(bet_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bet).options(selectinload(Bet.participants)).where(Bet.id == bet_id)
    )
    bet = result.scalar_one_or_none()
    if not bet:
        raise HTTPException(status_code=404, detail="شرط یافت نشد")
    return bet
