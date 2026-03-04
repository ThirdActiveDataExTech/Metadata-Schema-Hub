"""Common test fixtures for catalog-service."""

import os
from datetime import date, datetime
from typing import Any, Generator  # noqa: F401
from unittest.mock import MagicMock

import pytest
from sqlalchemy import URL, create_engine
from sqlmodel import Session, SQLModel
from testcontainers.postgres import PostgresContainer

from active_metadata.models import DraftStatus
from tests.constants import (
    ENTRY_ID_1,
    ENTRY_ID_2,
    ENTRY_ID_3,
    METADATA_ID_1,
    METADATA_ID_2,
    SNAPSHOT_ID_VALID,
    SNAPSHOT_ID_VALID_ALT,
    TEST_MAPPING_VERSION,
    TEST_MAPPING_VERSION_ALT,
    TEST_SHA256,
    TEST_SHA256_ALT,
)
from app.src.catalog_entry.model import CatalogEntry, CatalogEntrySummary
from app.src.catalog_entry.service import CatalogEntryService
from app.src.catalog_entry_draft.model import CatalogEntryDraft
from app.src.catalog_entry_draft.service import CatalogEntryDraftService
from app.src.column_relation.model import ColumnRelation
from app.src.column_relation.service import ColumnRelationService
from app.src.metadata_entry.model import MetadataEntry
from app.src.metadata_entry.service import MetadataEntryService
from app.src.metadata_snapshot.model import MetadataSnapshot
from app.src.metadata_snapshot.service import MetadataSnapshotService


# =============================================================================
# Database Connection (Hybrid: CI=env vars, Local=testcontainers)
# =============================================================================

_postgres_container = None


def _is_ci_environment() -> bool:
    """Check if running in CI environment."""
    return os.getenv("CI") is not None


def _get_ci_postgres_url() -> URL:
    """Get PostgreSQL URL from CI environment variables."""
    return URL.create(
        "postgresql",
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "test_db"),
    )


@pytest.fixture(scope="session")
def postgres_url():
    """Provide PostgreSQL URL (session-scoped).

    - CI: Use PostgreSQL service from GitLab services
    - Local: Start testcontainers PostgreSQL
    """
    global _postgres_container

    if _is_ci_environment():
        yield _get_ci_postgres_url()
    else:
        _postgres_container = PostgresContainer("postgres:17.4")
        _postgres_container.start()
        yield _postgres_container.get_connection_url()
        _postgres_container.stop()


@pytest.fixture(scope="function")
def engine(postgres_url):
    """Create engine for each test (function-scoped cleanup)."""
    engine = create_engine(postgres_url, echo=False)
    SQLModel.metadata.create_all(engine)

    yield engine

    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db(engine) -> Generator[Session, None, None]:
    """Create database session for each test."""
    with Session(engine) as session:
        yield session
        session.rollback()


# =============================================================================
# Mock Session
# =============================================================================


@pytest.fixture
def mock_db() -> MagicMock:
    """Create mock database session."""
    return MagicMock()


# =============================================================================
# CatalogEntry Fixtures
# =============================================================================


@pytest.fixture
def mock_catalog_entry_repository() -> MagicMock:
    """Create mock CatalogEntryRepository."""
    return MagicMock()


@pytest.fixture
def catalog_entry_service(mock_catalog_entry_repository: MagicMock) -> CatalogEntryService:
    """Create CatalogEntryService with mock repository."""
    return CatalogEntryService(repository=mock_catalog_entry_repository)


@pytest.fixture
def sample_catalog_entry() -> CatalogEntry:
    """Create sample CatalogEntry."""
    return CatalogEntry(
        id=1,
        title="Sample Dataset",
        description="A sample dataset for testing",
        identifier=ENTRY_ID_1,
        publisher="Test Publisher",
        keyword=["test", "sample"],
        theme=["science", "data"],
        landing_page="https://example.com/dataset",
        access_url="https://example.com/data.csv",
        issued=date(2024, 1, 1),
        modified=date(2024, 6, 1),
        raw_metadata={"title": "Sample Dataset", "nested": {"key": "value"}},
        ingested_at=datetime(2024, 1, 15, 10, 0, 0),
        updated_at=datetime(2024, 6, 15, 10, 0, 0),
    )


@pytest.fixture
def sample_catalog_entry_summary() -> CatalogEntrySummary:
    """Create sample CatalogEntrySummary."""
    return CatalogEntrySummary(
        id=1,
        title="Sample Dataset",
        identifier=ENTRY_ID_1,
        publisher="Test Publisher",
        keyword=["test", "sample"],
        theme=["science"],
        issued="2024-01-01",
        modified="2024-06-01",
    )


# =============================================================================
# MetadataEntry Fixtures
# =============================================================================


@pytest.fixture
def mock_metadata_entry_repository() -> MagicMock:
    """Create mock MetadataEntryRepository."""
    return MagicMock()


@pytest.fixture
def metadata_entry_service(mock_metadata_entry_repository: MagicMock) -> MetadataEntryService:
    """Create MetadataEntryService with mock repository."""
    return MetadataEntryService(repository=mock_metadata_entry_repository)


