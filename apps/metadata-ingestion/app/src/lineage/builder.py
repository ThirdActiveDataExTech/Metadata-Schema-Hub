"""OpenLineage event builder for creating spec-compliant RunEvent payloads."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from active_metadata.models import LineageEventType

__all__ = ["OpenLineageEventBuilder"]


class OpenLineageEventBuilder:
    """Builder for creating OpenLineage-compliant RunEvent payloads.

    Implements fluent interface for constructing OpenLineage events.
    See: https://openlineage.io/spec/2-0-2/OpenLineage.json
    """

    SCHEMA_URL = "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent"
    PRODUCER = "https://active-metadata.wisenut.com/metadata-ingestion"
    DEFAULT_NAMESPACE = "wisenut-amm"

    def __init__(self) -> None:
        """Initialize builder with default values."""
        self._run_id: UUID | None = None
        self._parent_run_id: UUID | None = None
        self._event_type: LineageEventType = LineageEventType.START
        self._event_time: datetime | None = None
        self._job_name: str = ""
        self._job_namespace: str = self.DEFAULT_NAMESPACE
        self._run_facets: dict[str, Any] = {}
        self._job_facets: dict[str, Any] = {}
        self._inputs: list[dict[str, Any]] = []
        self._outputs: list[dict[str, Any]] = []

    def with_new_run_id(self) -> "OpenLineageEventBuilder":
        """Generate new UUID for run."""
        self._run_id = uuid4()
        return self

    def with_run_id(self, run_id: UUID) -> "OpenLineageEventBuilder":
        """Set specific run ID."""
        self._run_id = run_id
        return self

    def with_parent_run_id(self, parent_run_id: UUID) -> "OpenLineageEventBuilder":
        """Set parent run ID for lineage chain."""
        self._parent_run_id = parent_run_id
        return self

    def with_event_type(self, event_type: LineageEventType) -> "OpenLineageEventBuilder":
        """Set event type (START, COMPLETE, FAIL, etc.)."""
        self._event_type = event_type
        return self

    def with_event_time(self, event_time: datetime) -> "OpenLineageEventBuilder":
        """Set event timestamp."""
        self._event_time = event_time
        return self

    def with_job(self, name: str, namespace: str | None = None) -> "OpenLineageEventBuilder":
        """Set job name and optional namespace."""
        self._job_name = name
        if namespace:
            self._job_namespace = namespace
        return self

    def with_run_facet(self, name: str, facet: dict[str, Any]) -> "OpenLineageEventBuilder":
        """Add run facet (metadata about the run)."""
        self._run_facets[name] = facet
        return self

    def with_job_facet(self, name: str, facet: dict[str, Any]) -> "OpenLineageEventBuilder":
        """Add job facet (metadata about the job)."""
        self._job_facets[name] = facet
        return self

    def with_input_dataset(
        self,
        namespace: str,
        name: str,
        facets: dict[str, Any] | None = None,
        input_facets: dict[str, Any] | None = None,
    ) -> "OpenLineageEventBuilder":
        """Add input dataset to the event."""
        dataset: dict[str, Any] = {"namespace": namespace, "name": name}
        if facets:
            dataset["facets"] = facets
        if input_facets:
            dataset["inputFacets"] = input_facets
        self._inputs.append(dataset)
        return self

    def with_output_dataset(
        self,
        namespace: str,
        name: str,
        facets: dict[str, Any] | None = None,
        output_facets: dict[str, Any] | None = None,
    ) -> "OpenLineageEventBuilder":
        """Add output dataset to the event."""
        dataset: dict[str, Any] = {"namespace": namespace, "name": name}
        if facets:
            dataset["facets"] = facets
        if output_facets:
            dataset["outputFacets"] = output_facets
        self._outputs.append(dataset)
        return self

    def build(self) -> dict[str, Any]:
        """Build the complete OpenLineage RunEvent payload.

        Returns:
            OpenLineage RunEvent JSON structure
        """
        if not self._run_id:
            self._run_id = uuid4()

        event_time = self._event_time or datetime.now(timezone.utc)

        # Build run object with facets
        run: dict[str, Any] = {
            "runId": str(self._run_id),
        }
        if self._run_facets:
            run["facets"] = self._run_facets
        if self._parent_run_id:
            if "facets" not in run:
                run["facets"] = {}
            run["facets"]["parent"] = {
                "_producer": self.PRODUCER,
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-1/ParentRunFacet.json",
                "run": {"runId": str(self._parent_run_id)},
                "job": {"namespace": self._job_namespace, "name": self._job_name},
            }

        # Build job object with facets
        job: dict[str, Any] = {
            "namespace": self._job_namespace,
            "name": self._job_name,
        }
        if self._job_facets:
            job["facets"] = self._job_facets

        # Build complete event
        payload: dict[str, Any] = {
            "eventTime": event_time.isoformat(),
            "eventType": self._event_type.value,
            "producer": self.PRODUCER,
            "schemaURL": self.SCHEMA_URL,
            "run": run,
            "job": job,
        }

        if self._inputs:
            payload["inputs"] = self._inputs
        if self._outputs:
            payload["outputs"] = self._outputs

        return payload

    @property
    def run_id(self) -> UUID:
        """Get the run ID (generates new one if not set)."""
        if not self._run_id:
            self._run_id = uuid4()
        return self._run_id

    @property
    def job_name(self) -> str:
        """Get the job name."""
        return self._job_name

    @property
    def job_namespace(self) -> str:
        """Get the job namespace."""
        return self._job_namespace

    @property
    def event_type(self) -> LineageEventType:
        """Get the event type."""
        return self._event_type

    def _make_facet(self, schema_path: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a facet with standard _producer and _schemaURL fields."""
        return {
            "_producer": self.PRODUCER,
            "_schemaURL": f"{self.PRODUCER}/schemas/{schema_path}",
            **data,
        }

    def with_amm_ingestion_run_facet(
        self, ingestion_run_id: int, mapping_version: str
    ) -> "OpenLineageEventBuilder":
        """Add AMM-specific ingestion run facet."""
        return self.with_run_facet(
            "amm_ingestionRun",
            self._make_facet(
                "AmmIngestionRunFacet.json",
                {"ingestionRunId": ingestion_run_id, "mappingVersion": mapping_version},
            ),
        )

    def with_amm_snapshot_output_facet(
        self, snapshot_id: str, payload_sha256: str, storage_key: str
    ) -> "OpenLineageEventBuilder":
        """Add AMM-specific snapshot output facet."""
        return self.with_output_dataset(
            namespace="postgres://amm-db.wisenut.com/amm",
            name="metadata_snapshot",
            output_facets={
                "amm_snapshot": self._make_facet(
                    "AmmSnapshotFacet.json",
                    {
                        "snapshotId": snapshot_id,
                        "payloadSha256": payload_sha256,
                        "storageKey": storage_key,
                    },
                )
            },
        )

    def with_amm_draft_output_facet(
        self, draft_id: int, mapping_version: str
    ) -> "OpenLineageEventBuilder":
        """Add AMM-specific draft output facet."""
        return self.with_output_dataset(
            namespace="postgres://amm-db.wisenut.com/amm",
            name="catalog_entry_draft",
            output_facets={
                "amm_draft": self._make_facet(
                    "AmmDraftFacet.json",
                    {"draftId": draft_id, "mappingVersion": mapping_version},
                )
            },
        )

    def with_amm_catalog_entry_output_facet(
        self, catalog_entry_id: int, identifier: str
    ) -> "OpenLineageEventBuilder":
        """Add AMM-specific catalog entry output facet."""
        return self.with_output_dataset(
            namespace="postgres://amm-db.wisenut.com/amm",
            name="catalog_entry",
            output_facets={
                "amm_catalogEntry": self._make_facet(
                    "AmmCatalogEntryFacet.json",
                    {"catalogEntryId": catalog_entry_id, "identifier": identifier},
                )
            },
        )
