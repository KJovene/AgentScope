"""Contrat de mapping (``docs/PLAN.md`` §5.1) — dataclasses pures.

Un *mapping* est un document JSON qui décrit comment transformer les
enregistrements bruts d'une source (``RawRecord.payload``) en entités du domaine
(``Session``, ``ModelCall``, ``ToolCall``).

Ce module ne fait que **représenter** ce document en objets Python typés et le
relire depuis un ``dict`` (``MappingDefinition.from_dict``). Il n'exécute rien :

- la validation sémantique vit dans ``validator.py`` (issue I2.13) ;
- l'application du mapping vit dans ``normalizer.py`` (issue I2.6).

Toute structure manifestement cassée lève ``InvalidMappingError`` dès la lecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from agentscope.domain import InvalidMappingError


class OnError(StrEnum):
    """Que faire quand un champ ne peut pas être produit (cf. §5.1)."""

    REJECT = "reject"  # l'enregistrement entier part dans import_reject
    NULL = "null"  # la valeur devient NULL et est comptée dans missing_info
    SKIP = "skip"  # le champ est simplement ignoré


class WhereOp(StrEnum):
    """Opérateurs autorisés dans un filtre ``iterate.where`` (aucune éval de code)."""

    EQ = "eq"
    NE = "ne"
    IN = "in"
    EXISTS = "exists"
    GT = "gt"
    LT = "lt"


@dataclass(frozen=True, slots=True)
class WhereClause:
    """Un triplet ``[champ, opérateur, valeur]`` d'un filtre d'itération."""

    field: str
    op: WhereOp
    value: Any = None


@dataclass(frozen=True, slots=True)
class IterateSpec:
    """Où trouver les enregistrements d'une entité dans le payload brut.

    ``path`` = chemin pointé vers un tableau ; ``""`` = l'enregistrement racine.
    ``where`` = filtres combinés en ET.
    """

    path: str = ""
    where: tuple[WhereClause, ...] = ()


@dataclass(frozen=True, slots=True)
class ParentSpec:
    """Comment une entité fille retrouve la clé de sa session parente."""

    entity: str
    key_from: str


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """Règle de production d'un champ cible.

    ``target`` est la clé dans le bloc ``fields`` du JSON (ex. ``"prompt_tokens"``).
    ``source`` est le champ brut (``from`` dans le JSON) ; il peut être absent
    pour ``transform: "const"``.
    """

    target: str
    source: str | None = None
    transform: str = "identity"
    args: dict[str, Any] = field(default_factory=dict)
    required: bool = False
    on_error: OnError = OnError.NULL


@dataclass(frozen=True, slots=True)
class EntitySpec:
    """Comment construire une entité cible (``session`` / ``model_call`` / ``tool_call``)."""

    name: str
    iterate: IterateSpec
    key_fields: tuple[str, ...]
    fields: tuple[FieldSpec, ...]
    parent: ParentSpec | None = None

    def field(self, target: str) -> FieldSpec | None:
        return next((f for f in self.fields if f.target == target), None)


@dataclass(frozen=True, slots=True)
class MappingDefinition:
    """Le document de mapping complet, prêt à être appliqué par le ``Normalizer``."""

    name: str
    version: int
    source_format: str
    entities: tuple[EntitySpec, ...]
    constants: dict[str, Any] = field(default_factory=dict)
    unmapped_fields: tuple[str, ...] = ()

    def entity(self, name: str) -> EntitySpec | None:
        return next((e for e in self.entities if e.name == name), None)

    # ------------------------------------------------------------------
    # Lecture depuis un dict (JSON déjà désérialisé)
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, raw: Any) -> MappingDefinition:
        if not isinstance(raw, dict):
            raise InvalidMappingError("Le mapping doit être un objet JSON.")

        name = _require_str(raw, "name")
        version = _require_int(raw, "version")
        source_format = _require_str(raw, "source_format")

        entities_raw = raw.get("entities")
        if not isinstance(entities_raw, dict) or not entities_raw:
            raise InvalidMappingError(
                "Le mapping doit déclarer au moins une entité dans `entities`."
            )

        entities = tuple(
            _entity_from_dict(entity_name, entity_raw)
            for entity_name, entity_raw in entities_raw.items()
        )

        constants = raw.get("constants") or {}
        if not isinstance(constants, dict):
            raise InvalidMappingError("`constants` doit être un objet.")

        unmapped = tuple(raw.get("unmapped_fields") or ())

        return cls(
            name=name,
            version=version,
            source_format=source_format,
            entities=entities,
            constants=dict(constants),
            unmapped_fields=unmapped,
        )


# ---------------------------------------------------------------------------
# Helpers de lecture — messages d'erreur explicites, jamais de crash brut
# ---------------------------------------------------------------------------


def _require_str(source: dict[str, Any], key: str) -> str:
    value = source.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InvalidMappingError(f"Champ `{key}` manquant ou vide dans le mapping.")
    return value


def _require_int(source: dict[str, Any], key: str) -> int:
    value = source.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidMappingError(f"Champ `{key}` manquant ou non entier dans le mapping.")
    return value


def _entity_from_dict(name: str, raw: Any) -> EntitySpec:
    if not isinstance(raw, dict):
        raise InvalidMappingError(f"L'entité `{name}` doit être un objet.")

    iterate = _iterate_from_dict(name, raw.get("iterate"))

    identity = raw.get("identity")
    if not isinstance(identity, dict) or not isinstance(identity.get("key_fields"), list):
        raise InvalidMappingError(f"L'entité `{name}` doit déclarer `identity.key_fields` (liste).")
    key_fields = tuple(str(k) for k in identity["key_fields"])
    if not key_fields:
        raise InvalidMappingError(f"L'entité `{name}` a une liste `identity.key_fields` vide.")

    fields_raw = raw.get("fields")
    if not isinstance(fields_raw, dict) or not fields_raw:
        raise InvalidMappingError(
            f"L'entité `{name}` doit déclarer au moins un champ dans `fields`."
        )
    fields = tuple(
        _field_from_dict(name, target, field_raw) for target, field_raw in fields_raw.items()
    )

    parent = _parent_from_dict(name, raw.get("parent"))

    return EntitySpec(
        name=name,
        iterate=iterate,
        key_fields=key_fields,
        fields=fields,
        parent=parent,
    )


def _iterate_from_dict(entity_name: str, raw: Any) -> IterateSpec:
    if raw is None:
        return IterateSpec()
    if not isinstance(raw, dict):
        raise InvalidMappingError(f"`iterate` de l'entité `{entity_name}` doit être un objet.")

    path = raw.get("path", "")
    if not isinstance(path, str):
        raise InvalidMappingError(f"`iterate.path` de `{entity_name}` doit être une chaîne.")

    where_raw = raw.get("where") or []
    if not isinstance(where_raw, list):
        raise InvalidMappingError(f"`iterate.where` de `{entity_name}` doit être une liste.")

    clauses: list[WhereClause] = []
    for triplet in where_raw:
        if not isinstance(triplet, (list, tuple)) or len(triplet) not in (2, 3):
            raise InvalidMappingError(
                f"`iterate.where` de `{entity_name}` : chaque filtre est [champ, op, valeur?]."
            )
        field_name, op_name = triplet[0], triplet[1]
        value = triplet[2] if len(triplet) == 3 else None
        try:
            op = WhereOp(op_name)
        except ValueError as error:
            raise InvalidMappingError(
                f"Opérateur de filtre inconnu `{op_name}` dans l'entité `{entity_name}`."
            ) from error
        clauses.append(WhereClause(field=str(field_name), op=op, value=value))

    return IterateSpec(path=path, where=tuple(clauses))


def _field_from_dict(entity_name: str, target: str, raw: Any) -> FieldSpec:
    if not isinstance(raw, dict):
        raise InvalidMappingError(f"Le champ `{entity_name}.{target}` doit être un objet.")

    transform = raw.get("transform", "identity")
    if not isinstance(transform, str) or not transform:
        raise InvalidMappingError(f"`transform` de `{entity_name}.{target}` doit être une chaîne.")

    source = raw.get("from")
    if source is not None and not isinstance(source, str):
        raise InvalidMappingError(f"`from` de `{entity_name}.{target}` doit être une chaîne.")

    args = raw.get("args") or {}
    if not isinstance(args, dict):
        raise InvalidMappingError(f"`args` de `{entity_name}.{target}` doit être un objet.")

    on_error_name = raw.get("on_error", OnError.NULL.value)
    try:
        on_error = OnError(on_error_name)
    except ValueError as error:
        raise InvalidMappingError(
            f"`on_error` inconnu `{on_error_name}` pour `{entity_name}.{target}` "
            f"(attendu : reject | null | skip)."
        ) from error

    return FieldSpec(
        target=target,
        source=source,
        transform=transform,
        args=dict(args),
        required=bool(raw.get("required", False)),
        on_error=on_error,
    )


def _parent_from_dict(entity_name: str, raw: Any) -> ParentSpec | None:
    if raw is None:
        return None
    if not isinstance(raw, dict) or not raw.get("entity") or not raw.get("key_from"):
        raise InvalidMappingError(
            f"`parent` de `{entity_name}` doit déclarer `entity` et `key_from`."
        )
    return ParentSpec(entity=str(raw["entity"]), key_from=str(raw["key_from"]))