@pytest.fixture
def sample_metadata_entry() -> MetadataEntry:
    """Create sample MetadataEntry."""
    return MetadataEntry(
        id=1,
        metadata_schema="dct:title",
        value="Sample Title",
        metadata_id=METADATA_ID_1,
        ingested_at=datetime(2024, 1, 15, 10, 0, 0),
    )


# =============================================================================
# ColumnRelation Fixtures
# =============================================================================


@pytest.fixture
def mock_column_relation_repository() -> MagicMock:
    """Create mock ColumnRelationRepository."""
    return MagicMock()


@pytest.fixture
def column_relation_service(mock_column_relation_repository: MagicMock) -> ColumnRelationService:
    """Create ColumnRelationService with mock repository."""
    return ColumnRelationService(repository=mock_column_relation_repository)


@pytest.fixture
def sample_column_relation() -> ColumnRelation:
    """Create sample ColumnRelation."""
    return ColumnRelation(
        id=1,
        catalog_column="title",
        metadata_column="dct:title",
        correlation=0.95,
    )


# =============================================================================
# CatalogEntryDraft Fixtures
# =============================================================================


@pytest.fixture
def mock_catalog_entry_draft_repository() -> MagicMock:
    """Create mock CatalogEntryDraftRepository."""
    return MagicMock()


@pytest.fixture
def catalog_entry_draft_service(mock_catalog_entry_draft_repository: MagicMock) -> CatalogEntryDraftService:
    """Create CatalogEntryDraftService with mock repository."""
    return CatalogEntryDraftService(repository=mock_catalog_entry_draft_repository)


@pytest.fixture
def sample_catalog_entry_draft() -> CatalogEntryDraft:
    """Create sample CatalogEntryDraft."""
    return CatalogEntryDraft(
        id=1,
        snapshot_id=SNAPSHOT_ID_VALID,
        mapping_version=TEST_MAPPING_VERSION,
        title="Draft Dataset",
        description="Draft description",
        keyword=["draft", "test"],
        theme=["science"],
        mapping_evidence={
            "title": [{"schema": "dct:title", "value": "Draft Dataset", "score": 0.95}],
            "description": [{"schema": "dct:description", "value": "Draft description", "score": 0.90}],
        },
    )


# =============================================================================
# MetadataSnapshot Fixtures
# =============================================================================


@pytest.fixture
def mock_metadata_snapshot_repository() -> MagicMock:
    """Create mock MetadataSnapshotRepository."""
    return MagicMock()


@pytest.fixture
def mock_filesystem_storage() -> MagicMock:
    """Create mock FilesystemStorage."""
    return MagicMock()


@pytest.fixture
def metadata_snapshot_service(
    mock_metadata_snapshot_repository: MagicMock,
    mock_filesystem_storage: MagicMock,
) -> MetadataSnapshotService:
    """Create MetadataSnapshotService with mock dependencies."""
    return MetadataSnapshotService(
        repository=mock_metadata_snapshot_repository,
        storage=mock_filesystem_storage,
    )


@pytest.fixture
def sample_metadata_snapshot() -> MetadataSnapshot:
    """Create sample MetadataSnapshot."""
    from active_metadata.types import SnapshotIdentifier

    snapshot_id = SnapshotIdentifier(SNAPSHOT_ID_VALID)
    return MetadataSnapshot(
        snapshot_id=snapshot_id,
        payload_sha256=TEST_SHA256,
        storage_key="snapshots/2024/01/abc123.json",
        original_filename="metadata.json",
        ingested_at=datetime(2024, 1, 15, 10, 0, 0),
    )


# =============================================================================
# Repository Fixtures (Real instances for integration tests)
# =============================================================================


@pytest.fixture
def catalog_entry_repository():
    """Create CatalogEntryRepository instance."""
    from app.src.catalog_entry.repository import CatalogEntryRepository

    return CatalogEntryRepository()


@pytest.fixture
def metadata_entry_repository():
    """Create MetadataEntryRepository instance."""
    from app.src.metadata_entry.repository import MetadataEntryRepository

    return MetadataEntryRepository()


@pytest.fixture
def column_relation_repository():
    """Create ColumnRelationRepository instance."""
    from app.src.column_relation.repository import ColumnRelationRepository

    return ColumnRelationRepository()


@pytest.fixture
def catalog_entry_draft_repository():
    """Create CatalogEntryDraftRepository instance."""
    from app.src.catalog_entry_draft.repository import CatalogEntryDraftRepository

    return CatalogEntryDraftRepository()


@pytest.fixture
def metadata_snapshot_repository():
    """Create MetadataSnapshotRepository instance."""
    from app.src.metadata_snapshot.repository import MetadataSnapshotRepository

    return MetadataSnapshotRepository()


# =============================================================================
# Sample Data Fixtures (DB-persisted for integration tests)
# =============================================================================


