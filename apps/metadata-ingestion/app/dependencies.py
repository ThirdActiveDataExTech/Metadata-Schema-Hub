from typing import Annotated, Generator

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from sqlmodel import Session

from app.db import engine
from app.utils.authentication import token_validation

header_scheme = APIKeyHeader(name="x-token")


async def get_token_header(x_token: Annotated[str, Security(header_scheme)]):
    await token_validation(x_token)


def get_session() -> Generator[Session, None, None]:
    """Get session"""
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


SessionDep = Annotated[Session, Depends(get_session)]
