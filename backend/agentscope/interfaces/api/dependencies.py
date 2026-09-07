from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from agentscope.application.use_cases.analyze_unknown_file import AnalyzeUnknownFileUseCase
from agentscope.application.use_cases.import_file import ImportFileUseCase
from agentscope.infrastructure.config.settings import Settings
from agentscope.interfaces.api.container import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


def get_settings_dep(container: Annotated[Container, Depends(get_container)]) -> Settings:
    return container.settings


def get_db_session(
    container: Annotated[Container, Depends(get_container)],
) -> Iterator[Session]:
    with container.database.session() as session:
        yield session


def get_import_file_use_case(
    container: Annotated[Container, Depends(get_container)],
    session: Annotated[Session, Depends(get_db_session)],
) -> ImportFileUseCase:
    return container.make_import_file_use_case(session)


def get_analyze_file_use_case(
    container: Annotated[Container, Depends(get_container)],
) -> AnalyzeUnknownFileUseCase:
    return container.make_analyze_file_use_case()


ContainerDep = Annotated[Container, Depends(get_container)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DbSessionDep = Annotated[Session, Depends(get_db_session)]
ImportFileUseCaseDep = Annotated[ImportFileUseCase, Depends(get_import_file_use_case)]
AnalyzeFileUseCaseDep = Annotated[AnalyzeUnknownFileUseCase, Depends(get_analyze_file_use_case)]
