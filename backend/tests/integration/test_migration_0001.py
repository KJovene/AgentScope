"""La migration 0001 crée le schéma v1 et les contraintes d'unicité (idempotence).

DoD de l'issue I1.3 : ``alembic upgrade head`` crée toutes les tables ; les
contraintes qui empêchent le doublement au réimport sont vérifiées.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

import agentscope.infrastructure.persistence as persistence_pkg

MIGRATIONS_DIR = Path(persistence_pkg.__file__).parent / "migrations"

EXPECTED_TABLES = {
    "source",
    "repository",
    "mapping",
    "import_batch",
    "raw_record",
    "session",
    "model_call",
    "tool_call",
    "import_reject",
    "field_profile",
}

_TS = "2026-01-01T00:00:00+00:00"


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    url = f"sqlite:///{tmp_path / 'agentscope_test.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    eng = create_engine(url)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture
def seeded(engine: Engine) -> tuple[Engine, dict[str, int]]:
    """Insère une source, un mapping, un import et une session valides."""
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO source (name) VALUES ('tracelab')"))
        source_id = conn.execute(text("SELECT id FROM source")).scalar_one()
        conn.execute(
            text(
                "INSERT INTO mapping "
                "(source_id, name, version, source_format, definition_json, is_active, created_at) "
                "VALUES (:s, 'tracelab-jsonl', 1, 'jsonl', '{}', 1, :ts)"
            ),
            {"s": source_id, "ts": _TS},
        )
        mapping_id = conn.execute(text("SELECT id FROM mapping")).scalar_one()
        conn.execute(
            text(
                "INSERT INTO import_batch (source_id, mapping_id, original_filename, "
                "file_sha256, file_format, status, imported_at) "
                "VALUES (:s, :m, 'sessions.jsonl', 'SHA-DEADBEEF', 'jsonl', 'succeeded', :ts)"
            ),
            {"s": source_id, "m": mapping_id, "ts": _TS},
        )
        batch_id = conn.execute(text("SELECT id FROM import_batch")).scalar_one()
        conn.execute(
            text(
                "INSERT INTO session (source_id, import_batch_id, external_id) "
                "VALUES (:s, :b, 'sess-1')"
            ),
            {"s": source_id, "b": batch_id},
        )
        session_id = conn.execute(text("SELECT id FROM session")).scalar_one()
    return engine, {
        "source_id": source_id,
        "mapping_id": mapping_id,
        "batch_id": batch_id,
        "session_id": session_id,
    }


def test_creates_all_tables_and_stamps_version(engine: Engine) -> None:
    inspector = inspect(engine)
    names = set(inspector.get_table_names())
    assert names >= EXPECTED_TABLES
    version = None
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert version == "0001_initial"


@pytest.mark.parametrize(
    ("table", "columns"),
    [
        ("import_batch", {"source_id", "file_sha256"}),
        ("session", {"source_id", "external_id"}),
        ("model_call", {"session_id", "sequence"}),
        ("tool_call", {"session_id", "sequence"}),
        ("raw_record", {"import_batch_id", "record_index"}),
        ("field_profile", {"import_batch_id", "path"}),
    ],
)
def test_idempotence_unique_constraints_declared(
    engine: Engine, table: str, columns: set[str]
) -> None:
    inspector = inspect(engine)
    declared = [set(u["column_names"]) for u in inspector.get_unique_constraints(table)]
    assert columns in declared, f"{table} : contrainte unique {columns} absente (vu : {declared})"


def test_reimport_same_file_is_rejected_by_unique(seeded: tuple[Engine, dict[str, int]]) -> None:
    engine, ids = seeded
    insert_same_batch = text(
        "INSERT INTO import_batch "
        "(source_id, mapping_id, original_filename, file_sha256, file_format, status, imported_at) "
        "VALUES (:s, :m, 'sessions.jsonl', 'SHA-DEADBEEF', 'jsonl', 'succeeded', :ts)"
    )
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(
            insert_same_batch,
            {"s": ids["source_id"], "m": ids["mapping_id"], "ts": _TS},
        )


def test_duplicate_session_external_id_is_rejected_by_unique(
    seeded: tuple[Engine, dict[str, int]],
) -> None:
    engine, ids = seeded
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO session (source_id, import_batch_id, external_id) "
                "VALUES (:s, :b, 'sess-1')"
            ),
            {"s": ids["source_id"], "b": ids["batch_id"]},
        )


def test_duplicate_model_call_sequence_is_rejected_by_unique(
    seeded: tuple[Engine, dict[str, int]],
) -> None:
    engine, ids = seeded
    insert_call = text(
        "INSERT INTO model_call (session_id, import_batch_id, sequence, model_name, status) "
        "VALUES (:sess, :b, 0, 'claude-sonnet', 'success')"
    )
    with engine.begin() as conn:
        conn.execute(insert_call, {"sess": ids["session_id"], "b": ids["batch_id"]})
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(insert_call, {"sess": ids["session_id"], "b": ids["batch_id"]})


def test_check_constraint_rejects_unknown_status(
    seeded: tuple[Engine, dict[str, int]],
) -> None:
    engine, ids = seeded
    insert_bad_status = text(
        "INSERT INTO model_call "
        "(session_id, import_batch_id, sequence, model_name, status) "
        "VALUES (:sess, :b, 1, 'm', 'not-a-real-status')"
    )
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(insert_bad_status, {"sess": ids["session_id"], "b": ids["batch_id"]})


def test_downgrade_drops_everything(engine: Engine, tmp_path: Path) -> None:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", str(engine.url))
    command.downgrade(cfg, "base")

    remaining = set(inspect(engine).get_table_names()) - {"alembic_version"}
    assert remaining == set()
