"""In-memory SQLite database for testing"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from app.schemas.heroes import HeroCreate
from app.src.heroes.hero_repository import SQLiteHeroRepository


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="repository")
def repository_fixture():
    return SQLiteHeroRepository()


def test_create_hero(session, repository):
    hero_create = HeroCreate(name="Test Hero", age=30, secret_name="Secret")
    hero = repository.create_hero(session, hero_create)
    assert hero.id is not None
    assert hero.name == "Test Hero"
    assert hero.age == 30
    assert hero.secret_name == "Secret"


def test_get_heroes(session, repository):
    hero_create = HeroCreate(name="Test Hero", age=30, secret_name="Secret")
    repository.create_hero(session, hero_create)
    heroes = repository.get_heroes(session)
    assert len(heroes) == 1
    assert heroes[0].name == "Test Hero"


def test_get_hero(session, repository):
    hero_create = HeroCreate(name="Test Hero", age=30, secret_name="Secret")
    created_hero = repository.create_hero(session, hero_create)
    hero = repository.get_hero(session, created_hero.id)
    assert hero is not None
    assert hero.name == "Test Hero"


def test_update_hero(session, repository):
    hero_create = HeroCreate(name="Test Hero", age=30, secret_name="Secret")
    created_hero = repository.create_hero(session, hero_create)
    hero_update = HeroCreate(name="Updated Hero", age=35, secret_name="Updated Secret")
    updated_hero = repository.update_hero(session, created_hero.id, hero_update)
    assert updated_hero.name == "Updated Hero"
    assert updated_hero.age == 35
    assert updated_hero.secret_name == "Updated Secret"
