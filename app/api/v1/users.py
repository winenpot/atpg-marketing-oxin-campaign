from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    get_authentication_service,
    get_current_user,
    get_passport_service,
    get_redemption_service,
    get_wallet_service,
)
from app.api.v1.schemas import (
    PassportProgressResponse,
    RedeemCodeRequest,
    RedeemResponse,
    UserResponse,
    UserUpdate,
    WalletResponse,
)
from app.application.authentication import AuthenticationService
from app.application.passports import PassportService
from app.application.redemption_codes import (
    RedemptionError,
    RedemptionFailure,
    RedemptionService,
)
from app.application.wallets import WalletService
from app.domain.users import User

router = APIRouter(tags=["users"])

_REDEMPTION_ERRORS: dict[RedemptionFailure, tuple[int, str]] = {
    RedemptionFailure.INVALID: (
        status.HTTP_400_BAD_REQUEST,
        "This code is not valid.",
    ),
    RedemptionFailure.MISTYPED: (
        status.HTTP_400_BAD_REQUEST,
        "This code looks mistyped. Check each character and try again.",
    ),
    RedemptionFailure.ALREADY_REDEEMED: (
        status.HTTP_409_CONFLICT,
        "This code has already been used.",
    ),
    RedemptionFailure.UNAVAILABLE: (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Redemption is temporarily unavailable.",
    ),
}


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


@router.post("/me/redeem", response_model=RedeemResponse)
async def redeem_code(
    payload: RedeemCodeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[RedemptionService, Depends(get_redemption_service)],
) -> RedeemResponse:
    try:
        outcome = await service.redeem(current_user.id, payload.code)
    except RedemptionError as error:
        status_code, message = _REDEMPTION_ERRORS[error.failure]
        raise HTTPException(
            status_code=status_code,
            detail={"code": error.failure.value, "message": message},
        ) from error
    return RedeemResponse.from_outcome(outcome)


@router.get("/me/wallet", response_model=WalletResponse)
async def get_my_wallet(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletResponse:
    return WalletResponse.from_summary(await service.summary(current_user.id))
