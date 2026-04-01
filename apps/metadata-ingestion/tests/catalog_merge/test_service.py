"""Unit tests for CatalogMergeService."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest

from active_metadata.models import DraftStatus, MergeDecision
from app.src.catalog_entry.model import CatalogEntry
from app.src.catalog_entry_draft.model import CatalogEntryDraft, DecidedMapping, MappingCandidate, MappingEvidence
from app.src.catalog_merge.model import CatalogMerge
from app.src.catalog_merge.repository import CatalogMergeRepository
from app.src.catalog_merge.service import CatalogMergeService
from tests.constants import SNAPSHOT_ID_VALID, TEST_EXTERNAL_ID_URL, TEST_MAPPING_VERSION


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_merge_repository() -> MagicMock:
    repo = MagicMock(spec=CatalogMergeRepository)
    repo.save = MagicMock(side_effect=lambda db, merge: merge)
    repo.update = MagicMock(side_effect=lambda db, merge: merge)
    repo.find_by_id = MagicMock(return_value=None)
    return repo


@pytest.fixture
def mock_event_bus():
    bus = MagicMock()
    bus.publish = MagicMock()
    return bus


@pytest.fixture
def merge_service(mock_merge_repository, catalog_entry_service, mock_event_bus) -> CatalogMergeService:
    return CatalogMergeService(
        repository=mock_merge_repository,
        catalog_entry_service=catalog_entry_service,
        event_bus=mock_event_bus,
    )


def _make_draft(
    draft_id: int = 1,
    external_ids: list[str] | None = None,
    mapping_evidence: dict | None = None,
) -> CatalogEntryDraft:
    """Helper to create draft with mapping_evidence."""
    return CatalogEntryDraft(
        id=draft_id,
        snapshot_id=SNAPSHOT_ID_VALID,
        mapping_version=TEST_MAPPING_VERSION,
        status=DraftStatus.PENDING,
        title="Test Title",
        description="Test Description",
        external_ids=external_ids,
        mapping_evidence=mapping_evidence or {},
    )


def _make_full_evidence(correlation: float = 0.95) -> dict:
    """Build mapping_evidence with all 10 content fields having decided.correlation."""
    from active_metadata.models import CatalogContentFields

    fields = CatalogContentFields.get_content_fields()
    evidence = {}
    for field in fields:
        evidence[field] = MappingEvidence(
            candidates=[MappingCandidate(metadata_column=f"meta:{field}", correlation=correlation, value=f"val_{field}")],
            recommended=MappingCandidate(metadata_column=f"meta:{field}", correlation=correlation, value=f"val_{field}"),
            decided=DecidedMapping(metadata_column=f"meta:{field}", correlation=correlation, value=f"val_{field}"),
        ).model_dump()
    return evidence


def _make_partial_evidence(count: int = 5, correlation: float = 0.95) -> dict:
    """Build mapping_evidence with only `count` fields."""
    from active_metadata.models import CatalogContentFields

    fields = list(CatalogContentFields.get_content_fields())[:count]
    evidence = {}
    for field in fields:
        evidence[field] = MappingEvidence(
            candidates=[MappingCandidate(metadata_column=f"meta:{field}", correlation=correlation, value=f"val_{field}")],
            recommended=MappingCandidate(metadata_column=f"meta:{field}", correlation=correlation, value=f"val_{field}"),
            decided=DecidedMapping(metadata_column=f"meta:{field}", correlation=correlation, value=f"val_{field}"),
        ).model_dump()
    return evidence


def _make_catalog_entry(entry_id: int = 42, external_ids: list[str] | None = None) -> CatalogEntry:
    return CatalogEntry(
        id=entry_id,
        identifier=f"entry-{entry_id}",
        title="Existing Title",
        external_ids=external_ids or [TEST_EXTERNAL_ID_URL],
        latest_snapshot_id=SNAPSHOT_ID_VALID,
    )


# =============================================================================
# compute_mapping_score tests
# =============================================================================


class TestComputeMappingScore:
    def test_full_coverage(self):
        """10필드 * 0.95 correlation / 10 = 0.95"""
        evidence = _make_full_evidence(0.95)
        score = CatalogMergeService.compute_mapping_score(evidence)
        assert score == pytest.approx(0.95, abs=0.01)

    def test_partial_coverage(self):
        """5필드 * 0.95 / 10 = 0.475"""
        evidence = _make_partial_evidence(5, 0.95)
        score = CatalogMergeService.compute_mapping_score(evidence)
        assert score == pytest.approx(0.475, abs=0.01)

    def test_empty_evidence(self):
        """빈 evidence → 0.0"""
        score = CatalogMergeService.compute_mapping_score({})
        assert score == 0.0

    def test_none_correlation_treated_as_zero(self):
        """correlation=None인 필드는 0으로 처리."""
        evidence = {
            "title": MappingEvidence(
                candidates=[],
                recommended=None,
                decided=DecidedMapping(metadata_column="meta:title", correlation=None, value="v", out_of_candidates=True),
            ).model_dump()
        }
        score = CatalogMergeService.compute_mapping_score(evidence)
        assert score == 0.0


# =============================================================================
# create_merge tests
# =============================================================================


class TestCreateMerge:
    def test_no_external_ids(self, merge_service, mock_db_session):
        """external_ids=None → candidates=[], PENDING."""
        draft = _make_draft(external_ids=None)
        merge = merge_service.create_merge(mock_db_session, draft)

        assert merge.decision == MergeDecision.PENDING
        assert merge.decided_by is None
        assert merge.merge_evidence["candidates"] == []

    def test_no_matching_entries(self, merge_service, mock_db_session, mock_catalog_entry_repository):
        """external_ids 있지만 매칭 entry 없음 → PENDING."""
        mock_catalog_entry_repository.find_by_external_ids = MagicMock(return_value=[])
        draft = _make_draft(external_ids=[TEST_EXTERNAL_ID_URL])
        merge = merge_service.create_merge(mock_db_session, draft)

        assert merge.decision == MergeDecision.PENDING
        assert merge.merge_evidence["candidates"] == []

    def test_below_threshold(self, merge_service, mock_db_session, mock_catalog_entry_repository):
        """매칭 entry 있지만 score < threshold → PENDING."""
        entry = _make_catalog_entry()
        mock_catalog_entry_repository.find_by_external_ids = MagicMock(return_value=[entry])

        # 3 fields → score = 3 * 0.95 / 10 = 0.285, below 0.90
        draft = _make_draft(
            external_ids=[TEST_EXTERNAL_ID_URL],
            mapping_evidence=_make_partial_evidence(3, 0.95),
        )
        merge = merge_service.create_merge(mock_db_session, draft)

        assert merge.decision == MergeDecision.PENDING
        assert merge.decided_by is None

    def test_above_threshold(self, merge_service, mock_db_session, mock_catalog_entry_repository):
        """매칭 entry + score >= threshold → APPROVED, decided_by="system_auto"."""
        entry = _make_catalog_entry(entry_id=42)
        mock_catalog_entry_repository.find_by_external_ids = MagicMock(return_value=[entry])

        draft = _make_draft(
            external_ids=[TEST_EXTERNAL_ID_URL],
            mapping_evidence=_make_full_evidence(0.95),
        )
        merge = merge_service.create_merge(mock_db_session, draft)

        assert merge.decision == MergeDecision.APPROVED
        assert merge.decided_by == "system_auto"
        assert merge.target_entry_id == 42
        assert merge.merge_evidence["decided"]["entry_id"] == 42

    def test_selects_most_recent(self, merge_service, mock_db_session, mock_catalog_entry_repository):
        """여러 매칭 → recommended = candidates[0] (최신순)."""
        entries = [
            _make_catalog_entry(entry_id=42, external_ids=[TEST_EXTERNAL_ID_URL]),
            _make_catalog_entry(entry_id=17, external_ids=[TEST_EXTERNAL_ID_URL]),
        ]
        # find_by_external_ids는 updated_at desc 정렬이므로 42가 최신
        mock_catalog_entry_repository.find_by_external_ids = MagicMock(return_value=entries)

        draft = _make_draft(
            external_ids=[TEST_EXTERNAL_ID_URL],
            mapping_evidence=_make_full_evidence(0.95),
        )
        merge = merge_service.create_merge(mock_db_session, draft)

        assert merge.merge_evidence["recommended"]["entry_id"] == 42
        assert len(merge.merge_evidence["candidates"]) == 2


# =============================================================================
# approve / reject tests
# =============================================================================


class TestApproveReject:
    def test_approve_sets_decision(self, merge_service, mock_db_session, mock_merge_repository, mock_catalog_entry_repository):
        """approve → APPROVED + publish, decided_by set."""
        existing = CatalogMerge(
            id=1, draft_id=10, decision=MergeDecision.PENDING,
            merge_evidence={"searched_external_ids": [], "candidates": [], "recommended": None, "decided": None},
            mapping_score=0.5,
        )
        mock_merge_repository.find_by_id = MagicMock(return_value=existing)

        draft = _make_draft(draft_id=10)
        mock_draft_service = MagicMock()
        mock_draft_service.get_draft = MagicMock(return_value=draft)

        mock_catalog_entry_repository.save = MagicMock(side_effect=lambda db, entry: entry)

        merge, catalog_entry = merge_service.approve(mock_db_session, 1, "user-123", mock_draft_service)
        assert merge.decision == MergeDecision.APPROVED
        assert merge.decided_by == "user-123"
        assert merge.decided_at is not None
        assert catalog_entry is not None

    def test_reject_sets_decision(self, merge_service, mock_db_session, mock_merge_repository):
        """reject → REJECTED, decided_by set."""
        existing = CatalogMerge(
            id=1, draft_id=10, decision=MergeDecision.PENDING,
            merge_evidence={}, mapping_score=0.0,
        )
        mock_merge_repository.find_by_id = MagicMock(return_value=existing)

        result = merge_service.reject(mock_db_session, 1, "user-456")
        assert result.decision == MergeDecision.REJECTED
        assert result.decided_by == "user-456"


# =============================================================================
# apply_merge tests
# =============================================================================


class TestApplyMerge:
    def test_creates_new_entry(self, merge_service, mock_db_session, mock_catalog_entry_repository):
        """target_entry_id=None → 새 CatalogEntry 생성."""
        merge = CatalogMerge(
            id=1, draft_id=10, target_entry_id=None,
            decision=MergeDecision.APPROVED, merge_evidence={}, mapping_score=0.95,
        )
        draft = _make_draft()

        result = merge_service.apply_merge(mock_db_session, merge, draft)
        mock_catalog_entry_repository.save.assert_called_once()
        saved_entry = mock_catalog_entry_repository.save.call_args[0][1]
        assert saved_entry.title == "Test Title"

    def test_updates_existing_entry(self, merge_service, mock_db_session, mock_catalog_entry_repository):
        """target_entry_id=42 → 기존 entry 업데이트 (전체 필드 덮어쓰기)."""
        existing = _make_catalog_entry(entry_id=42)
        mock_catalog_entry_repository.select = MagicMock(return_value=existing)
        mock_catalog_entry_repository.save = MagicMock(return_value=existing)

        merge = CatalogMerge(
            id=1, draft_id=10, target_entry_id=42,
            decision=MergeDecision.APPROVED, merge_evidence={}, mapping_score=0.95,
        )
        draft = _make_draft()
        draft.title = "Updated Title"
        draft.description = "Updated Description"

        merge_service.apply_merge(mock_db_session, merge, draft)
        mock_catalog_entry_repository.select.assert_called_once_with(mock_db_session, 42)
