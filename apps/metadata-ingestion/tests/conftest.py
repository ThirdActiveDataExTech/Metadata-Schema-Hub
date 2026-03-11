"""Shared test fixtures and configuration for metadata-ingestion unit tests."""

import os
import pathlib
from datetime import date
from typing import Any, Dict, Generator, List
from unittest.mock import MagicMock

import pytest
from sqlalchemy import URL, create_engine
from sqlmodel import Session, SQLModel
from testcontainers.postgres import PostgresContainer

from active_metadata.models import DraftStatus, IngestionRunState
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
    TEST_RUN_UUID_1,
    TEST_RUN_UUID_2,
    TEST_SHA256,
    TEST_SHA256_ALT,
)

from app.src.catalog_entry.model import CatalogEntry
from app.src.catalog_entry_draft.model import CatalogEntryDraft
from app.src.column_relation.model import ColumnRelation
from app.src.ingestion_run.model import IngestionRun
from app.src.metadata_entry.model import MetadataEntry
from app.src.metadata_snapshot.model import MetadataSnapshot


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

# ============================================================================
# Path Configuration
# ============================================================================

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent  # /active-metadata-management
SAMPLE_DIR = PROJECT_ROOT / "sample"


# ============================================================================
# Sample File Loading Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def sample_dir() -> pathlib.Path:
    """Return path to sample files directory."""
    return SAMPLE_DIR


@pytest.fixture(scope="session")
def sample_json_files(sample_dir: pathlib.Path) -> Dict[str, bytes]:
    """Load all JSON sample files as bytes."""
    json_files = {}
    for pattern in ["schema_org_*.json", "kosis_*.json"]:
        for path in sample_dir.glob(pattern):
            json_files[path.name] = path.read_bytes()
    return json_files


@pytest.fixture(scope="session")
def sample_rdf_files(sample_dir: pathlib.Path) -> Dict[str, bytes]:
    """Load all RDF sample files as bytes."""
    rdf_files = {}
    for pattern in ["dcat_*.rdf"]:
        for path in sample_dir.glob(pattern):
            rdf_files[path.name] = path.read_bytes()
    return rdf_files


@pytest.fixture(scope="session")
def sample_xml_files(sample_dir: pathlib.Path) -> Dict[str, bytes]:
    """Load all XML sample files as bytes."""
    xml_files = {}
    for path in sample_dir.glob("kosis_*.xml"):
        xml_files[path.name] = path.read_bytes()
    return xml_files


@pytest.fixture
def sample_schema_org_json(sample_json_files: Dict[str, bytes]) -> bytes:
    """Return a single schema.org JSON file for basic tests."""
    return sample_json_files["schema_org_15107742.json"]


@pytest.fixture
def sample_dcat_rdf(sample_rdf_files: Dict[str, bytes]) -> bytes:
    """Return a single DCAT RDF file for basic tests."""
    return sample_rdf_files["dcat_15107742.rdf"]


@pytest.fixture
def sample_kosis_xml(sample_xml_files: Dict[str, bytes]) -> bytes:
    """Return a single KOSIS XML file for basic tests."""
    return sample_xml_files["kosis_MT_ZTITLE_101_DT_1EI10122.xml"]


# ============================================================================
# Mock Session Fixture
# ============================================================================


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Create a mock database session."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.flush = MagicMock()
    session.exec = MagicMock()
    session.get = MagicMock()
    session.delete = MagicMock()
    return session


# ============================================================================
# Mock Repository Fixtures
# ============================================================================


@pytest.fixture
def mock_catalog_entry_repository() -> MagicMock:
    """Create mock CatalogEntryRepository."""
    repo = MagicMock()
    repo.save = MagicMock(side_effect=lambda db, entry: entry)
    repo.select = MagicMock()
    repo.select_by_identifier = MagicMock()
    repo.select_by_ids = MagicMock(return_value=[])
    repo.select_by_identifiers = MagicMock(return_value=[])
    repo.select_summaries_by_identifiers = MagicMock(return_value=[])
    repo.export_data_list = MagicMock(return_value=[])
    repo.list_catalog_summary = MagicMock(return_value=[])
    repo.search_catalog = MagicMock(return_value=[])
    repo.create_bulk = MagicMock()
    repo.update_bulk = MagicMock()
    return repo


