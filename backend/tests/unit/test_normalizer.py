"""``Normalizer`` (issue I2.6) : mapping + RawRecord -> entités + rejets + manquants."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agentscope.application.mapping.contract import MappingDefinition
from agentscope.application.mapping.normalizer import Normalizer
from agentscope.domain import CallStatus, RawRecord, RejectReason

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "tracelab" / "sample.jsonl"

BASE_MAPPING = {
    "name": "demo",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "Demo"},
    "entities": {
        "session": {
            "iterate": {"path": ""},
            "identity": {"key_fields": ["sid"]},
            "fields": {
                "external_id": {"from": "sid", "required": True, "on_error": "reject"},
                "agent_name": {"from": "agent", "transform": "lower"},
            },
        },
        "model_call": {
            "iterate": {"path": "calls", "where": [["kind", "eq", "model"]]},
            "parent": {"entity": "session", "key_from": "sid"},
            "identity": {"key_fields": ["sid", "seq"]},
            "fields": {
                "sequence": {"from": "seq", "transform": "to_int"},
                "model_name": {"from": "model", "required": True, "on_error": "reject"},
                "prompt_tokens": {"from": "tokens_in", "transform": "to_int"},
            },
        },
    },
}


def _mapping(raw: dict | None = None) -> MappingDefinition:
    return MappingDefinition.from_dict(raw or BASE_MAPPING)


def _record(index: int, payload: dict) -> RawRecord:
    blob = json.dumps(payload).encode()
    return RawRecord(index=index, payload=payload, sha256=hashlib.sha256(blob).hexdigest())


def test_produit_session_et_appels() -> None:
    record = _record(
        0,
        {
            "sid": "s1",
            "agent": "Claude",
            "calls": [
                {"kind": "model", "seq": 0, "model": "gpt", "tokens_in": "120"},
                {"kind": "tool", "seq": 1, "name": "grep"},  # filtré (kind != model)
            ],
        },
    )

    result = Normalizer().normalize([record], _mapping())

    assert [s.external_id for s in result.sessions] == ["s1"]
    assert result.sessions[0].agent_name == "claude"
    assert len(result.model_calls) == 1
    assert result.model_calls[0].tokens.prompt_tokens == 120
    assert result.model_calls[0].session_external_id == "s1"
    assert result.rejects == ()


def test_ligne_illisible_part_en_rejet_sans_stopper_le_reste() -> None:
    broken = RawRecord(index=0, payload={}, sha256="a" * 64, parse_error="invalid JSON: x")
    good = _record(1, {"sid": "s2", "agent": "codex", "calls": []})

    result = Normalizer().normalize([broken, good], _mapping())

    assert len(result.rejects) == 1
    assert result.rejects[0].reason is RejectReason.UNPARSEABLE_RECORD
    assert result.rejects[0].record_index == 0
    assert [s.external_id for s in result.sessions] == ["s2"]


def test_champ_requis_absent_rejette_l_enregistrement() -> None:
    record = _record(0, {"agent": "x", "calls": []})  # pas de `sid`

    result = Normalizer().normalize([record], _mapping())

    assert result.sessions == ()
    assert result.rejects[0].reason is RejectReason.MISSING_REQUIRED_FIELD


def test_valeur_absente_toleree_est_comptee_dans_missing_info() -> None:
    record = _record(
        0,
        {"sid": "s1", "calls": [{"kind": "model", "seq": 0, "model": "gpt"}]},  # pas de tokens_in
    )

    result = Normalizer().normalize([record], _mapping())

    assert result.model_calls[0].tokens.prompt_tokens is None
    assert result.missing_info["model_call.prompt_tokens"] == 1
    assert result.missing_info["session.agent_name"] == 1


def test_transform_qui_echoue_avec_on_error_null() -> None:
    mapping = json.loads(json.dumps(BASE_MAPPING))
    mapping["entities"]["model_call"]["fields"]["prompt_tokens"]["on_error"] = "null"
    record = _record(
        0,
        {"sid": "s1", "calls": [{"kind": "model", "seq": 0, "model": "gpt", "tokens_in": "abc"}]},
    )

    result = Normalizer().normalize([record], _mapping(mapping))

    assert result.model_calls[0].tokens.prompt_tokens is None
    assert result.missing_info["model_call.prompt_tokens"] == 1


def test_external_id_synthetise_quand_non_mappe() -> None:
    mapping = json.loads(json.dumps(BASE_MAPPING))
    del mapping["entities"]["session"]["fields"]["external_id"]
    record = _record(0, {"sid": "s1", "calls": []})

    result = Normalizer().normalize([record], _mapping(mapping))

    # sha1("Demo|session|s1")
    assert result.sessions[0].external_id == hashlib.sha1(b"Demo|session|s1").hexdigest()


def test_doublon_dans_le_fichier_ignore_silencieusement() -> None:
    record = _record(0, {"sid": "s1", "agent": "x", "calls": []})

    result = Normalizer().normalize([record, record], _mapping())

    assert len(result.sessions) == 1
    assert result.rejects == ()


def test_reimport_produit_le_meme_resultat() -> None:
    records = [_record(0, {"sid": "s1", "agent": "x", "calls": []})]
    normalizer = Normalizer()

    first = normalizer.normalize(records, _mapping())
    second = normalizer.normalize(records, _mapping())

    assert first == second


# ---------------------------------------------------------------------------
# Bout-en-bout sur l'extrait TraceLab réel (DoD de l'issue I2.6)
# ---------------------------------------------------------------------------

TRACELAB_MAPPING_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "data" / "mappings" / "tracelab.json"
)


def _tracelab_records() -> list[RawRecord]:
    records = []
    with FIXTURE.open(encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            if not line.strip():
                continue
            payload = json.loads(line)
            records.append(_record(index, payload))
    return records


def test_bout_en_bout_tracelab() -> None:
    records = _tracelab_records()

    mapping = MappingDefinition.from_dict(
        json.loads(TRACELAB_MAPPING_PATH.read_text(encoding="utf-8"))
    )
    result = Normalizer().normalize(records, mapping)

    assert result.rejects == ()
    # 2 sessions (claude + codex), 103 rounds -> 103 model_calls
    assert {s.external_id for s in result.sessions} == {
        "claude:3954969b-4831-6a10-935f-77f37fb5698c",
        "codex:b9f544c9-4be2-91ec-1a77-a51050b2c473",
    }
    assert len(result.model_calls) == 103
    assert all(mc.model_name for mc in result.model_calls)
    assert len(result.tool_calls) > 0
    # les appels sont bien rattachés à une session connue
    known = {s.external_id for s in result.sessions}
    assert all(mc.session_external_id in known for mc in result.model_calls)
    assert all(tc.session_external_id in known for tc in result.tool_calls)
    # statut cohérent (pas d'exception d'invariant)
    assert any(tc.status is CallStatus.ERROR for tc in result.tool_calls)


def test_tracelab_reimport_zero_doublon() -> None:
    records = _tracelab_records()
    normalizer = Normalizer()
    mapping = MappingDefinition.from_dict(
        json.loads(TRACELAB_MAPPING_PATH.read_text(encoding="utf-8"))
    )

    first = normalizer.normalize(records, mapping)
    second = normalizer.normalize(records + records, mapping)  # fichier "doublé"

    assert len(second.sessions) == len(first.sessions)
    assert len(second.model_calls) == len(first.model_calls)
    assert len(second.tool_calls) == len(first.tool_calls)


def test_from_path_indexe_les_listes() -> None:
    """Un segment entier d'un chemin ``from`` indexe une liste, négatif compris."""
    mapping = {
        "name": "demo",
        "version": 1,
        "source_format": "jsonl",
        "constants": {"source_name": "Demo"},
        "entities": {
            "session": {
                "iterate": {"path": ""},
                "identity": {"key_fields": ["sid"]},
                "fields": {
                    "external_id": {"from": "sid", "required": True, "on_error": "reject"},
                    "started_at": {"from": "events.0.ts"},
                    "ended_at": {"from": "events.-1.ts"},
                },
            }
        },
    }
    record = _record(
        0,
        {
            "sid": "s1",
            "events": [
                {"ts": "2026-01-01T00:00:00Z"},
                {"ts": "2026-01-01T00:00:05Z"},
                {"ts": "2026-01-01T00:00:09Z"},
            ],
        },
    )

    result = Normalizer().normalize([record], _mapping(mapping))

    assert result.rejects == ()
    session = result.sessions[0]
    assert session.interval.started_at is not None
    assert session.interval.ended_at is not None
    assert session.interval.duration_ms == 9_000


