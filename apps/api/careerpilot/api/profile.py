from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from careerpilot.db.session import get_db
from careerpilot.repositories import CareerProfileRepository
from careerpilot.schemas import CareerProfileCreate, CareerProfileRead, CareerProfileUpdate
from careerpilot.services.profile import CareerProfileService, ProfileAlreadyExistsError

router = APIRouter(prefix="/profile", tags=["profile"])


def get_profile_service(session: Annotated[Session, Depends(get_db)]) -> CareerProfileService:
    return CareerProfileService(CareerProfileRepository(session))


ProfileService = Annotated[CareerProfileService, Depends(get_profile_service)]


def get_or_404(service: CareerProfileService) -> CareerProfileRead:
    try:
        return CareerProfileRead.model_validate(service.get())
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("", response_model=CareerProfileRead)
def get_profile(service: ProfileService) -> CareerProfileRead:
    return get_or_404(service)


@router.get("/full", response_model=CareerProfileRead)
def get_full_profile(service: ProfileService) -> CareerProfileRead:
    return get_or_404(service)


@router.post("", response_model=CareerProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(payload: CareerProfileCreate, service: ProfileService) -> CareerProfileRead:
    try:
        return CareerProfileRead.model_validate(service.create(payload))
    except ProfileAlreadyExistsError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.patch("", response_model=CareerProfileRead)
def update_profile(payload: CareerProfileUpdate, service: ProfileService) -> CareerProfileRead:
    try:
        return CareerProfileRead.model_validate(service.update(payload))
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
