"""DB 관련된 로직을 처리하는 레포지토리 클래스 작성

서비스 관련 로직은 app/src/heroes/hero_service.py에 작성하시길 바랍니다.
"""

from abc import abstractmethod, ABC
from typing import Optional, List

from sqlmodel import Session, select

from app.dependencies import SessionDep
from app.exceptions.service import HeroNotFoundError
from app.schemas.heroes import Hero, HeroCreate


class HeroRepositoryInterface(ABC):
    """Hero 레포지토리 인터페이스 클래스

    이 클래스는 Hero 객체의 데이터베이스 작업을 위한 인터페이스를 정의합니다.
    """

    @abstractmethod
    def create_hero(self, db: Session, hero: HeroCreate) -> Hero:
        """Hero 객체를 생성합니다.

        Args:
            db (Session): 데이터베이스 세션
            hero (HeroCreate): 생성할 Hero 객체의 데이터

        Returns:
            Hero: 생성된 Hero 객체
        """
        pass

    @abstractmethod
    def get_heroes(self, db: Session, offset: int = 0, limit: int = 100) -> List[Hero]:
        """Hero 객체 목록을 조회합니다.

        Args:
            db (Session): 데이터베이스 세션
            offset (int, optional): 조회를 시작할 오프셋. 기본값은 0.
            limit (int, optional): 조회할 최대 객체 수. 기본값은 100.

        Returns:
            List[Hero]: 조회된 Hero 객체 목록
        """
        pass

    @abstractmethod
    def get_hero(self, db: Session, hero_id: int) -> Optional[Hero]:
        """주어진 ID에 해당하는 Hero 객체를 조회합니다.

        Args:
            db (Session): 데이터베이스 세션
            hero_id (int): 조회할 Hero 객체의 ID

        Returns:
            Optional[Hero]: 조회된 Hero 객체, 없을 경우 None
        """
        pass

    @abstractmethod
    def update_hero(self, db: Session, hero_id: int, hero: HeroCreate) -> Optional[Hero]:
        """주어진 ID에 해당하는 Hero 객체를 수정합니다.

        Args:
            db (Session): 데이터베이스 세션
            hero_id (int): 수정할 Hero 객체의 ID
            hero (HeroCreate): 수정할 데이터

        Returns:
            Optional[Hero]: 수정된 Hero 객체, 없을 경우 None
        """
        pass

    @abstractmethod
    def delete_hero(self, db: Session, hero_id: int) -> Optional[Hero]:
        """주어진 ID에 해당하는 Hero 객체를 삭제합니다.

        Args:
            db (Session): 데이터베이스 세션
            hero_id (int): 삭제할 Hero 객체의 ID

        Returns:
            Optional[Hero]: 삭제된 Hero 객체, 없을 경우 None
        """
        pass


class SQLiteHeroRepository(HeroRepositoryInterface):
    """SQLite Hero 레포지토리 클래스

    이 클래스는 SQLite 데이터베이스를 사용하여 Hero 객체의 데이터베이스 작업을 처리합니다.
    """

    def create_hero(self, db: SessionDep, hero: HeroCreate) -> Hero:
        """Hero 객체를 생성합니다.

        Args:
            db (SessionDep): 데이터베이스 세션
            hero (HeroCreate): 생성할 Hero 객체의 데이터

        Returns:
            Hero: 생성된 Hero 객체
        """
        db_hero = Hero.model_validate(hero)
        db.add(db_hero)
        db.commit()
        db.refresh(db_hero)
        return db_hero

    def get_heroes(self, db: SessionDep, offset: int = 0, limit: int = 100) -> List[Hero]:
        """Hero 객체 목록을 조회합니다.

        Args:
            db (SessionDep): 데이터베이스 세션
            offset (int, optional): 조회를 시작할 오프셋. 기본값은 0.
            limit (int, optional): 조회할 최대 객체 수. 기본값은 100.

        Returns:
            List[Hero]: 조회된 Hero 객체 목록
        """
        return list(db.exec(select(Hero).offset(offset).limit(limit)).all())

    def get_hero(self, db: SessionDep, hero_id: int) -> Optional[Hero]:
        """주어진 ID에 해당하는 Hero 객체를 조회합니다.

        Args:
            db (SessionDep): 데이터베이스 세션
            hero_id (int): 조회할 Hero 객체의 ID

        Returns:
            Optional[Hero]: 조회된 Hero 객체, 없을 경우 None
        """
        return db.get(Hero, hero_id)

    def update_hero(self, db: SessionDep, hero_id: int, hero: HeroCreate) -> Optional[Hero]:
        """주어진 ID에 해당하는 Hero 객체를 수정합니다.

        Args:
            db (SessionDep): 데이터베이스 세션
            hero_id (int): 수정할 Hero 객체의 ID
            hero (HeroCreate): 수정할 데이터

        Returns:
            Optional[Hero]: 수정된 Hero 객체, 없을 경우 None

        Raises:
            HeroNotFoundError: 주어진 ID에 해당하는 Hero 객체가 없을 때 발생
        """
        hero_db = db.get(Hero, hero_id)
        if not hero_db:
            raise HeroNotFoundError(hero_id)
        hero_data = hero.model_dump(exclude_unset=True)
        hero_db.sqlmodel_update(hero_data)
        db.add(hero_db)
        db.commit()
        db.refresh(hero_db)
        return hero_db

    def delete_hero(self, db: SessionDep, hero_id: int) -> Optional[Hero]:
        """주어진 ID에 해당하는 Hero 객체를 삭제합니다.

        Args:
            db (SessionDep): 데이터베이스 세션
            hero_id (int): 삭제할 Hero 객체의 ID

        Returns:
            Optional[Hero]: 삭제된 Hero 객체, 없을 경우 None

        Raises:
            HeroNotFoundError: 주어진 ID에 해당하는 Hero 객체가 없을 때 발생
        """
        hero = db.get(Hero, hero_id)
        if not hero:
            raise HeroNotFoundError(hero_id)
        db.delete(hero)
        db.commit()
        return hero
