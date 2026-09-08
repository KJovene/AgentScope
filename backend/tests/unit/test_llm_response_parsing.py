"""Conversion réponse modèle -> contrat, avec validation (issue I3.11)."""

from __future__ import annotations

import copy
import json

import pytest

from agentscope.application.ports.llm_provider import FieldExplanation, MappingProposal
from agentscope.domain import LLMError
from agentscope.infrastructure.llm.response_parsing import (
    extract_json_object,
    parse_mapping_response,
    parse_mapping_response_text,
)

VALID_DEFINITION = {
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
            },
        },
    },
}

VALID_RESPONSE = {
    "definition": VALID_DEFINITION,
    "explanations": [
        {
            "target_field": "external_id",
            "source_field": "session_id",
            "rationale": "Identifiant unique de session.",
            "confidence": 0.9,
        },
    ],
    "ambiguities": ["Le champ `agent` pourrait être un nom de modèle."],
    "unmapped_fields": ["debug"],
}


def test_reponse_valide_est_convertie_en_mapping_proposal() -> None:
    proposal = parse_mapping_response(VALID_RESPONSE)

    assert isinstance(proposal, MappingProposal)
    assert proposal.definition == VALID_DEFINITION
    assert proposal.explanations == [
        FieldExplanation(
            target_field="external_id",
            source_field="session_id",
            rationale="Identifiant unique de session.",
            confidence=0.9,
        )
    ]
    assert proposal.ambiguities == VALID_RESPONSE["ambiguities"]
    assert proposal.unmapped_fields == VALID_RESPONSE["unmapped_fields"]


def test_explanations_et_listes_optionnelles_peuvent_etre_vides() -> None:
    response = copy.deepcopy(VALID_RESPONSE)
    response["explanations"] = []
    response["ambiguities"] = []
    response["unmapped_fields"] = []

    proposal = parse_mapping_response(response)

    assert proposal.explanations == []
    assert proposal.ambiguities == []
    assert proposal.unmapped_fields == []


def test_reponse_qui_n_est_pas_un_objet_est_refusee() -> None:
    with pytest.raises(LLMError, match="objet JSON"):
        parse_mapping_response(["not", "a", "dict"])


def test_definition_manquante_est_refusee() -> None:
    response = copy.deepcopy(VALID_RESPONSE)
    del response["definition"]

    with pytest.raises(LLMError, match="definition"):
        parse_mapping_response(response)


def test_definition_qui_ne_respecte_pas_le_contrat_est_refusee() -> None:
    response = copy.deepcopy(VALID_RESPONSE)
    response["definition"] = {**VALID_DEFINITION, "source_format": "xml"}

    with pytest.raises(LLMError, match="mapping proposé par le modèle est invalide"):
        parse_mapping_response(response)


def test_explanations_qui_n_est_pas_une_liste_est_refusee() -> None:
    response = copy.deepcopy(VALID_RESPONSE)
    response["explanations"] = "not-a-list"

    with pytest.raises(LLMError, match="explanations"):
        parse_mapping_response(response)


def test_explanation_qui_n_est_pas_un_objet_est_refusee() -> None:
    response = copy.deepcopy(VALID_RESPONSE)
    response["explanations"] = ["not-a-dict"]

    with pytest.raises(LLMError, match="explanations\\[0\\]"):
        parse_mapping_response(response)


@pytest.mark.parametrize(
    "overrides",
    [
        {"target_field": None},
        {"target_field": ""},
        {"source_field": 123},
        {"rationale": None},
        {"confidence": "high"},
        {"confidence": 1.5},
        {"confidence": -0.1},
    ],
)
def test_explanation_malformee_est_refusee(overrides: dict[str, object]) -> None:
    response = copy.deepcopy(VALID_RESPONSE)
    response["explanations"][0].update(overrides)

    with pytest.raises(LLMError, match="explanations\\[0\\]"):
        parse_mapping_response(response)


def test_ambiguities_avec_un_element_non_texte_est_refusee() -> None:
    response = copy.deepcopy(VALID_RESPONSE)
    response["ambiguities"] = [1, 2]

    with pytest.raises(LLMError, match="ambiguities"):
        parse_mapping_response(response)


def test_unmapped_fields_avec_un_element_non_texte_est_refusee() -> None:
    response = copy.deepcopy(VALID_RESPONSE)
    response["unmapped_fields"] = [{"not": "a string"}]

    with pytest.raises(LLMError, match="unmapped_fields"):
        parse_mapping_response(response)


def test_extract_json_object_lit_un_json_brut() -> None:
    assert extract_json_object(json.dumps(VALID_RESPONSE)) == VALID_RESPONSE


def test_extract_json_object_retire_le_bloc_markdown() -> None:
    text = f"Voici le mapping :\n```json\n{json.dumps(VALID_RESPONSE)}\n```\n"

    assert extract_json_object(text) == VALID_RESPONSE


def test_extract_json_object_illisible_est_refuse() -> None:
    with pytest.raises(LLMError, match="JSON illisible"):
        extract_json_object("not json at all")


def test_parse_mapping_response_text_combine_extraction_et_conversion() -> None:
    text = f"```json\n{json.dumps(VALID_RESPONSE)}\n```"

    proposal = parse_mapping_response_text(text)

    assert isinstance(proposal, MappingProposal)
    assert proposal.definition == VALID_DEFINITION
