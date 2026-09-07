"""Les ports repository sont des interfaces typées, sans implémentation ni dépendance
framework (DoD de l'issue I1.4)."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterable

import pytest

from agentscope.application.ports import (
    ImportRepository,
    SessionRepository,
    UnitOfWork,
    UpsertOutcome,
)
from agentscope.application.ports import repositories as ports_module
from agentscope.domain import ImportBatch, Session

ALL_PORTS = [
    "ReferenceRepository",
    "MappingRepository",
    "ImportRepository",
    "RawRecordRepository",
    "SessionRepository",
    "ModelCallRepository",
    "ToolCallRepository",
    "RejectRepository",
    "FieldProfileRepository",
]


@pytest.mark.parametrize("name", ALL_PORTS)
def test_each_port_is_a_protocol(name: str) -> None:
    port = getattr(ports_module, name)
    assert getattr(port, "_is_protocol", False), f"{name} n'est pas un Protocol"
    with pytest.raises(TypeError):
        port()  # un Protocol ne s'instancie pas


def test_unit_of_work_is_a_protocol() -> None:
    assert getattr(UnitOfWork, "_is_protocol", False)


class TestUpsertOutcome:
    def test_total_and_sum(self) -> None:
        assert UpsertOutcome(inserted=2, skipped=1).total == 3
        combined = UpsertOutcome(2, 1) + UpsertOutcome(5, 3)
        assert combined == UpsertOutcome(inserted=7, skipped=4)

    def test_empty(self) -> None:
        assert UpsertOutcome.empty() == UpsertOutcome(0, 0)


def test_structural_conformance_with_a_fake() -> None:
    """Un adaptateur en mémoire minimal satisfait le port (typage structurel)."""

    class InMemorySessionRepository:
        def __init__(self) -> None:
            self.saved: list[Session] = []

        def upsert_many(
            self, batch: ImportBatch, sessions: Iterable[Session]
        ) -> UpsertOutcome:
            new = [s for s in sessions if s not in self.saved]
            self.saved.extend(new)
            return UpsertOutcome(inserted=len(new), skipped=0)

    fake: SessionRepository = InMemorySessionRepository()
    assert isinstance(fake, SessionRepository)
    assert not isinstance(object(), ImportRepository)


def test_ports_layer_imports_no_framework() -> None:
    code = (
        "import sys; "
        "import agentscope.application.ports.repositories; "
        "import agentscope.application.ports.unit_of_work; "
        "print(','.join(sorted(m.split('.')[0] for m in sys.modules)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    loaded = set(result.stdout.strip().split(","))
    forbidden = {"sqlalchemy", "fastapi", "starlette", "alembic", "httpx", "pydantic"}
    assert not (loaded & forbidden), f"import interdit : {sorted(loaded & forbidden)}"