@pytest.fixture
def mock_metadata_entry_repository() -> MagicMock:
    """Create mock MetadataEntryRepository."""
    repo = MagicMock()
    repo.save = MagicMock(side_effect=lambda db, entries: entries)
    repo.select_metadata_entry = MagicMock(return_value=[])
    repo.select_metadata_entries_by_metadata_ids = MagicMock(return_value=[])
    repo.select_distinct_metadata_schemas = MagicMock(return_value=[])
    repo.list_metadata_summary = MagicMock(return_value=[])
    repo.search_metadata = MagicMock(return_value=[])
    repo.get_all_distinct_metadata_schemas = MagicMock(return_value=[])
    repo.create_bulk = MagicMock()
    return repo


@pytest.fixture
def mock_column_relation_repository() -> MagicMock:
    """Create mock ColumnRelationRepository."""
    repo = MagicMock()
    repo.save = MagicMock(side_effect=lambda db, relation: relation)
    repo.save_bulk = MagicMock(side_effect=lambda db, relations: relations)
    repo.select_relations_by_catalog_column = MagicMock(return_value=[])
    repo.select_relations_by_metadata_column = MagicMock(return_value=[])
    repo.select_relations_by_metadata_columns = MagicMock(return_value=[])
    repo.select_all_relations = MagicMock(return_value=[])
    repo.delete_relations_by_catalog_column = MagicMock(return_value=0)
    return repo


@pytest.fixture
def mock_metadata_snapshot_repository() -> MagicMock:
    """Create mock MetadataSnapshotRepository."""
    repo = MagicMock()
    repo.save = MagicMock(side_effect=lambda db, snapshot: snapshot)
    repo.find_by_snapshot_id = MagicMock(return_value=None)
    repo.find_latest_by_hash = MagicMock(return_value=None)
    return repo


@pytest.fixture
def mock_ingestion_run_repository() -> MagicMock:
    """Create mock IngestionRunRepository."""
    repo = MagicMock()
    repo.save = MagicMock(side_effect=lambda db, run: run)
    repo.find_by_run_id = MagicMock()
    repo.find_by_snapshot_id = MagicMock()
    repo.find_by_state = MagicMock(return_value=[])
    repo.find_all = MagicMock(return_value=[])
    return repo


@pytest.fixture
def mock_catalog_entry_draft_repository() -> MagicMock:
    """Create mock CatalogEntryDraftRepository."""
    repo = MagicMock()
    repo.save = MagicMock(side_effect=lambda db, draft: draft)
    repo.update = MagicMock(side_effect=lambda db, draft: draft)
    repo.find_by_id = MagicMock()
    repo.find_by_snapshot_id = MagicMock(return_value=[])
    repo.find_all = MagicMock(return_value=[])
    return repo


@pytest.fixture
def mock_file_storage() -> MagicMock:
    """Create mock FilesystemStorage."""
    storage = MagicMock()
    storage.save = MagicMock()
    storage.load = MagicMock()
    storage.exists = MagicMock(return_value=True)
    return storage


@pytest.fixture
def mock_event_bus() -> MagicMock:
    """Create mock EventBus."""
    from app.src.events import EventBus

    bus = MagicMock(spec=EventBus)
    bus.publish = MagicMock()
    bus.subscribe = MagicMock()
    return bus


# ============================================================================
# Service Instance Fixtures
# ============================================================================


@pytest.fixture
def catalog_entry_service(mock_catalog_entry_repository):
    """Create CatalogEntryService with mock repository."""
    from app.src.catalog_entry.service import CatalogEntryService

    return CatalogEntryService(repository=mock_catalog_entry_repository)


