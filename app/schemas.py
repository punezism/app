from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models import MatchStatus, MatchResult


# ---------- Auth ----------

class TelegramLoginData(BaseModel):
    """دیتایی که Telegram Login Widget برمی‌گرداند"""
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    is_admin: bool
    balance: int


# ---------- Wallet ----------

class TransactionOut(BaseModel):
    id: int
    amount: int
    type: str
    balance_after: int
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AdminGrantRequest(BaseModel):
    user_id: int
    amount: int = Field(gt=0)
    note: Optional[str] = None


# ---------- Matches ----------

class MatchCreate(BaseModel):
    team_a: str
    team_b: str
    group_name: Optional[str] = None
    start_time: datetime


class MatchUpdate(BaseModel):
    team_a: Optional[str] = None
    team_b: Optional[str] = None
    group_name: Optional[str] = None
    start_time: Optional[datetime] = None
    status: Optional[MatchStatus] = None


class MatchResultPayload(BaseModel):
    result: MatchResult


class MatchOut(BaseModel):
    id: int
    team_a: str
    team_b: str
    group_name: Optional[str]
    start_time: datetime
    status: MatchStatus
    result: Optional[MatchResult]

    class Config:
        from_attributes = True


# ---------- Bets ----------

class BetCreate(BaseModel):
    match_id: int
    choice: MatchResult
    stake_amount: int = Field(gt=0)
    title: Optional[str] = None


class BetJoin(BaseModel):
    choice: MatchResult
    stake_amount: int = Field(gt=0)


class BetParticipantOut(BaseModel):
    user_id: int
    choice: MatchResult
    stake_amount: int
    payout_amount: Optional[int]

    class Config:
        from_attributes = True


class BetOut(BaseModel):
    id: int
    match_id: int
    title: Optional[str]
    status: str
    created_by: int
    participants: List[BetParticipantOut]

    class Config:
        from_attributes = True
