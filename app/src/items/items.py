from typing import Dict

from starlette import status

from app.config import settings
from app.exceptions.base import ApplicationError
from app.exceptions.service import ItemNotFoundError


def load_mock_items() -> Dict[str, Dict[str, str]]:
    """Mock data.

    Returns:

    """
    fake_items_db = {"plumbus": {"name": "Plumbus"}, "gun": {"name": "Portal Gun"}}
    return fake_items_db


def read_item_from_db(item_id):
    """Read item from fake db.

    Args:
        item_id:

    Returns:

    """
    fake_items_db = load_mock_items()
    if item_id not in fake_items_db.keys():
        raise ItemNotFoundError(item_id)
    return fake_items_db[item_id]["name"]


def update_item_to_db(item_id):
    """Update item to fake db.

    Args:
        item_id:

    Returns:

    """
    if item_id != "plumbus":
        raise ApplicationError(
            code=int(str(settings.SERVICE_CODE) + str(status.HTTP_403_FORBIDDEN)),
            message="You can only update the item: plumbus", result={}
        )
    return "The great Plumbus"
