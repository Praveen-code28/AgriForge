import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_current_user,
    get_disease_service,
    get_prediction_repo,
    get_settings_dep,
)
from backend.app.core.config import Settings
from backend.app.db.session import get_db
from backend.app.models import User, AnalysisReport
from backend.app.repositories.prediction_repository import PredictionRepository
from backend.app.schemas import PaginatedPredictions, PredictionRead
from backend.app.services.analysis_service import DiseaseService
from backend.app.utils.file_upload import save_upload

router = APIRouter()


def _to_prediction_read(record) -> PredictionRead:
    return PredictionRead(
        id=record.id,
        image_path=record.image_path,
        primary_plant=record.primary_plant,
        primary_disease=record.primary_disease,
        primary_confidence=record.primary_confidence,
        predictions=json.loads(record.predictions_json),
        created_at=record.created_at.isoformat(),
    )


@router.post("/disease")
async def predict_disease(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
    disease_service: Annotated[DiseaseService, Depends(get_disease_service)],
    prediction_repo: Annotated[PredictionRepository, Depends(get_prediction_repo)],
    image: UploadFile = File(...),
    farm_id: int | None = Form(default=None),
):
    _, saved_path = await save_upload(image, settings.upload_path, settings.max_upload_bytes)
    result = disease_service.predict_disease(str(saved_path))
    record = prediction_repo.create_prediction(
        db,
        current_user.id,
        str(saved_path.relative_to(settings.repo_root)) if saved_path.is_relative_to(settings.repo_root) else str(saved_path),
        result["predictions"],
        farm_id=farm_id,
    )
    return {"prediction_id": record.id, **result}


@router.get("/history", response_model=PaginatedPredictions)
def prediction_history(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    prediction_repo: Annotated[PredictionRepository, Depends(get_prediction_repo)],
    page: int = 1,
    page_size: int = 20,
):
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Invalid pagination parameters")
    items, total = prediction_repo.list_paginated(db, current_user.id, page, page_size)
    return PaginatedPredictions(
        items=[_to_prediction_read(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{prediction_id}", response_model=PredictionRead)
def get_prediction(
    prediction_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    prediction_repo: Annotated[PredictionRepository, Depends(get_prediction_repo)],
):
    record = prediction_repo.get_by_id(db, current_user.id, prediction_id)
    if not record:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return _to_prediction_read(record)


@router.get("/{prediction_id}/report")
def get_prediction_report(
    prediction_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    report = (
        db.query(AnalysisReport)
        .filter(
            AnalysisReport.prediction_id == prediction_id,
            AnalysisReport.user_id == current_user.id
        )
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Analysis report not found")

    return {
        "prediction_id": report.prediction_id,
        "disease": json.loads(report.disease_result),
        "treatment": json.loads(report.treatment_result),
        "weather": json.loads(report.weather_result) if report.weather_result else None,
        "combined": json.loads(report.combined_json),
    }
