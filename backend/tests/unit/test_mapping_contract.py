"""Lecture du contrat de mapping (``docs/PLAN.md`` §5.1) depuis un dict."""

from __future__ import annotations

import pytest

from agentscope.application.mapping.contract import (
    MappingDefinition,
    OnError,
    WhereOp,
)
from agentscope.domain import InvalidMappingError

VALID_MAPPING = {
    "name": "tracelab-jsonl",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "TraceLab"},
    "entities": {
        "session": {
            "iterate": {"path": "", "where": []},
            "identity": {"key_fields": ["session_id"]},
            "fields": {
                "external_id": {
                    "from": "session_id",
                    "transform": "identity",
                    "required": True,
                    "on_error": "reject",
                },
                "agent_name": {"from": "provider", "transform": "lower"},
            },
        },
        "model_call": {
            "iterate": {"path": "events", "where": [["type", "eq", "model"]]},
            "parent": {"entity": "session", "key_from": "session_id"},
            "identity": {"key_fields": ["session_id", "seq"]},
            "fields": {
                "model_name": {
                    "from": "model",
                    "transform": "identity",
                    "required": True,
                    "on_error": "reject",
                },
            },
        },
    },
    "unmapped_fields": ["debug"],
}


def test_lit_un_mapping_complet() -> None:
    mapping = MappingDefinition.from_dict(VALID_MAPPING)

    assert mapping.name == "tracelab-jsonl"
    assert mapping.version == 1
    assert mapping.constants["source_name"] == "TraceLab"
    assert mapping.unmapped_fields == ("debug",)
    assert {e.name for e in mapping.entities} == {"session", "model_call"}


def test_expose_les_details_d_une_entite() -> None:
    mapping = MappingDefinition.from_dict(VALID_MAPPING)
    model_call = mapping.entity("model_call")

    assert model_call is not None
    assert model_call.key_fields == ("session_id", "seq")
    assert model_call.parent is not None
    assert model_call.parent.entity == "session"
    assert model_call.iterate.path == "events"
    assert model_call.iterate.where[0].op is WhereOp.EQ
    assert model_call.field("model_name").required is True
    assert model_call.field("model_name").on_error is OnError.REJECT


def test_on_error_par_defaut_est_null() -> None:
    mapping = MappingDefinition.from_dict(VALID_MAPPING)

    assert mapping.entity("session").field("agent_name").on_error is OnError.NULL


@pytest.mark.parametrize(
    ("mutation", "message_fragment"),
    [
        ({"name": ""}, "name"),
        ({"version": "1"}, "version"),
        ({"entities": {}}, "entité"),
    ],
)
def test_rejette_une_structure_cassee(mutation: dict, message_fragment: str) -> None:
    broken = {**VALID_MAPPING, **mutation}

    with pytest.raises(InvalidMappingError) as error:
        MappingDefinition.from_dict(broken)
    assert message_fragment in str(error.value)


def test_rejette_un_operateur_de_filtre_inconnu() -> None:
    broken = {
        **VALID_MAPPING,
        "entities": {
            "session": {
                "iterate": {"path": "", "where": [["type", "matches", "x"]]},
                "identity": {"key_fields": ["session_id"]},
                "fields": {"external_id": {"from": "session_id"}},
            }
        },
    }

    with pytest.raises(InvalidMappingError, match="matches"):
        MappingDefinition.from_dict(broken)


def test_rejette_un_on_error_inconnu() -> None:
    broken = {
        **VALID_MAPPING,
        "entities": {
            "session": {
                "identity": {"key_fields": ["session_id"]},
                "fields": {"external_id": {"from": "session_id", "on_error": "explode"}},
            }
        },
    }

    with pytest.raises(InvalidMappingError, match="explode"):
        MappingDefinition.from_dict(broken)