_INTERVAL_MAPPING = {
    "name": "demo",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "Demo"},
    "entities": {
        "session": {
            "iterate": {"path": ""},
            "identity": {"key_fields": ["sid"]},
            "fields": {
                "external_id": {"from": "sid", "required": True, "on_error": "reject"},
                "started_at": {"from": "s_start"},
                "ended_at": {"from": "s_end"},
            },
        },
        "model_call": {
            "iterate": {"path": "calls"},
            "parent": {"entity": "session", "key_from": "sid"},
            "identity": {"key_fields": ["sid", "seq"]},
            "fields": {
                "sequence": {"from": "seq", "transform": "to_int"},
                "model_name": {"from": "model", "required": True, "on_error": "reject"},
                "started_at": {"from": "t0"},
                "ended_at": {"from": "t1"},
            },
        },
    },
}


def _round(sid: str, seq: int, t0: str, t1: str, **session_times: str) -> RawRecord:
    return _record(
        seq,
        {
            "sid": sid,
            **session_times,
            "calls": [{"seq": seq, "model": "gpt", "t0": t0, "t1": t1}],
        },
    )


def test_backfill_deduit_l_enveloppe_quand_la_session_n_est_pas_bornee() -> None:
    records = [
        _round("s1", 0, "2026-01-01T09:00:00Z", "2026-01-01T09:00:30Z"),
        _round("s1", 1, "2026-01-01T09:05:00Z", "2026-01-01T09:07:00Z"),
    ]

    result = Normalizer().normalize(records, _mapping(_INTERVAL_MAPPING))

    session = result.sessions[0]
    assert session.interval.started_at.isoformat() == "2026-01-01T09:00:00+00:00"
    assert session.interval.ended_at.isoformat() == "2026-01-01T09:07:00+00:00"
    assert session.duration_ms == 420_000
    assert "session.started_at" not in result.missing_info
    assert "session.ended_at" not in result.missing_info


