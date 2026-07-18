# AgriForge

AI-powered precision agriculture platform for smallholder farmers.

## Features

- **Disease detection** — EfficientNet-B0 model (13 classes: tomato + potato)
- **Treatment recommendations** — JSON knowledge base per crop/disease
- **Weather intelligence** — Rule-based analysis via OpenWeatherMap
- **Combined analysis** — Single endpoint merges DL prediction, treatment, and weather
- **JWT authentication** — User accounts with farm management
- **PostgreSQL persistence** — Predictions, weather analyses, and reports

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- OpenWeatherMap API key ([openweathermap.org](https://openweathermap.org/api))
- Trained model checkpoint at `checkpoints/agriforge_crop_health_v1.pth` (gitignored)

## Setup

```bash
# Clone and enter repo
cd AgriForge

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env          # Windows
# cp .env.example .env          # Linux/macOS
# Edit .env with your DATABASE_URL, SECRET_KEY, OPENWEATHER_API_KEY

# Create database
createdb agriforge            # or via pgAdmin

# Run migrations
alembic upgrade head

# Start API server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime (default 60) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `MODEL_PATH` | Path to `.pth` checkpoint (relative to repo root) |
| `UPLOAD_DIR` | Directory for uploaded images |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key |
| `MAX_UPLOAD_SIZE_MB` | Max image upload size |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login (OAuth2 form) |
| GET | `/api/v1/users/me` | Current user |
| POST/GET | `/api/v1/farms` | Create/list farms |
| GET | `/api/v1/farms/{id}` | Get farm |
| POST | `/api/v1/predictions/disease` | Disease prediction only |
| POST | `/api/v1/analysis/weather` | Weather analysis only |
| POST | `/api/v1/analysis/complete` | **Primary** combined analysis |
| GET | `/api/v1/predictions/history` | Paginated history |
| GET | `/api/v1/predictions/{id}` | Single prediction |
| GET | `/api/v1/metadata/supported-crops` | Supported crops + OOD note |

## Testing

```bash
pytest tests/ -v
```

Tests use mocked DL inference and weather — no checkpoint or live OpenWeather calls required.

## Known Limitations

- Model trained on **tomato and potato only**; other crops may misclassify (OOD detection stub only)
- Weather module is **rule-based**, not a trained ML model
- Model checkpoint is **not in git**; must be obtained separately
- Location geocoding uses placeholder district/state names
- `CropValidationLayer` is a stub for future OOD detection

## Project Structure

```
backend/
  app/           # FastAPI application
  disease_detection/  # DL training & inference (EfficientNet-B0)
ml/
  weather/       # Rule-based weather intelligence + knowledge JSON
checkpoints/     # Model weights (gitignored)
tests/           # Pytest suite
alembic/         # Database migrations
```

## CrewAI Next Steps

The weather summary JSON is structured for downstream CrewAI agents:

1. Wire `/api/v1/analysis/complete` response into a CrewAI orchestrator
2. Use `combined` field as agent input context
3. Add agent roles: agronomist advisor, spray scheduler, farmer communicator
4. Pass `treatment` + `weather.spray_recommendation` to scheduling agent

## License

See [LICENSE](LICENSE).
