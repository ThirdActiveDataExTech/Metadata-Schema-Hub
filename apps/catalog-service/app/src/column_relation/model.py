from active_metadata.models import ColumnRelationBase


class ColumnRelation(ColumnRelationBase, table=True):  # type: ignore
    """실제 DB 테이블 모델."""

    __tablename__ = "column_relation"  # type: ignore
