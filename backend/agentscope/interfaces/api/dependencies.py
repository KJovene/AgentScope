"""Injection de dépendances FastAPI — pont routes ↔ conteneur de composition.

Chaque route déclare le service dont elle a besoin via un `Annotated[..., Depends]`
défini ici. Le conteneur (construit dans le lifespan) est la seule source.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from agentscope.application.ports.data_quality import DataQualityQueryService
from agentscope.application.ports.imports import ImportService
from agentscope.application.ports.mapping_crud import MappingCrudService
from agentscope.application.ports.metrics import MetricsQueryService
from agentscope.application.ports.pricing_registry import PricingRegistryService
from agentscope.application.ports.repository_registry import RepositoryRegistryService
from agentscope.application.ports.sources import SourcesQueryService
from agentscope.application.ports.workbench import MappingWorkbenchService
from agentscope.infrastructure.config.settings import Settings
from agentscope.interfaces.api.container import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_settings_dep(container: ContainerDep) -> Settings:
    return container.settings


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


def get_db_session(container: ContainerDep) -> Iterator[Session]:
    with container.database.session() as session:
        yield session


DbSessionDep = Annotated[Session, Depends(get_db_session)]


# --- Services de lecture (CQRS) + service d'import -----------------------------


def get_metrics_service(
    container: ContainerDep, session: DbSessionDep
) -> MetricsQueryService:
    return container.make_metrics_service(session)


def get_sources_service(
    container: ContainerDep, session: DbSessionDep
) -> SourcesQueryService:
    return container.make_sources_service(session)


def get_data_quality_service(
    container: ContainerDep, session: DbSessionDep
) -> DataQualityQueryService:
    return container.make_data_quality_service(session)


def get_import_service(
    container: ContainerDep, session: DbSessionDep
) -> ImportService:
    return container.make_import_service(session)


def get_mapping_service(
    container: ContainerDep, session: DbSessionDep
) -> MappingCrudService:
    return container.make_mapping_service(session)


def get_workbench_service(container: ContainerDep) -> MappingWorkbenchService:
    return container.make_workbench_service()


def get_repository_registry_service(
    container: ContainerDep, session: DbSessionDep
) -> RepositoryRegistryService:
    return container.make_repository_registry_service(session)


def get_pricing_registry_service(
    container: ContainerDep, session: DbSessionDep
) -> PricingRegistryService:
    return container.make_pricing_registry_service(session)


MetricsServiceDep = Annotated[MetricsQueryService, Depends(get_metrics_service)]
SourcesServiceDep = Annotated[SourcesQueryService, Depends(get_sources_service)]
DataQualityServiceDep = Annotated[
    DataQualityQueryService, Depends(get_data_quality_service)
]
ImportServiceDep = Annotated[ImportService, Depends(get_import_service)]
MappingServiceDep = Annotated[MappingCrudService, Depends(get_mapping_service)]
WorkbenchServiceDep = Annotated[
    MappingWorkbenchService, Depends(get_workbench_service)
]
RepositoryRegistryServiceDep = Annotated[
    RepositoryRegistryService, Depends(get_repository_registry_service)
]
PricingRegistryServiceDep = Annotated[
    PricingRegistryService, Depends(get_pricing_registry_service)
]
