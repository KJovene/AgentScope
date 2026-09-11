"""Rattachement des sessions à un dépôt de code — dimension SWE-chat (issue I1.10)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from agentscope.application.ports import MetricFilter, Page
from agentscope.domain import (
    FileFormat,
    ImportBatch,
    ImportStatus,
    Interval,
    Provenance,
    RawRecord,
    Repository,
    Session,
    Source,
    SourceMapping,
)
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.queries import SqlMetricsQueryService
from agentscope.infrastructure.persistence.repositories import SqlReferenceRepository
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
SHA = "SHA-SWE"
MakeUow = Callable[[], SqlAlchemyUnitOfWork]

REPOS = [
    Repository(source_name="swe-chat", name="octo/api", url="https://x/api", language="python"),
    Repository(source_name="swe-chat", name="octo/web", url="https://x/web", language="typescript"),
    Repository(source_name="swe-chat", name="octo/infra", language="hcl"),
]


def _session(ext: str, repo: str | None) -> Session:
    return Session(
        source_name="swe-chat",
        external_id=ext,
        provenance=Provenance(record_index=0, record_sha256="rr-0"),
        interval=Interval(started_at=NOW, ended_at=NOW),
        repository_name=repo,
    )


@pytest.fixture
def seeded(make_uow: MakeUow, database: Database) -> Database:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="swe-chat"))
        uow.reference.add_source(Source(name="tracelab"))
        uow.reference.upsert_code_repositories("swe-chat", REPOS)
        uow.reference.upsert_code_repositories(
            "tracelab", [Repository(source_name="tracelab", name="other/repo")]
        )
        uow.mappings.add(
            SourceMapping(
                name="swe-chat-parquet",
                version=1,
                source_name="swe-chat",
                source_format=FileFormat.PARQUET,
                definition={"e": 1},
                created_at=NOW,
            )
        )
        batch = ImportBatch(
            source_name="swe-chat",
            original_filename="swe.parquet",
            file_sha256=SHA,
            file_format=FileFormat.PARQUET,
            imported_at=NOW,
            status=ImportStatus.SUCCEEDED,
            mapping_name="swe-chat-parquet",
        )
        uow.imports.add(batch)
        uow.raw_records.upsert_many(batch, [RawRecord(index=0, payload={}, sha256="rr-0")])
        uow.sessions.upsert_many(
            batch,
            [
                _session("s1", "octo/api"),
                _session("s2", "octo/api"),
                _session("s3", "octo/web"),
                _session("s4", None),  # session sans dépôt
                _session("s5", "octo/ghost"),  # dépôt non déclaré -> non résolu
            ],
        )
        uow.commit()
    return database


def _repo_ids(database: Database) -> dict[str, int | None]:
    with database.engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT s.external_id, r.name "
                "FROM session s LEFT JOIN repository r ON r.id = s.repository_id"
            )
        ).all()
    return dict(rows)


def test_sessions_are_linked_to_their_repository(seeded: Database) -> None:
    links = _repo_ids(seeded)
    assert links == {
        "s1": "octo/api",
        "s2": "octo/api",
        "s3": "octo/web",
        "s4": None,  # pas de dépôt
        "s5": None,  # "octo/ghost" jamais déclaré -> rattachement best-effort à NULL
    }


def test_list_code_repositories(seeded: Database) -> None:
    ref = SqlReferenceRepository(seeded.create_session())

    swe = ref.list_code_repositories("swe-chat")
    assert [r.name for r in swe] == ["octo/api", "octo/infra", "octo/web"]
    api = next(r for r in swe if r.name == "octo/api")
    assert (api.url, api.language) == ("https://x/api", "python")

    every = ref.list_code_repositories()
    assert {r.name for r in every} == {"octo/api", "octo/infra", "octo/web", "other/repo"}
    assert {r.source_name for r in every} == {"swe-chat", "tracelab"}


def test_get_code_repository_round_trips(seeded: Database) -> None:
    ref = SqlReferenceRepository(seeded.create_session())
    got = ref.get_code_repository("swe-chat", "octo/web")
    assert got == Repository(
        source_name="swe-chat", name="octo/web", url="https://x/web", language="typescript"
    )
    assert ref.get_code_repository("swe-chat", "absent") is None


def test_dashboard_can_filter_by_repository(seeded: Database) -> None:
    svc = SqlMetricsQueryService(seeded.create_session())

    only_api = svc.sessions(MetricFilter(repositories=("octo/api",)), Page())
    assert only_api.total == 2
    assert {i.repository_name for i in only_api.items} == {"octo/api"}

    api_or_web = svc.sessions(MetricFilter(repositories=("octo/api", "octo/web")), Page())
    assert api_or_web.total == 3


def test_session_list_and_detail_expose_repository_name(seeded: Database) -> None:
    svc = SqlMetricsQueryService(seeded.create_session())

    by_ext = {i.session_id: i for i in svc.sessions(MetricFilter(), Page()).items}
    assert any(i.repository_name == "octo/api" for i in by_ext.values())
    assert any(i.repository_name is None for i in by_ext.values())  # s4 / s5

    with seeded.engine.connect() as conn:
        sid = conn.execute(text("SELECT id FROM session WHERE external_id = 's3'")).scalar_one()
    detail = svc.session_detail(sid)
    assert detail is not None
    assert detail.repository_name == "octo/web"


def test_indicators_scoped_to_a_repository(seeded: Database) -> None:
    svc = SqlMetricsQueryService(seeded.create_session())
    assert svc.indicators(MetricFilter(repositories=("octo/api",))).session_count == 2
    assert svc.indicators(MetricFilter(repositories=("octo/ghost",))).session_count == 0
