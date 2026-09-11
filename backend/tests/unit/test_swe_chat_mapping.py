"""Mapping intégré SWE-chat (issue I2.12).

La fixture reproduit le schéma réel de la table ``conversations`` du dataset
``SALT-NLP/SWE-chat`` (une ligne = un tour), tel qu'aplati par
``scripts/swe_chat_extract.py`` : ``turn_type`` porte la nature du tour,
les tokens par tour sont pauvres (seul ``output_tokens`` est exploitable) et
les timestamps peuvent manquer (agents Codex / OpenCode).
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from agentscope.application.mapping.contract import MappingDefinition
from agentscope.application.mapping.normalizer import Normalizer
from agentscope.infrastructure.readers.jsonl_reader import JsonlReader

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "backend" / "tests" / "fixtures" / "swe_chat" / "sample.jsonl"
MAPPING = ROOT / "docs" / "data" / "mappings" / "swe-chat.json"


def _normalize():
    records = list(JsonlReader().read(BytesIO(FIXTURE.read_bytes())))
    mapping = MappingDefinition.from_dict(json.loads(MAPPING.read_text(encoding="utf-8")))
    return Normalizer().normalize(records, mapping)


def test_bout_en_bout_swe_chat() -> None:
    result = _normalize()

    assert result.rejects == ()
    assert {s.external_id for s in result.sessions} == {"swe-a", "swe-b"}
    assert {s.agent_name for s in result.sessions} == {"Claude Code", "Codex"}
    assert {s.repository_name for s in result.sessions} == {"acme/widgets", "acme/api"}

    # model_call = tour `assistant_response`. `model_name` = `model` sinon, à défaut,
    # l'`agent` (coalesce) : swe-a#5 (assistant_response sans model) devient un
    # appel « Claude Code » au lieu d'être perdu.
    assert {(m.session_external_id, m.model_name) for m in result.model_calls} == {
        ("swe-a", "claude-opus-4-6"),
        ("swe-a", "Claude Code"),
        ("swe-b", "gpt-5-codex"),
    }
    swe_a_opus = next(m for m in result.model_calls if m.model_name == "claude-opus-4-6")
    assert swe_a_opus.tokens.completion_tokens == 200
    assert swe_a_opus.tokens.cached_tokens == 5000

    # tool_call = tour `tool_use`
    assert {(t.session_external_id, t.tool_name) for t in result.tool_calls} == {
        ("swe-a", "Read"),
        ("swe-b", "bash"),
    }


def test_session_interval_deduit_quand_les_tours_sont_horodates() -> None:
    result = _normalize()
    by_id = {s.external_id: s for s in result.sessions}

    # swe-a : appels horodatés -> enveloppe déduite du min/max de leurs timestamps
    # (1er appel @ 20:37:25, dernier @ 20:37:31).
    assert by_id["swe-a"].interval.started_at is not None
    assert by_id["swe-a"].duration_ms == 6000

    # swe-b : aucun tour horodaté -> reste NULL, signalé dans missing_info
    assert by_id["swe-b"].interval.started_at is None
    assert result.missing_info.get("session.started_at") == 1
