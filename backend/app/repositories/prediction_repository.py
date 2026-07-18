import json
import logging
from typing import Any, List, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models import AnalysisReport, Prediction, WeatherAnalysis

logger = logging.getLogger(__name__)


class PredictionRepository:
    """
    Handles database operations for Predictions, Weather Analyses, and AI Reports.
    All methods expect an active SQLAlchemy session.
    """

    def create_prediction(
        self,
        db: Session,
        user_id: int,
        image_path: str,
        predictions: List[dict],
        farm_id: Optional[int] = None,
    ) -> Optional[Prediction]:
        # Safely extract the primary prediction if the list is not empty
        primary = predictions[0] if predictions else {}
        
        record = Prediction(
            user_id=user_id,
            farm_id=farm_id,
            image_path=image_path,
            primary_plant=primary.get("plant", "Unknown"),
            primary_disease=primary.get("disease", "Unknown"),
            primary_confidence=primary.get("confidence", 0.0),
            predictions_json=json.dumps(predictions, default=str),
        )
        try:
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to create prediction: {e}")
            raise

    def get_by_id(self, db: Session, user_id: int, prediction_id: int) -> Optional[Prediction]:
        try:
            return (
                db.query(Prediction)
                .filter(
                    Prediction.user_id == user_id, 
                    Prediction.id == prediction_id
                )
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch prediction by id {prediction_id}: {e}")
            return None

    def list_paginated(
        self, db: Session, user_id: int, page: int, page_size: int
    ) -> Tuple[List[Prediction], int]:
        try:
            query = db.query(Prediction).filter(Prediction.user_id == user_id)
            total = query.count()
            
            # Ensure page is at least 1 to avoid negative offset bugs
            safe_page = max(1, page)
            
            items = (
                query.order_by(Prediction.created_at.desc())
                .offset((safe_page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            return items, total
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch paginated predictions: {e}")
            return [], 0

    def create_weather_analysis(
        self, db: Session, prediction_id: int, location: dict, weather: dict
    ) -> Optional[WeatherAnalysis]:
        record = WeatherAnalysis(
            prediction_id=prediction_id,
            location_json=json.dumps(location, default=str),
            weather_json=json.dumps(weather, default=str),
        )
        try:
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to create weather analysis: {e}")
            raise

    def create_analysis_report(
        self,
        db: Session,
        prediction_id: int,
        user_id: int,
        disease_result: dict,
        treatment_result: dict,
        weather_result: Optional[dict],
        combined: dict,
    ) -> Optional[AnalysisReport]:
        record = AnalysisReport(
            prediction_id=prediction_id,
            user_id=user_id,
            disease_result=json.dumps(disease_result, default=str),
            treatment_result=json.dumps(treatment_result, default=str),
            weather_result=json.dumps(weather_result, default=str) if weather_result else None,
            combined_json=json.dumps(combined, default=str),
        )
        try:
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to create analysis report: {e}")
            raise
