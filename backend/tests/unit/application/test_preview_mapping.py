"""``PreviewMapping`` (issue I3.9) : dry-run de normalisation, sans écriture DB."""

from __future__ import annotations

from collections.abc import Iterator
from io import BufferedIOBase

import pytest

from agentscope.application.mapping.validator import parse_and_validate
from agentscope.application.use_cases.preview_mapping import (
    PreviewFailedError,
    PreviewMapping,
)
from agentscope.domain import FileFormat, RawRecord

MAPPING = parse_and_validate(
    {
        "name": "demo",
        "version": 1,
        "source_format": "jsonl",
        "constants": {"source_name": "Demo"},
        "entities": {
            "session": {
                "iterate": {"path": "", "where": []},
                "identity": {"key_fields": ["sid"]},
                "fields": {
                    "external_id": {
                        "from": "sid",
                        "transform": "identity",
                        "required": True,
                        "on_error": "reject",
                    },
                    "agent_name": {"from": "agent", "transform": "lower"},
                },
            },
        },
    }
)


class _FakeReader:
    """Lecteur en mémoire : ignore le contenu binaire, renvoie des `RawRecord` fixés."""

    def __init__(self, file_format: str, records: list[RawRecord]) -> None:
        self._file_format = file_format
        self._records = records

    def supports(self, file_format: str) -> bool:
        return file_format == self._file_format

    def read(self, source: BufferedIOBase) -> Iterator[RawRecord]:
        yield from self._records


def _records(count: int, *, missing_agent_from: int | None = None) -> list[RawRecord]:
    records = []
    for i in range(count):
        payload: dict[str, object] = {"sid": f"s{i}"}
        if missing_agent_from is None or i < missing_agent_from:
            payload["agent"] = "Claude"
        records.append(RawRecord(index=i, payload=payload, sha256=f"sha-{i}"))
    return records


def test_echantillon_plus_petit_que_le_fichier_est_tronque() -> None:
    reader = _FakeReader("jsonl", _records(10))
    preview = PreviewMapping([reader])

    report = preview.execute(
        content=b"unused", file_format=FileFormat.JSONL, mapping=MAPPING, sample_size=3
    )

    assert report.sampled_count == 3
    assert len(report.result.sessions) == 3


def test_echantillon_plus_grand_que_le_fichier_prend_tout() -> None:
    reader = _FakeReader("jsonl", _records(2))
    preview = PreviewMapping([reader])

    report = preview.execute(
        content=b"unused", file_format=FileFormat.JSONL, mapping=MAPPING, sample_size=50
    )

    assert report.sampled_count == 2
    assert len(report.result.sessions) == 2


def test_les_rejets_simules_sont_rapportes() -> None:
    records = _records(3)
    broken = RawRecord(index=99, payload={}, sha256="sha-broken")  # pas de `sid` -> requis manquant
    reader = _FakeReader("jsonl", [*records, broken])
    preview = PreviewMapping([reader])

    report = preview.execute(
        content=b"unused", file_format=FileFormat.JSONL, mapping=MAPPING, sample_size=50
    )

    assert report.sampled_count == 4
    assert len(report.result.sessions) == 3
    assert len(report.result.rejects) == 1


def test_les_valeurs_manquantes_tolerees_sont_comptees() -> None:
    reader = _FakeReader("jsonl", _records(3, missing_agent_from=1))
    preview = PreviewMapping([reader])

    report = preview.execute(
        content=b"unused", file_format=FileFormat.JSONL, mapping=MAPPING, sample_size=50
    )

    assert report.result.missing_info.get("session.agent_name") == 2


def test_aucune_ecriture_persistante_n_est_effectuee() -> None:
    """Pas d'UnitOfWork : `PreviewMapping` ne dépend d'aucun repository."""
    reader = _FakeReader("jsonl", _records(1))
    preview = PreviewMapping([reader])

    report = preview.execute(
        content=b"unused", file_format=FileFormat.JSONL, mapping=MAPPING, sample_size=1
    )

    assert report.result.sessions[0].external_id == "s0"


def test_aucun_lecteur_pour_le_format_leve_une_erreur() -> None:
    reader = _FakeReader("csv", _records(1))
    preview = PreviewMapping([reader])

    with pytest.raises(PreviewFailedError, match="jsonl"):
        preview.execute(
            content=b"unused", file_format=FileFormat.JSONL, mapping=MAPPING, sample_size=1
        )
