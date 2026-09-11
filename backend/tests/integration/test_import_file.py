"""Cas d'utilisation ``ImportFile`` (issues I2.8 / I2.7) : orchestration, bilan, idempotence."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from agentscope.application.use_cases.import_file import ImportFailedError, ImportFile
from agentscope.domain import FileFormat, ImportStatus, Source, SourceMapping
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from agentscope.infrastructure.readers.csv_reader import CsvReader
from agentscope.infrastructure.readers.jsonl_reader import JsonlReader
from agentscope.infrastructure.readers.parquet_reader import ParquetReader

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
MakeUow = Callable[[], SqlAlchemyUnitOfWork]

MAPPING_DEF = {
    "name": "demo-jsonl",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "demo"},
    "entities": {
        "session": {
            "iterate": {"path": ""},
            "identity": {"key_fields": ["sid"]},
            "fields": {
                "external_id": {"from": "sid", "required": True, "on_error": "reject"},
                "agent_name": {"from": "agent"},
            },
        },
        "model_call": {
            "iterate": {"path": ""},
            "parent": {"entity": "session", "key_from": "sid"},
            "identity": {"key_fields": ["sid", "round"]},
            "fields": {
                "sequence": {"from": "round", "transform": "to_int"},
                "model_name": {"from": "model", "required": True, "on_error": "reject"},
                "prompt_tokens": {"from": "tokens_in", "transform": "to_int"},
                "completion_tokens": {"from": "tokens_out", "transform": "to_int"},
            },
        },
        "tool_call": {
            "iterate": {"path": "tools"},
            "parent": {"entity": "session", "key_from": "sid"},
            "identity": {"key_fields": ["sid", "round", "ti"]},
            "fields": {
                "sequence": {"from": "ti", "transform": "to_int"},
                "tool_name": {"from": "name", "required": True, "on_error": "reject"},
            },
        },
    },
}

ROWS = [
    {
        "sid": "s1",
        "agent": "claude",
        "model": "m-1",
        "round": 0,
        "tokens_in": 100,
        "tokens_out": 10,
        "tools": [{"ti": 0, "name": "bash"}],
    },
    {
        "sid": "s1",
        "agent": "claude",
        "model": "m-1",
        "round": 1,
        "tokens_in": 200,
        "tokens_out": 20,
        "tools": [],
    },
    {
        "sid": "s2",
        "agent": "codex",
        "model": "m-2",
        "round": 0,
        "tokens_in": 50,
        "tokens_out": 5,
        "tools": [{"ti": 0, "name": "grep"}, {"ti": 1, "name": "read"}],
    },
    {"agent": "orphan", "model": "m-3", "round": 0},  # pas de `sid` -> rejet
]


def _jsonl(rows: list[dict]) -> bytes:
    return ("\n".join(json.dumps(row) for row in rows)).encode("utf-8")


@pytest.fixture
def seeded(make_uow: MakeUow) -> MakeUow:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="demo", display_name="Demo"))
        uow.mappings.add(
            SourceMapping(
                name="demo-jsonl",
                version=1,
                source_name="demo",
                source_format=FileFormat.JSONL,
                definition=MAPPING_DEF,
                created_at=NOW,
            )
        )
        uow.commit()
    return make_uow


def _import_file(make_uow: MakeUow) -> ImportFile:
    return ImportFile(
        uow_factory=make_uow,
        readers=[JsonlReader(), CsvReader(), ParquetReader()],
        clock=lambda: NOW,
    )


def _counts(database: Database) -> dict[str, int]:
    tables = ["session", "model_call", "tool_call", "raw_record", "import_reject", "import_batch"]
    with database.engine.connect() as conn:
        return {t: conn.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in tables}


# --- orchestration + bilan -------------------------------------------------------


def test_import_produit_un_bilan_et_persiste(seeded: MakeUow, database: Database) -> None:
    report = _import_file(seeded).execute(
        content=_jsonl(ROWS),
        original_filename="demo.jsonl",
        file_format=FileFormat.JSONL,
        mapping_name="demo-jsonl",
    )

    assert report.status is ImportStatus.SUCCEEDED
    assert report.record_count == 4
    assert report.rejected_count == 1  # la ligne sans `sid`
    assert report.imported_count == 2 + 3 + 3  # 2 sessions + 3 model_calls + 3 tool_calls
    assert report.duplicate_count == 0
    assert report.already_imported is False

    counts = _counts(database)
    assert counts["session"] == 2
    assert counts["model_call"] == 3
    assert counts["tool_call"] == 3
    assert counts["import_reject"] == 1
    assert counts["import_batch"] == 1


def test_bilan_et_rejet_exposent_un_reason_code_explicite(
    seeded: MakeUow, database: Database
) -> None:
    report = _import_file(seeded).execute(
        content=_jsonl(ROWS),
        original_filename="demo.jsonl",
        file_format=FileFormat.JSONL,
        mapping_name="demo-jsonl",
    )

    assert report.rejected_count == 1
    with seeded() as uow:
        rejects = uow.rejects.list_for_import(
            report.source_name, report.file_sha256, limit=10, offset=0
        )

    assert len(rejects) == 1
    assert rejects[0].record_index == 3
    assert rejects[0].reason.value == "missing_required_field"
    assert "sid" in rejects[0].detail


# --- idempotence (issue I2.7) --------------------------------------------------


def test_reimport_du_meme_fichier_ne_cree_aucun_doublon(
    seeded: MakeUow, database: Database
) -> None:
    use_case = _import_file(seeded)
    payload = _jsonl(ROWS)
    common = {
        "original_filename": "demo.jsonl",
        "file_format": FileFormat.JSONL,
        "mapping_name": "demo-jsonl",
    }

    first = use_case.execute(content=payload, **common)
    before = _counts(database)
    second = use_case.execute(content=payload, **common)

    assert first.already_imported is False
    assert second.already_imported is True  # court-circuit sur le sha256
    assert _counts(database) == before  # 0 ligne ajoutée


def test_reimport_fichier_reordonne_passe_par_l_upsert_sans_doublon(
    seeded: MakeUow, database: Database
) -> None:
    """Même contenu, ordre des lignes différent -> autre sha256, mais clés naturelles identiques."""
    use_case = _import_file(seeded)

    use_case.execute(
        content=_jsonl(ROWS),
        original_filename="demo.jsonl",
        file_format=FileFormat.JSONL,
        mapping_name="demo-jsonl",
    )
    before = _counts(database)

    report = use_case.execute(
        content=_jsonl(list(reversed(ROWS))),
        original_filename="demo-reordonne.jsonl",
        file_format=FileFormat.JSONL,
        mapping_name="demo-jsonl",
    )

    assert report.already_imported is False
    assert report.imported_count == 0  # tout est déjà là
    assert report.duplicate_count == 2 + 3 + 3
    row_counts = _counts(database)
    assert row_counts["session"] == before["session"]
    assert row_counts["model_call"] == before["model_call"]
    assert row_counts["tool_call"] == before["tool_call"]
    assert row_counts["import_batch"] == 2  # deux imports enregistrés, mêmes lignes métier


# --- atomicité (issue I2.8) ---------------------------------------------------


def test_un_echec_en_cours_d_import_ne_laisse_rien(seeded: MakeUow, database: Database) -> None:
    class _BoomUow(SqlAlchemyUnitOfWork):
        def __enter__(self) -> SqlAlchemyUnitOfWork:
            super().__enter__()
            original = self.tool_calls.upsert_many

            def explode(*args: object, **kwargs: object) -> None:
                raise RuntimeError("disque plein")

            self.tool_calls.upsert_many = explode  # type: ignore[method-assign]
            _ = original
            return self

    use_case = ImportFile(
        uow_factory=lambda: _BoomUow(database),
        readers=[JsonlReader()],
        clock=lambda: NOW,
    )

    with pytest.raises(RuntimeError, match="disque plein"):
        use_case.execute(
            content=_jsonl(ROWS),
            original_filename="demo.jsonl",
            file_format=FileFormat.JSONL,
            mapping_name="demo-jsonl",
        )

    assert _counts(database) == {
        "session": 0,
        "model_call": 0,
        "tool_call": 0,
        "raw_record": 0,
        "import_reject": 0,
        "import_batch": 0,
    }


# --- erreurs d'entrée --------------------------------------------------------


def test_mapping_absent_leve_une_erreur_explicite(seeded: MakeUow) -> None:
    with pytest.raises(ImportFailedError, match="introuvable"):
        _import_file(seeded).execute(
            content=_jsonl(ROWS),
            original_filename="demo.jsonl",
            file_format=FileFormat.JSONL,
            mapping_name="inconnu",
        )
