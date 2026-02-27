"""CatalogEntryDraft models for catalog-service (read-only)."""

from active_metadata.models import CatalogEntryDraftBase


class CatalogEntryDraft(CatalogEntryDraftBase, table=True):  # type: ignore[call-arg]
    """CatalogEntryDraft table model (read-only)."""

    __tablename__ = "catalog_entry_draft"  # type: ignore[assignment]
