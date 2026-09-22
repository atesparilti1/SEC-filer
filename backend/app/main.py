from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.routers import analysis, company, compare, financials
from app.services.demo_seed import seed_demo_data
from app.services.exceptions import (
    AIAnalysisError,
    FilingNotFoundError,
    FilingParsingError,
    FinancialDataUnavailableError,
    SECUnavailableError,
    TickerNotFoundError,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="SEC Filing Analyzer",
    description="AI-powered analysis of SEC 10-K and 10-Q filings.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_ERROR_STATUS_MAP = {
    TickerNotFoundError: 404,
    FilingNotFoundError: 404,
    FinancialDataUnavailableError: 404,
    SECUnavailableError: 502,
    FilingParsingError: 422,
    AIAnalysisError: 502,
}


def _register_exception_handlers(app: FastAPI) -> None:
    for exc_class, status_code in _ERROR_STATUS_MAP.items():

        def make_handler(code: int):
            async def handler(request: Request, exc: Exception) -> JSONResponse:
                return JSONResponse(status_code=code, content={"detail": str(exc)})

            return handler

        app.add_exception_handler(exc_class, make_handler(status_code))


_register_exception_handlers(app)


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(company.router)
app.include_router(financials.router)
app.include_router(analysis.router)
app.include_router(compare.router)
