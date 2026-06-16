import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, BigInteger, Integer, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MatchStatus(str, enum.Enum):
    scheduled = "scheduled"   # هنوز برگزار نشده، شرط‌بندی روش باز است
    finished = "finished"     # نتیجه ثبت شده و شرط‌ها تسویه شده‌اند
    cancelled = "cancelled"   # مسابقه لغو شده


class MatchResult(str, enum.Enum):
    team_a = "team_a"
    team_b = "team_b"
    draw = "draw"


class BetStatus(str, enum.Enum):
    open = "open"
    settled = "settled"
    cancelled = "cancelled"


class TransactionType(str, enum.Enum):
    signup_bonus = "signup_bonus"   # هدیه ثبت‌نام
    admin_grant = "admin_grant"     # هدیه دستی ادمین
    bet_stake = "bet_stake"         # برداشت بابت شرکت در شرط
    bet_payout = "bet_payout"       # واریز بابت برد شرط
    bet_refund = "bet_refund"       # بازگشت وجه (مساوی یا لغو شرط)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # موجودی کیف پول به "سکه" (فعلاً ارز خیالی، بعداً قابل تبدیل به Stars/TON)
    balance: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transactions: Mapped[List["Transaction"]] = relationship(back_populates="user")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_a: Mapped[str] = mapped_column(String(128))
    team_b: Mapped[str] = mapped_column(String(128))
    group_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.scheduled)
    result: Mapped[Optional[MatchResult]] = mapped_column(Enum(MatchResult), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    bets: Mapped[List["Bet"]] = relationship(back_populates="match")


class Bet(Base):
    """
    یک 'شرط' در واقع یک استخر (pool) است که بین دو یا چند نفر دوست
    روی یک مسابقه‌ی مشخص شکل می‌گیرد. نفر اول شرط را می‌سازد،
    بقیه با /join به آن ملحق می‌شوند.
    """
    __tablename__ = "bets"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    status: Mapped[BetStatus] = mapped_column(Enum(BetStatus), default=BetStatus.open)

    # درصد کارمزد - فعلاً صفر، بعداً وقتی پرداخت واقعی اضافه شد فعالش می‌کنیم
    fee_percent: Mapped[int] = mapped_column(Integer, default=0)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    match: Mapped["Match"] = relationship(back_populates="bets")
    participants: Mapped[List["BetParticipant"]] = relationship(
        back_populates="bet", cascade="all, delete-orphan"
    )


class BetParticipant(Base):
    __tablename__ = "bet_participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    bet_id: Mapped[int] = mapped_column(ForeignKey("bets.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    choice: Mapped[MatchResult] = mapped_column(Enum(MatchResult))
    stake_amount: Mapped[int] = mapped_column(Integer)
    payout_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    bet: Mapped["Bet"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship()


class Transaction(Base):
    """دفتر کل تراکنش‌های کیف پول - برای شفافیت و قابلیت گزارش‌گیری"""
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    amount: Mapped[int] = mapped_column(Integer)  # مثبت = واریز، منفی = برداشت
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    reference_bet_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bets.id"), nullable=True)

    balance_after: Mapped[int] = mapped_column(Integer)
    note: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="transactions")
