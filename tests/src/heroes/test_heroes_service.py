import re

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlmodel import SQLModel, Session

from app.exceptions.service import HeroNotFoundError
from app.schemas.heroes import HeroCreate
from app.src.heroes.hero_repository import SQLiteHeroRepository
from app.src.heroes.hero_service import HeroService


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="service")
def service_fixture(repository):
    return HeroService(repository)


@pytest.fixture(name="repository")
def repository_fixture():
    return SQLiteHeroRepository()


def test_delete_hero(session, repository, service):
    """service.delete_hero 테스트"""
    hero_create = HeroCreate(name="Test Hero", age=30, secret_name="Secret")
    created_hero = service.create_hero(session, hero_create)
    assert created_hero.id is not None, f"{created_hero=}"

    deleted_hero = service.delete_hero(session, created_hero.id)
    assert deleted_hero is not None
    print(f"{deleted_hero=}")

    with pytest.raises(HeroNotFoundError) as not_found_exc:
        service.get_hero(session, created_hero.id)
    assert re.search("not ?found", not_found_exc.value.message.lower())
