from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farms: Mapped[list["Farm"]] = relationship(back_populates="owner")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="user")
    analysis_reports: Mapped[list["AnalysisReport"]] = relationship(back_populates="user")


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="farms")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="farm")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    farm_id: Mapped[int | None] = mapped_column(ForeignKey("farms.id"), nullable=True, index=True)
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    primary_plant: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_disease: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    predictions_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="predictions")
    farm: Mapped["Farm | None"] = relationship(back_populates="predictions")
    weather_analysis: Mapped["WeatherAnalysis | None"] = relationship(
        back_populates="prediction", uselist=False
    )
    analysis_report: Mapped["AnalysisReport | None"] = relationship(
        back_populates="prediction", uselist=False
    )


class WeatherAnalysis(Base):
    __tablename__ = "weather_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), unique=True, nullable=False)
    location_json: Mapped[str] = mapped_column(Text, nullable=False)
    weather_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prediction: Mapped["Prediction"] = relationship(back_populates="weather_analysis")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    disease_result: Mapped[str] = mapped_column(Text, nullable=False)
    treatment_result: Mapped[str] = mapped_column(Text, nullable=False)
    weather_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    combined_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prediction: Mapped["Prediction"] = relationship(back_populates="analysis_report")
    user: Mapped["User"] = relationship(back_populates="analysis_reports")
