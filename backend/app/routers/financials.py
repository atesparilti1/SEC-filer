from fastapi import APIRouter

from app.schemas import FinancialsResponse
from app.services.analyze_pipeline import get_financials

router = APIRouter(prefix="/api/financials", tags=["financials"])


@router.get("/{ticker}", response_model=FinancialsResponse)
def get_financials_route(ticker: str) -> FinancialsResponse:
    return get_financials(ticker)
