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

import json
import re
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

# `PromptBuilder` (I3.6) ne dicte pas le format de sortie (il est indépendant du
# fournisseur) ; les adaptateurs concrets (I3.3/I3.4) ajoutent cette consigne au
# prompt utilisateur pour obtenir une réponse exploitable par ce module.
_DEFINITION_SKELETON = """{
  "name": "...",
  "version": 1,
  "source_format": "jsonl",
  "constants": {"source_name": "..."},
  "entities": {
    "session": {
      "iterate": {"path": "...", "where": [["type", "eq", "session"]]},
      "identity": {"key_fields": ["..."]},
      "fields": {
        "external_id": {"from": "...", "required": true, "on_error": "reject"}
      }
    },
    "model_call": {
      "iterate": {"path": "...", "where": [["type", "eq", "model_change"]]},
      "parent": {"entity": "session", "key_from": "..."},
      "identity": {"key_fields": ["..."]},
      "fields": {
        "model_name": {"from": "...", "required": true, "on_error": "reject"}
      }
    }
  }
}"""

RESPONSE_FORMAT_INSTRUCTION = (
    "Réponds uniquement avec un objet JSON valide (sans texte autour, sans bloc "
    "markdown) de la forme exacte :\n"
    "{\n"
    '  "definition": { ... contrat de mapping conforme au schéma cible ... },\n'
    '  "explanations": [\n'
    '    {"target_field": "...", "source_field": "..." ou null, "rationale": "...", '
    '"confidence": 0.0}\n'
    "  ],\n"
    '  "ambiguities": ["..."],\n'
    '  "unmapped_fields": ["..."]\n'
    "}\n\n"
    "`definition` DOIT suivre exactement ce squelette — chaque entité cible "
    "(session, model_call, tool_call, ...) est une clé sous `entities`, jamais "
    "une clé directe de `definition` ; `entities.session` est obligatoire.\n"
    "Règles strictes sur les champs d'une entité :\n"
    "- `where` est un tableau de triplets `[champ, opérateur, valeur]` — jamais "
    "un objet `{\"field\": ..., \"equals\": ...}`. Opérateurs valides : "
    '"eq", "ne", "in", "exists", "gt", "lt".\n'
    '- `on_error` accepte uniquement "reject", "null" ou "skip" — jamais '
    '"ignore" ni une autre valeur.\n'
    "- Omets entièrement une entrée de `fields` si l'entité n'a pas de champ "
    "source correspondant dans l'échantillon : n'écris jamais `\"from\": null`.\n"
    '- `parent.entity` vaut TOUJOURS `"session"`, y compris pour `tool_call` — '
    "il n'y a pas de rattachement structurel `tool_call` → `model_call` ; pour "
    "l'exprimer, mappe `tool_call.fields.model_call_sequence` au lieu de `parent`.\n"
    '- `parent.key_from` est une chaîne unique (ex. `"parentId"`), jamais un '
    "tableau.\n"
    '- `constants.source_name` est **obligatoire** : un nom court identifiant '
    "la source (ex. son nom de fichier ou de format), jamais absent ni vide.\n"
    "- Une entité (`session`/`model_call`/`tool_call`) n'a QUE les clés `iterate`, "
    "`identity`, `parent` et `fields` — jamais d'autre clé (ex. pas de `derive`) : "
    "toute logique de champ passe par `transform`/`args` d'une entrée de `fields`.\n"
    "- `transform` est un des noms whitelistés ci-dessous — jamais un objet "
    "condition inventé (ex. jamais `{\"champ\": {\"eq\": ..., \"then\": ..., "
    '"else": ...}}`) :\n'
    '  - `identity` (défaut, aucun `args`) ; `to_int`, `to_float` (aucun `args`) ; '
    '`to_iso8601` (`args: {"unit": "epoch_s" | "epoch_ms" | "iso"}`)\n'
    '  - `const` (`args: {"value": ...}`, pas de `from`) ; `coalesce` '
    '(`args: {"fields": ["...", "..."]}`, pas de `from`, lit plusieurs champs de '
    "la ligne)\n"
    '  - `map_enum` (`args: {"mapping": {"valeur_source": "valeur_cible", ...}, '
    '"default": ...}`) — pour dériver un champ (ex. `status` depuis un booléen '
    "`isError` : `mapping: {\"true\": \"error\", \"false\": \"success\"}`)\n"
    '  - `lower`, `upper`, `trim`, `json_stringify` (aucun `args`) ; `split` '
    '(`args: {"sep": "...", "index": 0}`) ; `regex_extract` '
    '(`args: {"pattern": "...", "group": 1}`) ; `cents_to_usd`, `ms_to_s` '
    "(aucun `args`)\n\n"
    f"{_DEFINITION_SKELETON}"
)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json_object(text: str) -> Any:
    """Extrait un objet JSON d'une réponse texte de modèle.

    Tolère un bloc encadré par des triples-backticks (```` ```json ... ``` ````),
    fréquent chez certains modèles malgré la consigne de réponse « JSON seul ».
    Tolère aussi du texte à la suite de l'objet JSON (un commentaire ajouté par
    le modèle malgré la même consigne) : seul le premier objet JSON valide en
    tête de la réponse est retenu, le reste est ignoré.
    """
    candidate = text.strip()
    fence_match = _JSON_FENCE_RE.search(candidate)
    if fence_match:
        candidate = fence_match.group(1).strip()

    try:
        obj, _ = json.JSONDecoder().raw_decode(candidate)
        return obj
    except json.JSONDecodeError as exc:
        raise LLMError(f"Réponse du modèle invalide : JSON illisible ({exc}).") from exc


def parse_mapping_response_text(text: str) -> MappingProposal:
    """Combine extraction JSON (réponse texte brute d'un provider) + ``parse_mapping_response``."""
    return parse_mapping_response(extract_json_object(text))


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

    definition = _drop_unfulfillable_fields(definition)

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

# Transformations qui ne lisent pas un champ source unique (cf. la même liste
# dans `validator.py`/`normalizer.py` — un `from` y est alors sans objet).
_NO_SOURCE_TRANSFORMS = {"const", "coalesce"}


def _drop_unfulfillable_fields(definition: dict[str, Any]) -> dict[str, Any]:
    """Retire les entrées `fields` que le modèle a laissées sans source.

    Malgré la consigne du prompt, un modèle (surtout un petit) répond parfois
    `"from": null` pour un champ cible qu'il ne sait pas mapper sur cet
    échantillon, au lieu d'omettre l'entrée. Le contrat de mapping exige `from`
    (sauf transformations sans source) : plutôt que de rejeter toute la
    proposition pour ça, on retire silencieusement ces entrées inexploitables
    — un champ cible non mappé est une situation normale (`missing_info` s'en
    charge à l'exécution), pas une erreur.
    """
    entities = definition.get("entities")
    if not isinstance(entities, dict):
        return definition

    cleaned_entities = {}
    for entity_name, entity in entities.items():
        if not isinstance(entity, dict):
            cleaned_entities[entity_name] = entity
            continue
        fields = entity.get("fields")
        if not isinstance(fields, dict):
            cleaned_entities[entity_name] = entity
            continue
        cleaned_fields = {
            field_name: spec
            for field_name, spec in fields.items()
            if not (
                isinstance(spec, dict)
                and spec.get("from") is None
                and spec.get("transform") not in _NO_SOURCE_TRANSFORMS
            )
        }
        cleaned_entities[entity_name] = {**entity, "fields": cleaned_fields}

    return {**definition, "entities": cleaned_entities}


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
