"""SQLModel schemas for the Hero model.

참고: https://fastapi.tiangolo.com/ko/tutorial/sql-databases/
"""

from typing import Optional

from sqlmodel import Field, SQLModel


class HeroBase(SQLModel):
    """공통 필드를 정의한 베이스 모델"""
    name: str = Field(index=True, min_length=1, max_length=100)
    age: Optional[int] = Field(default=None, index=True, ge=0, le=1000)


class Hero(HeroBase, table=True):
    """실제 DB 테이블 모델"""
    id: Optional[int] = Field(default=None, primary_key=True)
    secret_name: str


class HeroPublic(HeroBase):
    """공개 데이터 모델\n

    API 클라이언트에 반환되는 모델.\n

    역할:\n
    - HeroCreate로 생성하고 HeroPublic 반환하기\n
    - HeroPublic으로 Heroes 조회하기\n
    - HeroPublic으로 단일 Hero 조회하기
    """
    id: int


class HeroCreate(HeroBase):
    """생성용 데이터 모델\n

    클라이언트로부터 받은 데이터를 검증하는 역할.\n

    클라이언트가 새 hero를 생성할 때 secret_name을 보내고, 이는 데이터베이스에 저장되지만,\n
    해당 secret_name은 API를 통해 클라이언트에게 반환되지 않음.
    """
    secret_name: str


class HeroUpdate(SQLModel):
    """수정용 데이터 모델\n

    HeroBase와 동일한 필드를 가지지만 모든 필드의 조건이 변경되어 재설정해야되기 때문에(타입 None 포함 및 기본값 None 설정) HeroBase를 상속하지 않음.\n
    따라서 새로 선언한 HeroUpdate 모델을 통해 hero를 수정할 때, 전체 필드가 아닌 부분적으로 필드 업데이트 가능함.

    역할:\n
    - HeroUpdate로 Hero 수정하기
    """
    name: Optional[str] = Field(index=True, min_length=1, max_length=100)
    age: Optional[int] = Field(default=None, index=True, ge=0, le=1000)
    secret_name: Optional[str] = Field(default=None, min_length=0, max_length=1000)
