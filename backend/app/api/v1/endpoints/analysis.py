from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
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
from backend.app.schemas import CompleteAnalysisResponse, WeatherAnalysisRequest, AIReportResponse, YieldPredictionRequest, YieldPredictionResponse
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
    has_coords = payload.lat is not None and payload.lon is not None
    has_address = bool((payload.address or "").strip())

    if payload.lat is not None and payload.lon is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Both latitude and longitude must be provided together.",
        )
    if payload.lon is not None and payload.lat is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Both latitude and longitude must be provided together.",
        )
    if not has_coords and not has_address:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Location is required: provide both latitude and longitude, or a non-empty address.",
        )

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

    results = await ai_analysis_service.complete_ai_analysis(str(saved_path), lat, lon, address)

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
        ai_report_source=results.get("ai_report_source"),
        timings=results.get("timings"),
    )


@router.post("/yield", response_model=YieldPredictionResponse)
def predict_yield(
    payload: YieldPredictionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    crop_lower = payload.crop.lower()
    # Define optimal ranges based on crop
    if "tomato" in crop_lower:
        opt_ph = (6.0, 6.8)
        opt_n = (120.0, 160.0)
        opt_p = (40.0, 60.0)
        opt_k = (160.0, 220.0)
        avg_yield = 4.2
    elif "potato" in crop_lower:
        opt_ph = (5.0, 6.0)
        opt_n = (100.0, 140.0)
        opt_p = (35.0, 50.0)
        opt_k = (140.0, 190.0)
        avg_yield = 3.8
    else:
        opt_ph = (6.0, 7.0)
        opt_n = (110.0, 150.0)
        opt_p = (35.0, 55.0)
        opt_k = (150.0, 200.0)
        avg_yield = 4.0

    def score_factor(val, opt):
        if opt[0] <= val <= opt[1]:
            return 1.0
        elif val < opt[0]:
            return max(0.4, 1.0 - (opt[0] - val) / opt[0])
        else:
            return max(0.4, 1.0 - (val - opt[1]) / opt[1])

    # Calculate individual factors
    f_ph = score_factor(payload.soil_ph, opt_ph)
    f_n = score_factor(payload.nitrogen, opt_n)
    f_p = score_factor(payload.phosphorus, opt_p)
    f_k = score_factor(payload.potassium, opt_k)

    # Average score
    score = (f_ph + f_n + f_p + f_k) / 4.0

    estimated_yield = round(avg_yield * (0.6 + 0.4 * score), 1)
    confidence = round(85.0 + 10.0 * score, 1)

    if score > 0.85:
        risk = "Low Risk"
    elif score > 0.6:
        risk = "Medium Risk"
    else:
        risk = "High Risk"

    return YieldPredictionResponse(
        estimated_yield=estimated_yield,
        confidence=confidence,
        risk_assessment=risk,
        comparisons=[
            {"plot": "Plot A", "projected": estimated_yield, "average": avg_yield},
            {"plot": "Plot B", "projected": round(estimated_yield * 1.08, 1), "average": round(avg_yield * 1.03, 1)},
            {"plot": "Plot C", "projected": round(estimated_yield * 0.93, 1), "average": round(avg_yield * 0.98, 1)},
        ]
    )