@pytest.fixture
def sample_catalog_entries(db: Session) -> list[CatalogEntry]:
    """Create and persist sample catalog entries."""
    entries = [
        CatalogEntry(
            identifier=ENTRY_ID_1,
            title="First Dataset",
            description="Description for first dataset",
            publisher="Publisher A",
            keyword=["science", "data"],
            theme=["research"],
            issued=date(2024, 1, 1),
            modified=date(2024, 6, 1),
            raw_metadata={"source": "test"},
        ),
        CatalogEntry(
            identifier=ENTRY_ID_2,
            title="Second Dataset",
            description="Description for second dataset",
            publisher="Publisher B",
            keyword=["technology"],
            theme=["innovation"],
            issued=date(2024, 2, 1),
            modified=date(2024, 7, 1),
            raw_metadata={"source": "test"},
        ),
        CatalogEntry(
            identifier=ENTRY_ID_3,
            title="Third Dataset",
            description="Another description",
            publisher="Publisher A",
            keyword=["science", "environment"],
            theme=["research", "climate"],
            issued=date(2024, 3, 1),
            modified=date(2024, 8, 1),
            raw_metadata={"source": "test"},
        ),
    ]
    for entry in entries:
        db.add(entry)
    db.commit()
    for entry in entries:
        db.refresh(entry)
    return entries


@pytest.fixture
def sample_metadata_entries(db: Session) -> list[MetadataEntry]:
    """Create and persist sample metadata entries."""
    entries = [
        MetadataEntry(
            metadata_schema="dct:title",
            value="Sample Title",
            metadata_id=METADATA_ID_1,
        ),
        MetadataEntry(
            metadata_schema="dct:description",
            value="Sample Description",
            metadata_id=METADATA_ID_1,
        ),
        MetadataEntry(
            metadata_schema="dct:title",
            value="Another Title",
            metadata_id=METADATA_ID_2,
        ),
        MetadataEntry(
            metadata_schema="dcat:keyword",
            value="test,sample",
            metadata_id=METADATA_ID_2,
        ),
    ]
    for entry in entries:
        db.add(entry)
    db.commit()
    for entry in entries:
        db.refresh(entry)
    return entries


@pytest.fixture
def sample_column_relations(db: Session) -> list[ColumnRelation]:
    """Create and persist sample column relations."""
    relations = [
        ColumnRelation(catalog_column="title", metadata_column="dct:title", correlation=0.95),
        ColumnRelation(catalog_column="title", metadata_column="schema:name", correlation=0.85),
        ColumnRelation(catalog_column="description", metadata_column="dct:description", correlation=0.90),
        ColumnRelation(catalog_column="keyword", metadata_column="dcat:keyword", correlation=0.88),
    ]
    for relation in relations:
        db.add(relation)
    db.commit()
    for relation in relations:
        db.refresh(relation)
    return relations


@pytest.fixture
def sample_catalog_entry_drafts(db: Session) -> list[CatalogEntryDraft]:
    """Create and persist sample catalog entry drafts."""
    drafts = [
        CatalogEntryDraft(
            snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version=TEST_MAPPING_VERSION,
            status=DraftStatus.PENDING,
            title="Draft Title 1",
            description="Draft Description 1",
            keyword=["draft", "test"],
            mapping_evidence={"title": [{"schema": "dct:title", "score": 0.9}]},
        ),
        CatalogEntryDraft(
            snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version=TEST_MAPPING_VERSION,
            status=DraftStatus.PUBLISHED,
            title="Draft Title 2",
            description="Draft Description 2",
            keyword=["published"],
            mapping_evidence={"title": [{"schema": "dct:title", "score": 0.85}]},
        ),
        CatalogEntryDraft(
            snapshot_id=SNAPSHOT_ID_VALID_ALT,
            mapping_version=TEST_MAPPING_VERSION_ALT,
            status=DraftStatus.PENDING,
            title="Draft Title 3",
            description="Draft Description 3",
            keyword=["another"],
            mapping_evidence={},
        ),
    ]
    for draft in drafts:
        db.add(draft)
    db.commit()
    for draft in drafts:
        db.refresh(draft)
    return drafts


@pytest.fixture
def sample_metadata_snapshots(db: Session) -> list[MetadataSnapshot]:
    """Create and persist sample metadata snapshots."""
    from active_metadata.types import SnapshotIdentifier

    snapshots = [
        MetadataSnapshot(
            snapshot_id=SnapshotIdentifier(SNAPSHOT_ID_VALID),
            payload_sha256=TEST_SHA256,
            storage_key="2024/01/snapshot1.json",
            original_filename="data1.json",
        ),
        MetadataSnapshot(
            snapshot_id=SnapshotIdentifier(SNAPSHOT_ID_VALID_ALT),
            payload_sha256=TEST_SHA256_ALT,
            storage_key="2024/01/snapshot2.json",
            original_filename="data2.json",
        ),
    ]
    for snapshot in snapshots:
        db.add(snapshot)
    db.commit()
    for snapshot in snapshots:
        db.refresh(snapshot)
    return snapshots
