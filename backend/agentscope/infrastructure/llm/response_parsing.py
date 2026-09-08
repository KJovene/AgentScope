"""Conversion réponse modèle -> contrat commun, avec validation (issue I3.11).

Un ``LLMProvider`` réel (Anthropic I3.3, OpenAI-compatible I3.4) reçoit du modèle
un blob JSON en texte libre. Ce module le convertit vers ``MappingProposal``
(contrat commun, §5.2) et valide le mapping produit contre le contrat de mapping
(§5.1, cf. ``validator.py`` / I2.13).

Toute réponse non conforme (clé manquante, type incorrect, mapping qui ne
respecte pas le contrat) lève ``LLMError`` — jamais de ``KeyError``/``TypeError``
brut qui remonterait jusqu'à l'appelant.
"""

from __future__ import annotations

from typing import Any

from agentscope.application.mapping.validator import parse_and_validate
from agentscope.application.ports.llm_provider import FieldExplanation, MappingProposal
from agentscope.domain import InvalidMappingError, LLMError

# Structure attendue (négociée dans le prompt, cf. I3.6) :
#   {
#     "definition": {...},                 # contrat de mapping §5.1
#     "explanations": [
#       {"target_field": ..., "source_field": ..., "rationale": ..., "confidence": ...}, ...
#     ],
#     "ambiguities": [...],
#     "unmapped_fields": [...]
#   }


def parse_mapping_response(raw: object) -> MappingProposal:
    """Convertit la réponse JSON du modèle en ``MappingProposal`` validée.

    Lève ``LLMError`` si la structure est incorrecte ou si ``definition`` ne
    respecte pas le contrat de mapping (§5.1).
    """
    if not isinstance(raw, dict):
        raise LLMError("Réponse du modèle invalide : un objet JSON était attendu.")

    definition = _require_dict(raw, "definition")
    explanations = _parse_explanations(raw.get("explanations"))
    ambiguities = _require_str_list(raw, "ambiguities")
    unmapped_fields = _require_str_list(raw, "unmapped_fields")

    try:
        parse_and_validate(definition)
    except InvalidMappingError as exc:
        raise LLMError(f"Le mapping proposé par le modèle est invalide : {exc}") from exc

    return MappingProposal(
        definition=definition,
        explanations=explanations,
        ambiguities=ambiguities,
        unmapped_fields=unmapped_fields,
    )


# ---------------------------------------------------------------------------


def _require_dict(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise LLMError(f"Réponse du modèle invalide : `{key}` manquant ou n'est pas un objet.")
    return value


def _require_str_list(raw: dict[str, Any], key: str) -> list[str]:
    value = raw.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise LLMError(f"Réponse du modèle invalide : `{key}` doit être une liste de chaînes.")
    return list(value)


def _parse_explanations(raw: object) -> list[FieldExplanation]:
    if not isinstance(raw, list):
        raise LLMError("Réponse du modèle invalide : `explanations` doit être une liste.")

    return [_explanation_from_dict(index, item) for index, item in enumerate(raw)]


def _explanation_from_dict(index: int, item: object) -> FieldExplanation:
    prefix = f"Réponse du modèle invalide : `explanations[{index}]"
    if not isinstance(item, dict):
        raise LLMError(f"{prefix}` n'est pas un objet.")

    target_field = item.get("target_field")
    if not isinstance(target_field, str) or not target_field:
        raise LLMError(f"{prefix}.target_field` manquant ou vide.")

    source_field = item.get("source_field")
    if source_field is not None and not isinstance(source_field, str):
        raise LLMError(f"{prefix}.source_field` doit être une chaîne ou `null`.")

    rationale = item.get("rationale")
    if not isinstance(rationale, str):
        raise LLMError(f"{prefix}.rationale` manquant.")

    confidence = item.get("confidence")
    if not isinstance(confidence, int | float) or isinstance(confidence, bool):
        raise LLMError(f"{prefix}.confidence` doit être un nombre.")
    if not 0.0 <= float(confidence) <= 1.0:
        raise LLMError(f"{prefix}.confidence` doit être compris entre 0 et 1.")

    return FieldExplanation(
        target_field=target_field,
        source_field=source_field,
        rationale=rationale,
        confidence=float(confidence),
    )
