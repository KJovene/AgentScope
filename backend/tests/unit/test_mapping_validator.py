"""Validation sémantique d'un mapping (issue I2.13) : mapping invalide -> refus expliqué."""

from __future__ import annotations

import copy

import pytest

from agentscope.application.mapping.validator import parse_and_validate, validate_mapping
from agentscope.domain import InvalidMappingError

VALID = {
    "name": "tracelab-jsonl",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "TraceLab"},
    "entities": {
        "session": {
            "iterate": {"path": "", "where": []},
            "identity": {"key_fields": ["session_id"]},
            "fields": {
                "external_id": {"from": "session_id", "transform": "identity",
                                "required": True, "on_error": "reject"},
                "agent_name": {"from": "provider", "transform": "lower"},
            },
        },
        "model_call": {
            "iterate": {"path": "events", "where": [["type", "eq", "model"]]},
            "parent": {"entity": "session", "key_from": "session_id"},
            "identity": {"key_fields": ["session_id", "seq"]},
            "fields": {
                "model_name": {"from": "model", "transform": "identity",
                               "required": True, "on_error": "reject"},
                "prompt_tokens": {"from": "usage.input_tokens", "transform": "to_int"},
            },
        },
    },
}


def _mutant(**entity_overrides: dict) -> dict:
    data = copy.deepcopy(VALID)
    data["entities"].update(entity_overrides)
    return data


def test_un_mapping_correct_passe() -> None:
    validate_mapping(parse_and_validate(VALID))  # ne lève rien


def test_schema_json_refuse_une_structure_invalide_avec_un_message_explicite() -> None:
    broken = copy.deepcopy(VALID)
    del broken["version"]
    broken["entities"]["session"]["identity"]["key_fields"] = []

    with pytest.raises(InvalidMappingError, match="Mapping JSON invalide") as error:
        parse_and_validate(broken)

    message = str(error.value)
    assert "version" in message
    assert "key_fields" in message


def test_champ_cible_inconnu_est_refuse() -> None:
    broken = _mutant(session={
        "identity": {"key_fields": ["session_id"]},
        "fields": {
            "external_id": {"from": "session_id"},
            "nb_bananes": {"from": "x", "transform": "to_int"},
        },
    })

    with pytest.raises(InvalidMappingError, match="nb_bananes"):
        parse_and_validate(broken)


def test_transform_non_whitelistee_est_refusee() -> None:
    broken = _mutant(session={
        "identity": {"key_fields": ["session_id"]},
        "fields": {"external_id": {"from": "session_id", "transform": "exec_python"}},
    })

    with pytest.raises(InvalidMappingError, match="exec_python"):
        parse_and_validate(broken)


def test_champ_requis_non_mappe_est_refuse() -> None:
    broken = _mutant(model_call={
        "parent": {"entity": "session", "key_from": "session_id"},
        "identity": {"key_fields": ["session_id", "seq"]},
        "fields": {"prompt_tokens": {"from": "usage.input_tokens", "transform": "to_int"}},
    })

    with pytest.raises(InvalidMappingError, match="model_name"):
        parse_and_validate(broken)


def test_from_manquant_est_refuse_sauf_const() -> None:
    broken = _mutant(session={
        "identity": {"key_fields": ["session_id"]},
        "fields": {
            "external_id": {"from": "session_id"},
            "agent_name": {"transform": "identity"},  # pas de `from`
        },
    })

    with pytest.raises(InvalidMappingError, match="from` manquant"):
        parse_and_validate(broken)


def test_const_sans_valeur_est_refuse() -> None:
    broken = _mutant(session={
        "identity": {"key_fields": ["session_id"]},
        "fields": {
            "external_id": {"from": "session_id"},
            "agent_name": {"transform": "const", "args": {}},
        },
    })

    with pytest.raises(InvalidMappingError, match="args.value"):
        parse_and_validate(broken)


def test_parent_vers_entite_non_declaree_est_refuse() -> None:
    broken = _mutant(model_call={
        "parent": {"entity": "run", "key_from": "session_id"},
        "identity": {"key_fields": ["session_id", "seq"]},
        "fields": {"model_name": {"from": "model"}},
    })

    with pytest.raises(InvalidMappingError, match="run"):
        parse_and_validate(broken)


def test_appel_sans_parent_est_refuse() -> None:
    broken = _mutant(model_call={
        "identity": {"key_fields": ["session_id", "seq"]},
        "fields": {"model_name": {"from": "model"}},
    })

    with pytest.raises(InvalidMappingError, match="parent` manquant"):
        parse_and_validate(broken)


def test_toutes_les_erreurs_sont_listees_d_un_coup() -> None:
    broken = _mutant(session={
        "identity": {"key_fields": ["session_id"]},
        "fields": {
            "external_id": {"from": "session_id"},
            "zzz": {"from": "x", "transform": "nope"},
        },
    })

    with pytest.raises(InvalidMappingError) as error:
        parse_and_validate(broken)
    message = str(error.value)
    assert "zzz" in message and "nope" in message
