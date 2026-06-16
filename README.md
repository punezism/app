# شرط‌بندی دوستانه جام جهانی - اسکلت اولیه (نسخه سکه‌ی خیالی)

این نسخه با **سکه‌ی خیالی** کار می‌کند (هر کاربر جدید ۱۰۰ سکه می‌گیرد، ادمین هم می‌تواند دستی سکه هدیه بدهد).
وقتی تست‌ها جواب داد، فقط لایه‌ی کیف پول (`debit_wallet` / `credit_wallet`) را به Telegram Stars یا TON وصل می‌کنیم؛ بقیه‌ی منطق (شرط، تسویه، مسابقه) دست نمی‌خورد.

## ۱. نصب و راه‌اندازی دیتابیس

```bash
# پستگرس باید نصب و در حال اجرا باشد
createdb wcbet

cd wc_bet_app
python -m venv venv
source venv/bin/activate      # ویندوز: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# فایل .env رو باز کن و این مقادیر رو پر کن:
#   BOT_TOKEN          -> توکن باتت از @BotFather
#   JWT_SECRET          -> یک رشته‌ی تصادفی طولانی
#   ADMIN_TELEGRAM_IDS  -> آیدی عددی خودت، مثلاً [123456789]
#   DATABASE_URL        -> در صورت نیاز یوزر/پسورد پستگرس رو اصلاح کن
```

## ۲. اجرای سرور

```bash
uvicorn app.main:app --reload --port 8000
```

- مستندات تعاملی API (Swagger): http://localhost:8000/docs
  از همینجا هم می‌تونی همه‌ی اندپوینت‌ها رو بدون نیاز به ساخت UI تست کنی.

## ۳. تنظیم دامنه برای Telegram Login Widget

ویجت لاگین تلگرام **روی localhost کار نمی‌کند** و باید روی یک دامنه‌ی واقعی (یا ساب‌دامنه با HTTPS) باز شود.
برای تست سریع:

1. با `@BotFather` برو روی بات‌ت → **Bot Settings → Domain** و دامنه‌ی تستت رو ثبت کن.
2. برای گرفتن یک URL عمومی موقت از روی لپ‌تاپت می‌تونی از `ngrok http 8000` استفاده کنی و همون آدرس https رو در BotFather ثبت کنی.
3. در `static/index.html` و `static/admin.html` مقدار `YOUR_BOT_USERNAME` رو با یوزرنیم بات (بدون @) عوض کن.

## ۴. تست سریع کل فلو

1. باز کن: `https://<your-domain>/static/index.html` → با تلگرام لاگین کن → ۱۰۰ سکه می‌گیری.
2. باز کن: `https://<your-domain>/static/admin.html` با اکانت ادمین → یک مسابقه اضافه کن.
3. از همون صفحه‌ی index یا از `/docs`:
   - با کاربر A یک شرط بساز (`POST /bets/`) روی برد یک تیم با مقدار مشخص.
   - با کاربر B به همون شرط بپیوند (`POST /bets/{id}/join`) با انتخاب طرف مقابل.
4. برگرد به admin.html و نتیجه‌ی مسابقه رو ثبت کن → شرط به‌صورت خودکار تسویه می‌شود و موجودی برنده آپدیت می‌شود.

## ساختار پروژه

```
wc_bet_app/
  app/
    main.py          نقطه‌ی ورود FastAPI
    config.py         تنظیمات (.env)
    database.py        اتصال async به PostgreSQL
    models.py          مدل‌های SQLAlchemy (User, Match, Bet, BetParticipant, Transaction)
    schemas.py          مدل‌های Pydantic ورودی/خروجی
    security.py         تایید Telegram Login + JWT
    deps.py              دیپندنسی‌های auth (get_current_user / get_current_admin)
    crud.py               منطق کیف پول و تسویه‌ی شرط
    routers/
      auth.py             POST /auth/telegram-login
      wallet.py            GET /wallet/me ، GET /wallet/transactions ، POST /wallet/admin-grant
      matches.py            CRUD مسابقات + POST /matches/{id}/result (تسویه‌ی خودکار)
      bets.py                 POST /bets/ ، POST /bets/{id}/join ، POST /bets/{id}/cancel ، GET /bets/mine
  static/
    index.html      صفحه‌ی تست کاربر عادی
    admin.html        صفحه‌ی تست پنل مدیریت
```

## دیپلوی روی Railway (قدم به قدم)

### قدم ۱ - آپلود کد روی گیت‌هاب
1. یک ریپو جدید (مثلاً `wc-bet-app`) در گیت‌هاب بساز.
2. توی پوشه‌ی `wc_bet_app` این دستورها رو بزن:
   ```bash
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/USERNAME/wc-bet-app.git
   git push -u origin main
   ```

