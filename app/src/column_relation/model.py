from typing import Optional

from sqlmodel import SQLModel, Field


class ColumnRelationBase(SQLModel):
    """공통 필드를 정의한 베이스 모델"""
    catalog_column: str = Field(nullable=False)
    correlation: float = Field(nullable=False, ge=0.0, le=1.0)
    metadata_column: str = Field(nullable=False)

    def to_table_model(self) -> "ColumnRelation":
        """ColumnRelationBase 모델로 변환."""
        return ColumnRelation(**self.model_dump())


class ColumnRelation(ColumnRelationBase, table=True):  # type: ignore
    """실제 DB 테이블 모델."""
    __tablename__ = "column_relation"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
