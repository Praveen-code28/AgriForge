from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_analysis_service,
    get_ai_analysis_service,
    get_current_user,
    get_prediction_repo,
    get_settings_dep,
    get_weather_service,
)
from backend.app.core.config import Settings
from backend.app.db.session import get_db
from backend.app.models import User
from backend.app.repositories.prediction_repository import PredictionRepository
from backend.app.schemas import CompleteAnalysisResponse, WeatherAnalysisRequest, AIReportResponse
from backend.app.services.analysis_service import AnalysisService, WeatherService
from backend.app.services.ai_analysis_service import AIAnalysisService
from backend.app.utils.file_upload import save_upload

router = APIRouter()


@router.post("/weather")
def analyze_weather(
    payload: WeatherAnalysisRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    weather_service: Annotated[WeatherService, Depends(get_weather_service)],
):
    return weather_service.analyze(
        payload.crop,
        payload.disease,
        payload.confidence,
        payload.lat,
        payload.lon,
        payload.address,
    )


@router.post("/complete", response_model=CompleteAnalysisResponse)
async def complete_analysis(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
    analysis_service: Annotated[AnalysisService, Depends(get_analysis_service)],
    prediction_repo: Annotated[PredictionRepository, Depends(get_prediction_repo)],
    image: UploadFile = File(...),
    lat: float | None = Form(default=None),
    lon: float | None = Form(default=None),
    address: str | None = Form(default=None),
    farm_id: int | None = Form(default=None),
):
    _, saved_path = await save_upload(image, settings.upload_path, settings.max_upload_bytes)
    rel_path = (
        str(saved_path.relative_to(settings.repo_root))
        if saved_path.is_relative_to(settings.repo_root)
        else str(saved_path)
    )

    results = analysis_service.complete_analysis(str(saved_path), lat, lon, address)

    record = prediction_repo.create_prediction(
        db,
        current_user.id,
        rel_path,
        results["disease"]["predictions"],
        farm_id=farm_id,
    )

    weather = results["weather"]
    location = {}
    if isinstance(weather, dict) and not weather.get("skipped"):
        location = weather.get("location", {})
        prediction_repo.create_weather_analysis(db, record.id, location, weather)

    prediction_repo.create_analysis_report(
        db,
        record.id,
        current_user.id,
        results["disease"],
        results["treatment"],
        weather if isinstance(weather, dict) else None,
        results["combined"],
    )

    return CompleteAnalysisResponse(
        prediction_id=record.id,
        disease=results["disease"],
        treatment=results["treatment"],
        weather=weather,
        combined=results["combined"],
    )


@router.post("/ai-report", response_model=AIReportResponse)
async def get_ai_report(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
    ai_analysis_service: Annotated[AIAnalysisService, Depends(get_ai_analysis_service)],
    prediction_repo: Annotated[PredictionRepository, Depends(get_prediction_repo)],
    image: UploadFile = File(...),
    lat: float | None = Form(default=None),
    lon: float | None = Form(default=None),
    address: str | None = Form(default=None),
    farm_id: int | None = Form(default=None),
):
    _, saved_path = await save_upload(image, settings.upload_path, settings.max_upload_bytes)
    rel_path = (
        str(saved_path.relative_to(settings.repo_root))
        if saved_path.is_relative_to(settings.repo_root)
        else str(saved_path)
    )

    results = ai_analysis_service.complete_ai_analysis(str(saved_path), lat, lon, address)

    record = prediction_repo.create_prediction(
        db,
        current_user.id,
        rel_path,
        results["disease"]["predictions"],
        farm_id=farm_id,
    )

    weather = results["weather"]
    location = {}
    if isinstance(weather, dict) and not weather.get("skipped"):
        location = weather.get("location", {})
        prediction_repo.create_weather_analysis(db, record.id, location, weather)

    prediction_repo.create_analysis_report(
        db,
        record.id,
        current_user.id,
        results["disease"],
        results["treatment"],
        weather if isinstance(weather, dict) else None,
        results["combined"],
    )

    return AIReportResponse(
        prediction_id=record.id,
        disease=results["disease"],
        treatment=results["treatment"],
        weather=weather,
        combined=results["combined"],
        ai_report=results.get("ai_report"),
    )

