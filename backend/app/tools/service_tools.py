import json
import logging
from typing import Type, Any, Optional

from pydantic import BaseModel, Field, PrivateAttr
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class DiseaseToolInput(BaseModel):
    image_path: str = Field(description="The path to the image to analyze.")


class DiseasePredictionTool(BaseTool):
    name: str = "disease_prediction"
    description: str = "Runs the deterministic Deep Learning disease model on an image path."
    args_schema: Type[BaseModel] = DiseaseToolInput
    
    _disease_service: Any = PrivateAttr()

    def __init__(self, disease_service: Any, **kwargs):
        super().__init__(**kwargs)
        self._disease_service = disease_service
    
    def _run(self, image_path: str) -> str:
        if not self._disease_service:
            return json.dumps({"error": "Disease prediction service is not available."})
        try:
            results = self._disease_service.predict_disease(image_path)
            return json.dumps(results, default=str)
        except Exception as e:
            logger.error(f"Error running disease prediction: {e}")
            return json.dumps({"error": f"Failed to run disease prediction: {e}"})


class WeatherToolInput(BaseModel):
    crop: str = Field(description="The crop name.")
    disease: str = Field(description="The predicted disease name.")
    confidence: float = Field(description="The confidence of the disease prediction.")
    lat: Optional[float] = Field(default=None, description="Latitude.")
    lon: Optional[float] = Field(default=None, description="Longitude.")
    address: Optional[str] = Field(default=None, description="Location address.")


class WeatherAnalysisTool(BaseTool):
    name: str = "weather_analysis"
    description: str = "Analyzes the current weather and its impact on the specified crop and disease."
    args_schema: Type[BaseModel] = WeatherToolInput
    
    _weather_service: Any = PrivateAttr()

    def __init__(self, weather_service: Any, **kwargs):
        super().__init__(**kwargs)
        self._weather_service = weather_service

    def _run(self, crop: str, disease: str, confidence: float, lat: Optional[float] = None, lon: Optional[float] = None, address: Optional[str] = None) -> str:
        if not self._weather_service:
            return json.dumps({"error": "Weather analysis service is not available."})
        try:
            results = self._weather_service.analyze(crop, disease, confidence, lat, lon, address)
            return json.dumps(results, default=str)
        except Exception as e:
            logger.error(f"Error analyzing weather: {e}")
            return json.dumps({"error": f"Failed to analyze weather: {e}"})


class TreatmentToolInput(BaseModel):
    crop: str = Field(description="The crop name.")
    disease: str = Field(description="The disease name.")


class TreatmentKnowledgeTool(BaseTool):
    name: str = "treatment_knowledge"
    description: str = "Retrieves local deterministic treatment and prevention knowledge for a specific crop and disease."
    args_schema: Type[BaseModel] = TreatmentToolInput
    
    _treatment_service: Any = PrivateAttr()

    def __init__(self, treatment_service: Any, **kwargs):
        super().__init__(**kwargs)
        self._treatment_service = treatment_service

    def _run(self, crop: str, disease: str) -> str:
        if not self._treatment_service:
            return json.dumps({"error": "Treatment knowledge service is not available."})
        try:
            results = self._treatment_service.get_treatment(crop, disease)
            return json.dumps(results, default=str)
        except Exception as e:
            logger.error(f"Error retrieving treatment knowledge: {e}")
            return json.dumps({"error": f"Failed to retrieve treatment knowledge: {e}"})


class HistoryToolInput(BaseModel):
    farm_id: int = Field(description="The ID of the farm to retrieve history for.")
    limit: int = Field(default=5, description="Number of past predictions to retrieve.")


class PredictionHistoryTool(BaseTool):
    name: str = "prediction_history"
    description: str = "Retrieves relevant existing database history for a specific farm."
    args_schema: Type[BaseModel] = HistoryToolInput
    
    _prediction_repo: Any = PrivateAttr()
    _db: Any = PrivateAttr()

    def __init__(self, prediction_repo: Any, db: Any, **kwargs):
        super().__init__(**kwargs)
        self._prediction_repo = prediction_repo
        self._db = db

    def _run(self, farm_id: int, limit: int = 5) -> str:
        if not self._prediction_repo or not self._db:
            return json.dumps({"error": "Prediction history repository or database session is not available."})
        try:
            # Repository mapping for history retrieval needs to be implemented natively in PredictionRepository.
            # We return a structured placeholder so the LLM agent does not hallucinate a failure trace.
            return json.dumps({
                "farm_id": farm_id,
                "message": "History retrieval logic is pending concrete repository mapping."
            })
        except Exception as e:
            logger.error(f"Error retrieving history: {e}")
            return json.dumps({"error": f"Failed to retrieve history: {e}"})
