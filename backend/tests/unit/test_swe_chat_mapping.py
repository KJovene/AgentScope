"""Mapping integre SWE-chat (issue I2.12)."""

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


def test_bout_en_bout_swe_chat() -> None:
    records = list(JsonlReader().read(BytesIO(FIXTURE.read_bytes())))
    mapping = MappingDefinition.from_dict(json.loads(MAPPING.read_text(encoding="utf-8")))

    result = Normalizer().normalize(records, mapping)

    assert result.rejects == ()
    assert {session.external_id for session in result.sessions} == {"swe-001", "swe-002"}
    assert {session.repository_name for session in result.sessions} == {
        "octocat/hello",
        "psf/requests",
    }
    assert len(result.model_calls) == 3
    assert result.model_calls[0].tokens.prompt_tokens == 120
    assert result.model_calls[2].tokens.completion_tokens == 120
    assert len(result.tool_calls) == 2
    assert {(call.session_external_id, call.model_call_sequence) for call in result.tool_calls} == {
        ("swe-001", 0),
        ("swe-002", 0),
    }
