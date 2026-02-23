from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List

from app.src.metadata_entry.model import MetadataSchema


class Converter(ABC):
    """Abstract base class for metadata file format converters.

    Defines interface for converting file content to dictionary format
    and metadata objects. Each concrete implementation handles specific
    file formats (JSON, XML, etc.).
    """

    @abstractmethod
    def get_supported_extensions(self) -> Iterable[str]:
        """Return file extensions this converter supports.

        Returns:
            Iterable of lowercase extensions with dots (e.g., ['.json', '.jsonld'])
        """
        pass

    @abstractmethod
    def convert_to_dict(self, content: bytes) -> Dict[str, Any]:
        """Convert file content to dictionary representation.

        Args:
            content: Raw file bytes

        Returns:
            Parsed content as dictionary

        Raises:
            ValueError: If content format is invalid
        """
        pass

    @abstractmethod
    def convert_to_metadata_schemas(self, content: bytes) -> List[MetadataSchema]:
        """Convert file content to MetadataSchema objects.

        Args:
            content: Raw file bytes

        Returns:
            List of MetadataSchema objects (schema-value pairs)

        Raises:
            ValueError: If content format is invalid
        """
        pass