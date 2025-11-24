from typing import Annotated

from fastapi import Depends

from app.src.file_converter.json_converter import JsonConverter
from app.src.file_converter.xml_converter import LxmlConverter


def get_json_converter() -> JsonConverter:
    """JsonConverter dependency injection."""
    return JsonConverter()


def get_xml_converter() -> LxmlConverter:
    """LxmlConverter dependency injection."""
    return LxmlConverter()


JsonConverterDep = Annotated[JsonConverter, Depends(get_json_converter)]
XmlConverterDep = Annotated[LxmlConverter, Depends(get_xml_converter)]
