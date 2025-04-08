"""DB에 관련된 로직 처리하는 서비스 클래스 작성

HeroService 클래스는 Hero 객체의 생성, 조회, 수정, 삭제와 같은 데이터베이스 관련 작업을 처리합니다.
레포지토리 관련 로직은 app/src/heroes/hero_repository.py에 작성하시길 바랍니다.
"""

from typing import List

from app.dependencies import SessionDep
from app.exceptions.service import HeroNotFoundError
from app.schemas.heroes import HeroCreate, Hero
from app.src.heroes.hero_repository import HeroRepositoryInterface


class HeroService:
    """Hero 서비스 클래스

    이 클래스는 Hero 객체의 비즈니스 로직을 처리합니다.
    """

    def __init__(self, repository: HeroRepositoryInterface):
        """Hero 서비스 생성자

        Args:
            repository (HeroRepositoryInterface): Hero Repository Interface
        """
        self.repository = repository

    def create_hero(self, db: SessionDep, hero: HeroCreate) -> Hero:
        """새로운 Hero 객체를 생성합니다.

        Args:
            db (SessionDep): 데이터베이스 세션
            hero (HeroCreate): 생성할 Hero 객체의 데이터

        Returns:
            Hero: 생성된 Hero 객체
        """
        return self.repository.create_hero(db, hero)

    def get_heroes(self, db: SessionDep, skip: int = 0, limit: int = 10) -> List[Hero]:
        """Hero 객체 목록을 조회합니다.

        Args:
            db (SessionDep): 데이터베이스 세션
            skip (int, optional): 조회를 시작할 오프셋. 기본값은 0.
            limit (int, optional): 조회할 최대 객체 수. 기본값은 10.

        Returns:
            List[Hero]: 조회된 Hero 객체 목록
        """
        return self.repository.get_heroes(db, skip, limit)

    def get_hero(self, db: SessionDep, hero_id: int) -> Hero:
        """주어진 ID에 해당하는 Hero 객체를 조회합니다.

        Args:
            db (SessionDep): 데이터베이스 세션
            hero_id (int): 조회할 Hero 객체의 ID

        Returns:
            Hero: 조회된 Hero 객체

        Raises:
            HeroNotFoundError: 주어진 ID에 해당하는 Hero 객체가 없을 때 발생
        """
        hero = self.repository.get_hero(db, hero_id)
        if hero is None:
            raise HeroNotFoundError(hero_id=hero_id)
        return hero

    def update_hero(self, db: SessionDep, hero_id: int, hero: HeroCreate):
        """주어진 ID에 해당하는 Hero 객체를 수정합니다.

        Args:
            db (SessionDep): 데이터베이스 세션
            hero_id (int): 수정할 Hero 객체의 ID
            hero (HeroCreate): 수정할 데이터

        Returns:
            Hero: 수정된 Hero 객체
        """
        return self.repository.update_hero(db, hero_id, hero)

    def delete_hero(self, db: SessionDep, hero_id: int):
        """주어진 ID에 해당하는 Hero 객체를 삭제합니다.

        Args:
            db (SessionDep): 데이터베이스 세션
            hero_id (int): 삭제할 Hero 객체의 ID

        Returns:
            Hero: 삭제된 Hero 객체
        """
        return self.repository.delete_hero(db, hero_id)