def test_backfill_ne_touche_pas_une_borne_deja_mappee() -> None:
    records = [
        _round(
            "s1",
            0,
            "2026-01-01T09:00:00Z",
            "2026-01-01T09:30:00Z",
            s_start="2026-01-01T08:00:00Z",  # mappé -> conservé
        ),
    ]

    result = Normalizer().normalize(records, _mapping(_INTERVAL_MAPPING))

    session = result.sessions[0]
    assert session.interval.started_at.isoformat() == "2026-01-01T08:00:00+00:00"  # mappé
    assert session.interval.ended_at.isoformat() == "2026-01-01T09:30:00+00:00"  # déduit


def test_backfill_laisse_null_sans_appel_horodate() -> None:
    record = _record(0, {"sid": "s1", "calls": [{"seq": 0, "model": "gpt"}]})

    result = Normalizer().normalize([record], _mapping(_INTERVAL_MAPPING))

    assert result.sessions[0].interval.started_at is None
    assert result.sessions[0].interval.ended_at is None


def test_from_path_index_hors_bornes_est_absent() -> None:
    mapping = {
        "name": "demo",
        "version": 1,
        "source_format": "jsonl",
        "constants": {"source_name": "Demo"},
        "entities": {
            "session": {
                "iterate": {"path": ""},
                "identity": {"key_fields": ["sid"]},
                "fields": {
                    "external_id": {"from": "sid", "required": True, "on_error": "reject"},
                    "started_at": {"from": "events.5.ts"},
                },
            }
        },
    }
    record = _record(0, {"sid": "s1", "events": [{"ts": "2026-01-01T00:00:00Z"}]})

    result = Normalizer().normalize([record], _mapping(mapping))

    assert result.rejects == ()
    assert result.sessions[0].interval.started_at is None
    assert result.missing_info.get("session.started_at") == 1
