from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from agentscope.application.ports.data_quality import DataQualityQueryService
from agentscope.application.ports.imports import ImportService
from agentscope.application.ports.metrics import MetricsQueryService
from agentscope.application.ports.sources import SourcesQueryService
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


def get_metrics_service(
    container: Annotated[Container, Depends(get_container)],
    session: Annotated[Session, Depends(get_db_session)],
) -> MetricsQueryService:
    return container.make_metrics_service(session)


def get_sources_service(
    container: Annotated[Container, Depends(get_container)],
    session: Annotated[Session, Depends(get_db_session)],
) -> SourcesQueryService:
    return container.make_sources_service(session)


def get_data_quality_service(
    container: Annotated[Container, Depends(get_container)],
    session: Annotated[Session, Depends(get_db_session)],
) -> DataQualityQueryService:
    return container.make_data_quality_service(session)


def get_import_service(
    container: Annotated[Container, Depends(get_container)],
    session: Annotated[Session, Depends(get_db_session)],
) -> ImportService:
    return container.make_import_service(session)


ContainerDep = Annotated[Container, Depends(get_container)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DbSessionDep = Annotated[Session, Depends(get_db_session)]

MetricsServiceDep = Annotated[MetricsQueryService, Depends(get_metrics_service)]
SourcesServiceDep = Annotated[SourcesQueryService, Depends(get_sources_service)]
DataQualityServiceDep = Annotated[DataQualityQueryService, Depends(get_data_quality_service)]
ImportServiceDep = Annotated[ImportService, Depends(get_import_service)]
