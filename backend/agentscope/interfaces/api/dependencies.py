from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from agentscope.infrastructure.config.settings import Settings
from agentscope.interfaces.api.container import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


def get_settings_dep(
    container: Annotated[Container, Depends(get_container)],
) -> Settings:
    return container.settings


def get_db_session(
    container: Annotated[Container, Depends(get_container)],
) -> Iterator[Session]:
    with container.database.session() as session:
        yield session


ContainerDep = Annotated[Container, Depends(get_container)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DbSessionDep = Annotated[Session, Depends(get_db_session)]
