"""DB 예시 라우터 작성"""

from typing import Annotated

from fastapi import Query, APIRouter, Depends, Path

from app.dependencies import SessionDep
from app.schemas.heroes import HeroCreate, HeroUpdate
from app.schemas.response import APIResponseModel
from app.src.heroes.hero_repository import SQLiteHeroRepository
from app.src.heroes.hero_service import HeroService

router = APIRouter(
    prefix="/heroes",
    tags=["heroes"]
)


def get_hero_service(repo=Depends(SQLiteHeroRepository)):
    """Repository dependency injection."""
    return HeroService(repo)


@router.post("", response_model=APIResponseModel)
def create_hero(
        hero: HeroCreate,
        session: SessionDep,
        service: HeroService = Depends(get_hero_service)
):
    db_hero = service.create_hero(session, hero)
    return APIResponseModel(result=db_hero, description="Hero created")


@router.get("", response_model=APIResponseModel)
def read_heroes(
        session: SessionDep,
        service: HeroService = Depends(get_hero_service),
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100
):
    heroes = service.get_heroes(session, offset, limit)
    return APIResponseModel(result=heroes, description="Heroes found")


@router.get("/{hero_id}", response_model=APIResponseModel)
def read_hero(
        session: SessionDep,
        service: HeroService = Depends(get_hero_service),
        hero_id: int = Path(description="조회할 영웅의 ID", ge=1, le=1000, title="Hero ID", examples=[123])
):
    hero = service.get_hero(session, hero_id)
    return APIResponseModel(result=hero, description="Hero found")


@router.patch("/{hero_id}", response_model=APIResponseModel)
def update_hero(
        hero: HeroUpdate,
        session: SessionDep,
        service: HeroService = Depends(get_hero_service),
        hero_id: int = Path(description="조회할 영웅의 ID", ge=1, le=1000, title="Hero ID", examples=[123])
):
    hero_db = service.update_hero(session, hero_id, hero)
    return APIResponseModel(result=hero_db, description="Hero updated")


@router.delete("/{hero_id}", response_model=APIResponseModel)
def delete_hero(
        session: SessionDep,
        service: HeroService = Depends(get_hero_service),
        hero_id: int = Path(description="조회할 영웅의 ID", ge=1, le=1000, title="Hero ID", examples=[123])
):
    hero = service.delete_hero(session, hero_id)
    return APIResponseModel(result=hero, description="Hero deleted")
