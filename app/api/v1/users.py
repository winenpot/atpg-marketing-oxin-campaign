from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_authentication_service,
    get_current_user,
    get_passport_service,
)
from app.api.v1.schemas import (
    PassportProgressResponse,
    UserResponse,
    UserUpdate,
)
from app.application.authentication import AuthenticationService
from app.application.passports import PassportService
from app.domain.users import User

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.from_domain(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> UserResponse:
    user = await service.update_display_name(current_user.id, payload.display_name)
    return UserResponse.from_domain(user)


@router.get("/me/passports", response_model=list[PassportProgressResponse])
async def get_my_passports(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PassportService, Depends(get_passport_service)],
) -> list[PassportProgressResponse]:
    progress = await service.list_for_user(current_user.id)
    return [PassportProgressResponse.from_domain(item) for item in progress]
