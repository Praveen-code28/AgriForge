from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_farm_repo
from backend.app.db.session import get_db
from backend.app.models import User
from backend.app.repositories.farm_repository import FarmRepository
from backend.app.schemas import FarmCreate, FarmRead

router = APIRouter()


@router.post("", response_model=FarmRead, status_code=status.HTTP_201_CREATED)
def create_farm(
    payload: FarmCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    farm_repo: Annotated[FarmRepository, Depends(get_farm_repo)],
):
    return farm_repo.create(db, current_user.id, **payload.model_dump())


@router.get("", response_model=list[FarmRead])
def list_farms(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    farm_repo: Annotated[FarmRepository, Depends(get_farm_repo)],
):
    return farm_repo.list_for_user(db, current_user.id)


@router.get("/{farm_id}", response_model=FarmRead)
def get_farm(
    farm_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    farm_repo: Annotated[FarmRepository, Depends(get_farm_repo)],
):
    farm = farm_repo.get_for_user(db, current_user.id, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm
