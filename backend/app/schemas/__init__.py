from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None


class FarmBase(BaseModel):
    name: str
    location_lat: float | None = None
    location_lon: float | None = None
    address: str | None = None


class FarmCreate(FarmBase):
    pass


class FarmRead(FarmBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


class PredictionCandidate(BaseModel):
    plant: str
    disease: str
    confidence: float
    remedy: str | None = None


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_path: str
    primary_plant: str
    primary_disease: str
    primary_confidence: float
    predictions: list[PredictionCandidate]
    created_at: str


class PaginatedPredictions(BaseModel):
    items: list[PredictionRead]
    total: int
    page: int
    page_size: int


class WeatherAnalysisRequest(BaseModel):
    crop: str
    disease: str
    confidence: float = Field(ge=0, le=1)
    lat: float | None = None
    lon: float | None = None
    address: str | None = None


class CompleteAnalysisResponse(BaseModel):
    prediction_id: int
    disease: dict
    treatment: dict
    weather: dict | None
    combined: dict


class SupportedCropInfo(BaseModel):
    crop: str
    diseases: list[str]


class SupportedCropsResponse(BaseModel):
    crops: list[SupportedCropInfo]
    ood_limitation: str


from .ai_report import (
    AIReport,
    AIReportDisease,
    AIReportRisk,
    AIReportSource,
    AIReportTreatment,
    AIReportWeather,
)


class AIReportResponse(BaseModel):
    prediction_id: int
    disease: dict
    treatment: dict
    weather: dict | None
    combined: dict
    ai_report: AIReport | dict | None
