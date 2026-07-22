import logging

from fastapi import APIRouter
from sqlalchemy import text

from backend.app.core.config import get_settings
from backend.app.db.session import engine
from backend.app.ml.disease_inference import DiseaseInferenceService

logger = logging.getLogger(__name__)

router = APIRouter()


def _database_status() -> str:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "available"
    except Exception as exc:  # noqa: BLE001
        logger.error("Health check: database unavailable: %s", exc)
        return "unavailable"


def _dl_model_status() -> str:
    instance = getattr(DiseaseInferenceService, "_instance", None)
    if instance is None:
        return "not_loaded"
    return "available" if getattr(instance, "predictor", None) is not None else "mock_fallback"


def _search_status() -> str:
    try:
        from duckduckgo_search import DDGS  # noqa: F401

        return "available"
    except Exception:  # noqa: BLE001
        return "unavailable"


@router.get("/health")
def health_check():
    settings = get_settings()

    database = _database_status()
    dl_model = _dl_model_status()
    weather_service = "available" if settings.OPENWEATHER_API_KEY else "unavailable"
    llm = "available" if settings.LLM_API_KEY else "unavailable"
    search = _search_status()

    # Only the database is a hard dependency for the demo.
    status = "ok" if database == "available" else "degraded"

    return {
        "status": status,
        "service": "agriforge-api",
        "database": database,
        "dl_model": dl_model,
        "weather_service": weather_service,
        "llm": llm,
        "search": search,
    }
