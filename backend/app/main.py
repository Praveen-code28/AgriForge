from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings
from backend.app.ml.disease_inference import DiseaseInferenceService
from backend.app.ml.weather_inference import WeatherInferenceService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    model_path = settings.repo_root / settings.MODEL_PATH
    if model_path.exists():
        DiseaseInferenceService.get_instance(model_path)
    WeatherInferenceService.get_instance(
        str(settings.repo_root / settings.KNOWLEDGE_BASE_PATH),
        settings.OPENWEATHER_API_KEY or None,
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")
    return app


app = create_app()
