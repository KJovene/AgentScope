"""Validation sémantique d'un mapping (issue I2.13).

``MappingDefinition.from_dict`` (``contract.py``) a déjà refusé les structures
cassées. Ici on vérifie le **sens** :

- l'entité cible existe (``session`` / ``model_call`` / ``tool_call``) ;
- chaque champ visé est connu du schéma cible ;
- la transformation est dans la whitelist (``TRANSFORM_REGISTRY``) ;
- ``from`` est présent quand la transformation en a besoin ;
- les champs requis d'une entité sont mappés ;
- ``parent`` pointe vers une entité déclarée.

Toutes les erreurs sont **collectées puis levées ensemble** : l'utilisateur voit
d'un coup tout ce qui ne va pas — « mapping invalide ⇒ refus expliqué ».
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from agentscope.application.mapping.contract import EntitySpec, MappingDefinition
from agentscope.application.mapping.target_schema import (
    PARENT_ENTITY,
    TARGET_SCHEMA,
    TargetEntity,
)
from agentscope.application.mapping.transforms import TRANSFORM_REGISTRY
from agentscope.domain import FileFormat, InvalidMappingError

# Transformations qui ne lisent pas un champ source unique.
_NO_SOURCE_TRANSFORMS = {"const", "coalesce"}


def validate_mapping(mapping: MappingDefinition) -> None:
    """Lève ``InvalidMappingError`` (avec la liste des problèmes) si le mapping est invalide."""
    problems: list[str] = []
    _check_source_format(mapping, problems)
    _check_constants(mapping, problems)

    declared = {entity.name for entity in mapping.entities}
    if PARENT_ENTITY not in declared:
        problems.append(f"Le mapping doit déclarer l'entité `{PARENT_ENTITY}`.")
    for entity in mapping.entities:
        _check_entity(entity, declared, problems)

    if problems:
        raise InvalidMappingError("Mapping invalide :\n- " + "\n- ".join(problems))


def parse_and_validate(raw: object) -> MappingDefinition:
    """Raccourci : lit le dict puis le valide. Lève ``InvalidMappingError`` sinon."""
    _validate_json_schema(raw)
    mapping = MappingDefinition.from_dict(raw)
    validate_mapping(mapping)
    return mapping


# ---------------------------------------------------------------------------


_SCHEMA_PATH = (
    Path(__file__).resolve().parents[4] / "docs" / "data" / "mappings" / "mapping.schema.json"
)
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
_SCHEMA_VALIDATOR = Draft202012Validator(_SCHEMA)


def _validate_json_schema(raw: object) -> None:
    errors = sorted(_SCHEMA_VALIDATOR.iter_errors(raw), key=lambda error: list(error.path))
    if not errors:
        return

    details = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "mapping"
        details.append(f"`{location}` : {error.message}")
    raise InvalidMappingError("Mapping JSON invalide :\n- " + "\n- ".join(details))


# ---------------------------------------------------------------------------


def _check_source_format(mapping: MappingDefinition, problems: list[str]) -> None:
    allowed = [fmt.value for fmt in FileFormat]
    if mapping.source_format not in allowed:
        problems.append(
            f"source_format `{mapping.source_format}` inconnu (attendu : {', '.join(allowed)})."
        )


def _check_constants(mapping: MappingDefinition, problems: list[str]) -> None:
    source_name = mapping.constants.get("source_name")
    if not isinstance(source_name, str) or not source_name.strip():
        problems.append("`constants.source_name` est requis (nom de la source de traces).")


def _check_entity(entity: EntitySpec, declared: set[str], problems: list[str]) -> None:
    schema = TARGET_SCHEMA.get(entity.name)
    if schema is None:
        problems.append(
            f"Entité cible inconnue `{entity.name}` (attendu : {', '.join(TARGET_SCHEMA)})."
        )
        return

    allowed = schema.field_names()
    mapped: set[str] = set()
    for spec in entity.fields:
        mapped.add(spec.target)
        prefix = f"`{entity.name}.{spec.target}`"

        if spec.target not in allowed:
            problems.append(
                f"{prefix} : champ cible inconnu (disponibles : {', '.join(sorted(allowed))})."
            )
        if spec.transform not in TRANSFORM_REGISTRY:
            problems.append(f"{prefix} : transformation `{spec.transform}` non autorisée.")
        elif spec.transform == "const" and "value" not in spec.args:
            problems.append(f"{prefix} : transform `const` exige `args.value`.")
        elif spec.transform == "coalesce" and not spec.args.get("fields"):
            problems.append(f"{prefix} : transform `coalesce` exige `args.fields`.")

        if spec.source is None and spec.transform not in _NO_SOURCE_TRANSFORMS:
            problems.append(f"{prefix} : `from` manquant (obligatoire sauf pour `const`).")

    _check_required_fields(entity, schema, mapped, problems)
    _check_parent(entity, declared, problems)


def _check_required_fields(
    entity: EntitySpec, schema: TargetEntity, mapped: set[str], problems: list[str]
) -> None:
    missing = set(schema.required) - mapped
    if "external_id" in missing and entity.key_fields:
        missing.discard("external_id")  # sera synthétisé depuis identity.key_fields
    for name in sorted(missing):
        problems.append(f"`{entity.name}` : champ requis `{name}` non mappé.")


def _check_parent(entity: EntitySpec, declared: set[str], problems: list[str]) -> None:
    if entity.name == PARENT_ENTITY:
        if entity.parent is not None:
            problems.append(f"`{entity.name}` ne doit pas déclarer de `parent`.")
        return

    if entity.parent is None:
        problems.append(
            f"`{entity.name}` : `parent` manquant (un appel est rattaché à une session)."
        )
        return

    if entity.parent.entity not in declared:
        problems.append(
            f"`{entity.name}.parent` référence `{entity.parent.entity}`, "
            f"non déclarée dans le mapping."
        )
    elif entity.parent.entity != PARENT_ENTITY:
        problems.append(f"`{entity.name}.parent` doit pointer vers `{PARENT_ENTITY}`.")
