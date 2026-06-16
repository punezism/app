import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings


def verify_telegram_login(data: dict) -> bool:
    """
    طبق مستندات تلگرام: هش رو با کلید سکرت (هش شده از BOT_TOKEN) چک می‌کنیم
    تا مطمئن شیم دیتای لاگین واقعاً از طرف تلگرام آمده و دستکاری نشده.
    https://core.telegram.org/widgets/login
    """
    received_hash = data.get("hash")
    if not received_hash:
        return False

    check_data = {k: v for k, v in data.items() if k != "hash" and v is not None}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(check_data.items()))

    secret_key = hashlib.sha256(settings.BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return False

    auth_date = int(data.get("auth_date", 0))
    if time.time() - auth_date > 86400:  # دیتای لاگین قدیمی‌تر از یک روز رو قبول نکن
        return False

    return True


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return int(payload["sub"])