@pytest.fixture
def metadata_entry_service(mock_metadata_entry_repository):
    """Create MetadataEntryService with mock repository."""
    from app.src.metadata_entry.service import MetadataEntryService

    return MetadataEntryService(repository=mock_metadata_entry_repository)


@pytest.fixture
def column_relation_service(mock_column_relation_repository):
    """Create ColumnRelationService with mock repository."""
    from app.src.column_relation.service import ColumnRelationService

    return ColumnRelationService(repository=mock_column_relation_repository)


@pytest.fixture
def metadata_snapshot_service(mock_metadata_snapshot_repository):
    """Create MetadataSnapshotService with mock repository."""
    from app.src.metadata_snapshot.service import MetadataSnapshotService

    return MetadataSnapshotService(repository=mock_metadata_snapshot_repository)


@pytest.fixture
def ingestion_run_service(mock_ingestion_run_repository):
    """Create IngestionRunService with mock repository."""
    from app.src.ingestion_run.service import IngestionRunService

    return IngestionRunService(repository=mock_ingestion_run_repository)


@pytest.fixture
def catalog_entry_draft_service(mock_catalog_entry_draft_repository, mock_event_bus, catalog_entry_service):
    """Create CatalogEntryDraftService with mock repository, event bus, and catalog entry service."""
    from app.src.catalog_entry_draft.service import CatalogEntryDraftService

    return CatalogEntryDraftService(
        repository=mock_catalog_entry_draft_repository,
        event_bus=mock_event_bus,
        catalog_entry_service=catalog_entry_service,
    )


# ============================================================================
# Common Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_metadata_schemas() -> List[Dict[str, str]]:
    """Return sample MetadataSchema data as dicts."""
    return [
        {"metadata_schema": "name", "value": "Sample Dataset Title"},
        {"metadata_schema": "description", "value": "Sample description text"},
        {"metadata_schema": "keywords", "value": "keyword1,keyword2"},
        {"metadata_schema": "dateModified", "value": "2024-09-25"},
    ]


@pytest.fixture
def valid_snapshot_id() -> str:
    """Return a valid snapshot_id."""
    return SNAPSHOT_ID_VALID


@pytest.fixture
def valid_sha256() -> str:
    """Return a valid SHA256 hash."""
    return TEST_SHA256


# ============================================================================
# Repository Fixtures (Real instances for integration tests)
# ============================================================================


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


@pytest.fixture
def ingestion_run_repository():
    """Create IngestionRunRepository instance."""
    from app.src.ingestion_run.repository import IngestionRunRepository

    return IngestionRunRepository()


# ============================================================================
# Sample Data Fixtures (DB-persisted for integration tests)
# ============================================================================


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
            latest_snapshot_id=SNAPSHOT_ID_VALID,
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
            latest_snapshot_id=SNAPSHOT_ID_VALID_ALT,
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
            latest_snapshot_id=None,
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


@pytest.fixture
def sample_ingestion_runs(db: Session, sample_metadata_snapshots) -> list[IngestionRun]:
    """Create and persist sample ingestion runs."""
    runs = [
        IngestionRun(
            run_id=TEST_RUN_UUID_1,  # UUID required for PK
            snapshot_id=str(sample_metadata_snapshots[0].snapshot_id),
            state=IngestionRunState.STORED,
            mapping_version=TEST_MAPPING_VERSION,
        ),
        IngestionRun(
            run_id=TEST_RUN_UUID_2,  # UUID required for PK
            snapshot_id=str(sample_metadata_snapshots[1].snapshot_id),
            state=IngestionRunState.DRAFTED,
            mapping_version=TEST_MAPPING_VERSION,
            draft_id=1,
        ),
    ]
    for run in runs:
        db.add(run)
    db.commit()
    for run in runs:
        db.refresh(run)
    return runs
