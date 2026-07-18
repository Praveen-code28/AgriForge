from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.db.session import get_db
from backend.app.ml.crop_validation import CropValidationLayer
from backend.app.ml.disease_inference import DiseaseInferenceService
from backend.app.ml.weather_inference import WeatherInferenceService
from backend.app.models import User
from backend.app.repositories.farm_repository import FarmRepository
from backend.app.repositories.prediction_repository import PredictionRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.services.analysis_service import AnalysisService, DiseaseService, WeatherService
from backend.app.services.treatment_service import TreatmentService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_settings_dep() -> Settings:
    return get_settings()


def get_disease_inference(settings: Annotated[Settings, Depends(get_settings_dep)]) -> DiseaseInferenceService:
    model_path = settings.repo_root / settings.MODEL_PATH
    return DiseaseInferenceService.get_instance(model_path)


def get_weather_inference(settings: Annotated[Settings, Depends(get_settings_dep)]) -> WeatherInferenceService:
    kb_path = str(settings.repo_root / settings.KNOWLEDGE_BASE_PATH)
    api_key = settings.OPENWEATHER_API_KEY or None
    return WeatherInferenceService.get_instance(kb_path, api_key)


def get_treatment_service(settings: Annotated[Settings, Depends(get_settings_dep)]) -> TreatmentService:
    return TreatmentService(settings.repo_root / settings.KNOWLEDGE_BASE_PATH)


def get_disease_service(
    inference: Annotated[DiseaseInferenceService, Depends(get_disease_inference)],
) -> DiseaseService:
    return DiseaseService(inference, CropValidationLayer())


def get_weather_service(
    inference: Annotated[WeatherInferenceService, Depends(get_weather_inference)],
) -> WeatherService:
    return WeatherService(inference)


def get_analysis_service(
    disease_service: Annotated[DiseaseService, Depends(get_disease_service)],
    treatment_service: Annotated[TreatmentService, Depends(get_treatment_service)],
    weather_service: Annotated[WeatherService, Depends(get_weather_service)],
) -> AnalysisService:
    return AnalysisService(disease_service, treatment_service, weather_service)


def get_user_repo() -> UserRepository:
    return UserRepository()


def get_farm_repo() -> FarmRepository:
    return FarmRepository()


def get_prediction_repo() -> PredictionRepository:
    return PredictionRepository()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError):
        raise credentials_exception from None

    user = user_repo.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_ai_analysis_service(
    analysis_service: Annotated[AnalysisService, Depends(get_analysis_service)],
    db: Annotated[Session, Depends(get_db)],
    prediction_repo: Annotated[PredictionRepository, Depends(get_prediction_repo)],
) -> "AIAnalysisService":
    from backend.app.services.ai_analysis_service import AIAnalysisService
    return AIAnalysisService(analysis_service, db, prediction_repo)
