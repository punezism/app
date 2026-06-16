from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Bet, BetStatus, Match, MatchResult, Transaction, TransactionType


class InsufficientBalanceError(Exception):
    pass


async def debit_wallet(
    db: AsyncSession,
    user: User,
    amount: int,
    ttype: TransactionType,
    ref_bet_id: int | None = None,
    note: str | None = None,
) -> None:
    """کم کردن مبلغ از کیف پول کاربر (مثلاً وقتی در شرط شرکت می‌کند)"""
    if user.balance < amount:
        raise InsufficientBalanceError(f"موجودی کافی نیست. موجودی فعلی: {user.balance}")

    user.balance -= amount
    db.add(
        Transaction(
            user_id=user.id,
            amount=-amount,
            type=ttype,
            reference_bet_id=ref_bet_id,
            balance_after=user.balance,
            note=note,
        )
    )
    await db.flush()


async def credit_wallet(
    db: AsyncSession,
    user_id: int,
    amount: int,
    ttype: TransactionType,
    ref_bet_id: int | None = None,
    note: str | None = None,
) -> None:
    """واریز مبلغ به کیف پول کاربر (هدیه ادمین، برد شرط، بازگشت وجه)"""
    if amount <= 0:
        return
    user = await db.get(User, user_id)
    user.balance += amount
    db.add(
        Transaction(
            user_id=user.id,
            amount=amount,
            type=ttype,
            reference_bet_id=ref_bet_id,
            balance_after=user.balance,
            note=note,
        )
    )
    await db.flush()


async def settle_bet(db: AsyncSession, bet: Bet, match: Match) -> None:
    """
    منطق تسویه:
    - برنده‌ها = کسانی که choice شون با نتیجه‌ی مسابقه یکی است
    - اگر کسی برنده نشد یا طرف مقابلی وجود نداشت -> به همه پول‌شون برمی‌گردد (مثل حالت مساوی)
    - در غیر این صورت: استخر بازنده‌ها (منهای کارمزد) به نسبت سهم هر برنده بین برنده‌ها تقسیم می‌شود
    """
    if match.result is None:
        raise ValueError("نتیجه‌ی مسابقه هنوز ثبت نشده")

    participants = bet.participants
    winners = [p for p in participants if p.choice == match.result]
    losers = [p for p in participants if p.choice != match.result]

    if not winners or not losers:
        # یا کسی درست پیش‌بینی نکرده، یا طرف مقابلی وجود نداشته -> بازگشت پول به همه
        for p in participants:
            p.payout_amount = p.stake_amount
            await credit_wallet(
                db, p.user_id, p.stake_amount, TransactionType.bet_refund,
                ref_bet_id=bet.id, note="بازگشت وجه شرط (بدون برنده مشخص)"
            )
    else:
        losers_pool = sum(p.stake_amount for p in losers)
        winners_pool = sum(p.stake_amount for p in winners)
        fee_amount = (losers_pool * bet.fee_percent) // 100
        distributable = losers_pool - fee_amount

        for p in winners:
            share = (p.stake_amount * distributable) // winners_pool if winners_pool else 0
            payout = p.stake_amount + share
            p.payout_amount = payout
            await credit_wallet(
                db, p.user_id, payout, TransactionType.bet_payout,
                ref_bet_id=bet.id, note="برد شرط"
            )
        for p in losers:
            p.payout_amount = 0

    bet.status = BetStatus.settled
    bet.settled_at = datetime.now(timezone.utc)
    await db.flush()
