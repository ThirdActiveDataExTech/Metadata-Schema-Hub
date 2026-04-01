"""Unit tests for CatalogMergeService (thin CRUD + state transitions)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from active_metadata.models import DraftStatus, MergeDecision
from app.src.catalog_entry_draft.model import CatalogEntryDraft, DecidedMapping, MappingCandidate, MappingEvidence
from app.src.catalog_merge.exceptions import MergeNotFoundError, MergeNotPendingError
from app.src.catalog_merge.model import CatalogMerge
from app.src.catalog_merge.repository import CatalogMergeRepository
from app.src.catalog_merge.service import CatalogMergeService
from tests.constants import SNAPSHOT_ID_VALID, TEST_MAPPING_VERSION


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
def merge_service(mock_merge_repository) -> CatalogMergeService:
    return CatalogMergeService(repository=mock_merge_repository)


# =============================================================================
# create_merge tests (pure CRUD)
# =============================================================================


class TestCreateMerge:
    def test_creates_pending_merge(self, merge_service, mock_db_session):
        """create_merge saves a PENDING record with pre-built data."""
        evidence = {"searched_external_ids": [], "candidates": [], "recommended": None, "decided": None}
        merge = merge_service.create_merge(
            mock_db_session,
            draft_id=10,
            merge_evidence=evidence,
            mapping_score=0.5,
        )

        assert merge.decision == MergeDecision.PENDING
        assert merge.decided_by is None
        assert merge.draft_id == 10
        assert merge.mapping_score == 0.5
        assert merge.merge_evidence == evidence

    def test_creates_with_target_entry(self, merge_service, mock_db_session):
        """create_merge accepts optional target_entry_id."""
        merge = merge_service.create_merge(
            mock_db_session,
            draft_id=10,
            merge_evidence={"candidates": [{"entry_id": 42}]},
            mapping_score=0.95,
            target_entry_id=42,
        )

        assert merge.target_entry_id == 42
        assert merge.decision == MergeDecision.PENDING


# =============================================================================
# approve_decision tests (state transition only)
# =============================================================================


class TestApproveDecision:
    def test_sets_approved(self, merge_service, mock_db_session, mock_merge_repository):
        """approve_decision → APPROVED, decided_by set, no side effects."""
        existing = CatalogMerge(
            id=1, draft_id=10, decision=MergeDecision.PENDING,
            merge_evidence={"searched_external_ids": [], "candidates": [], "recommended": None, "decided": None},
            mapping_score=0.5,
        )
        mock_merge_repository.find_by_id = MagicMock(return_value=existing)

        result = merge_service.approve_decision(mock_db_session, 1, "user-123")

        assert result.decision == MergeDecision.APPROVED
        assert result.decided_by == "user-123"
        assert result.decided_at is not None

    def test_updates_target_entry_id(self, merge_service, mock_db_session, mock_merge_repository):
        """approve_decision with target_entry_id updates evidence.decided."""
        existing = CatalogMerge(
            id=1, draft_id=10, decision=MergeDecision.PENDING,
            merge_evidence={"searched_external_ids": [], "candidates": [], "recommended": None, "decided": None},
            mapping_score=0.5,
        )
        mock_merge_repository.find_by_id = MagicMock(return_value=existing)

        result = merge_service.approve_decision(mock_db_session, 1, "user-123", target_entry_id=42)

        assert result.target_entry_id == 42
        assert result.merge_evidence["decided"]["entry_id"] == 42
        assert result.merge_evidence["decided"]["decided_by"] == "user-123"

    def test_not_found_raises(self, merge_service, mock_db_session, mock_merge_repository):
        """approve_decision raises MergeNotFoundError."""
        mock_merge_repository.find_by_id = MagicMock(return_value=None)

        with pytest.raises(MergeNotFoundError):
            merge_service.approve_decision(mock_db_session, 999, "user-123")

    def test_not_pending_raises(self, merge_service, mock_db_session, mock_merge_repository):
        """approve_decision raises MergeNotPendingError for non-PENDING."""
        existing = CatalogMerge(
            id=1, draft_id=10, decision=MergeDecision.APPROVED,
            merge_evidence={}, mapping_score=0.5,
        )
        mock_merge_repository.find_by_id = MagicMock(return_value=existing)

        with pytest.raises(MergeNotPendingError):
            merge_service.approve_decision(mock_db_session, 1, "user-123")


# =============================================================================
# reject tests
# =============================================================================


class TestReject:
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

    def test_reject_not_found_raises(self, merge_service, mock_db_session, mock_merge_repository):
        """reject raises MergeNotFoundError."""
        mock_merge_repository.find_by_id = MagicMock(return_value=None)

        with pytest.raises(MergeNotFoundError):
            merge_service.reject(mock_db_session, 999, "user-456")
