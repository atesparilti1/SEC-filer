from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AnalysisRecord, AnalyzeRequest
from app.services import analyze_pipeline

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisRecord)
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)) -> AnalysisRecord:
    return analyze_pipeline.analyze_filing(
        db, request.ticker, request.accession_number, request.filing_type
    )


@router.get("/analysis/{analysis_id}", response_model=AnalysisRecord)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)) -> AnalysisRecord:
    record = analyze_pipeline.get_analysis_by_id(db, analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No analysis found with id {analysis_id}")
    return record
