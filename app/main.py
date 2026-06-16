import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import auth, wallet, matches, bets

app = FastAPI(title="World Cup Friendly Bet API", version="0.1.0")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# توجه: برای پروداکشن allow_origins رو به دامنه‌ی واقعی WebApp محدود کن
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(matches.router)
app.include_router(bets.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")
