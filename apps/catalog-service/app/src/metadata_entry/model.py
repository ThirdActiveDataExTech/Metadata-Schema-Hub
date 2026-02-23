from active_metadata.models import MetadataBase


class MetadataEntry(MetadataBase, table=True):  # type: ignore
    """실제 DB 테이블 모델."""

    __tablename__ = "metadata_entry"  # type: ignore