### قدم ۲ - ساخت پروژه در Railway
1. وارد [railway.com](https://railway.com) شو → **New Project** → **Deploy from GitHub repo** → ریپوی `wc-bet-app` رو انتخاب کن.
2. روی همون پروژه، دکمه‌ی **+ New** رو بزن → **Database** → **Add PostgreSQL**. ریلوی خودش یک سرویس Postgres جدا بالا می‌آره.

### قدم ۳ - تنظیم Environment Variables
برو روی سرویس FastAPI (همون که از گیت‌هاب ساختی) → تب **Variables** → این متغیرها رو اضافه کن:

| Variable | مقدار |
|---|---|
| `DATABASE_URL` | از دکمه‌ی Add Reference، سرویس Postgres رو انتخاب کن و متغیر `DATABASE_URL` همونو رفرنس بده (ریلوی خودش این مقدار رو با فرمت `postgres://...` می‌سازه - کد ما خودش تبدیلش می‌کند) |
| `BOT_TOKEN` | توکن باتت از BotFather |
| `JWT_SECRET` | یک رشته‌ی تصادفی طولانی (مثلاً از یک پسورد جنریتور) |
| `ADMIN_TELEGRAM_IDS` | مثلاً `[123456789]` |
| `STARTING_BALANCE` | `100` |
| `DEBUG` | `false` |

### قدم ۴ - دیپلوی
ریلوی به خاطر وجود فایل `Procfile` خودش تشخیص می‌ده باید با
`uvicorn app.main:app --host 0.0.0.0 --port $PORT` بالا بیاد. بعد از چند ثانیه build، در تب **Settings → Networking** روی **Generate Domain** بزن تا یک آدرس عمومی مثل
`https://wc-bet-app.up.railway.app` بگیری.

### قدم ۵ - وصل کردن دامنه به Telegram Login
1. توی تلگرام برو پیش `@BotFather` → `/setdomain` → باتت رو انتخاب کن → دامنه‌ی همین که ریلوی دادت (بدون `https://`) رو بفرست.
2. توی فایل‌های `static/index.html` و `static/admin.html` مقدار `YOUR_BOT_USERNAME` رو با یوزرنیم بات (بدون @) جایگزین کن، کامیت و پوش کن تا ریلوی خودش redeploy کند.

### قدم ۶ - تست نهایی
- `https://<آدرس-ریلوی>/static/index.html` رو باز کن، با تلگرام لاگین کن.
- `https://<آدرس-ریلوی>/static/admin.html` رو با اکانت ادمین باز کن، یک مسابقه بساز.
- مستندات کامل API هم همیشه روی `/docs` در دسترسه اگه خواستی چیزی رو مستقیم تست کنی.

## نکات مهم برای قدم بعدی

- **اتصال به Telegram Stars/TON**: وقتی آماده بودیم، در `crud.py` تابع `debit_wallet` رو طوری تغییر می‌دیم که قبل از کسر سکه، یک Invoice واقعی (`createInvoiceLink` تلگرام برای Stars، یا تراکنش TON) باز کنه و فقط بعد از تایید پرداخت موجودی رو آپدیت کنه.
- **کارمزد**: فیلد `fee_percent` روی مدل `Bet` از همین الان آماده‌ست؛ فقط مقدارش رو در `BetCreate` قابل تنظیم می‌کنیم (یا یک مقدار ثابت سراسری در `config.py` می‌گذاریم).
- **مهاجرت دیتابیس**: الان جدول‌ها مستقیم با `Base.metadata.create_all` ساخته می‌شن (`init_db`). قبل از دیپلوی واقعی بهتره Alembic رو اضافه کنیم تا تغییرات اسکیما کنترل‌شده باشه.
- **دیپلوی روی Railway**: دقیقاً مثل بات‌های قبلی‌ت - یک سرویس Postgres از Railway بگیر، `DATABASE_URL` رو از اونجا بگیر و در Environment Variables ست کن، و سرویس FastAPI رو با `uvicorn app.main:app --host 0.0.0.0 --port $PORT` بالا بیار.
- **اتصال به Telegram WebApp**: بعد از تست با مرورگر معمولی، همین `index.html` رو با اضافه کردن اسکریپت `https://telegram.org/js/telegram-web-app.js` و استفاده از `Telegram.WebApp.initDataUnsafe` (به‌جای ویجت لاگین معمولی) داخل بات وصل می‌کنیم - این کار نیاز به تغییر کمی در `verify_telegram_login` دارد چون فرمت initData با لاگین ویجت کمی فرق دارد، که در گام بعدی برات اضافه می‌کنم.
