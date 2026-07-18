from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_current_user
from backend.app.models import User
from backend.app.schemas import UserRead

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
