from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.core.config import settings
from api.core.database import Base, engine
from api.routers import (
    auth, users, transactions, budget,
    analytics, settings as settings_router,
    webhooks, categories, oauth, seed,
)

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/v1"
app.include_router(auth.router,            prefix=PREFIX)
app.include_router(oauth.router,           prefix=PREFIX)
app.include_router(users.router,           prefix=PREFIX)
app.include_router(transactions.router,    prefix=PREFIX)
app.include_router(budget.router,          prefix=PREFIX)
app.include_router(analytics.router,       prefix=PREFIX)
app.include_router(settings_router.router, prefix=PREFIX)
app.include_router(webhooks.router,        prefix=PREFIX)
app.include_router(categories.router,      prefix=PREFIX)
app.include_router(seed.router,            prefix=PREFIX)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": settings.APP_VERSION}