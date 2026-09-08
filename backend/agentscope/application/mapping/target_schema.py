"""Schéma cible : ce que le ``Normalizer`` sait produire (dérivé du domaine).

Sert deux besoins :

- **valider un mapping** (issue I2.13) : une règle ``from … -> X`` doit viser un
  champ ``X`` réellement connu ;
- plus tard, l'agent IA (I3.6) qui *propose* un mapping a besoin de connaître les
  cibles disponibles.

Les noms de champs suivent le bloc §5.1 du plan, **à plat**. Le ``Normalizer``
assemble ensuite ces valeurs dans les entités du domaine (``Session``,
``ModelCall``, ``ToolCall``).

Trois choses ne viennent jamais du mapping et n'apparaissent donc pas ici :
``source_name`` (vient de ``constants``), la provenance (vient du ``RawRecord``),
et le rattachement parent (vient de ``parent`` + ``identity``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class TargetField:
    """Un champ productible et le type attendu après transformation."""

    name: str
    type: str  # "string" | "int" | "float" | "datetime" | "call_status" | "error_type"


@dataclass(frozen=True, slots=True)
class TargetEntity:
    """Une entité cible et ses champs autorisés."""

    name: str
    fields: tuple[TargetField, ...]
    required: frozenset[str]  # champs sans lesquels l'entité ne peut pas exister
    # (``external_id`` fait exception : synthétisable via ``identity.key_fields``)

    def field_names(self) -> frozenset[str]:
        return frozenset(f.name for f in self.fields)

    def field(self, name: str) -> TargetField | None:
        return next((f for f in self.fields if f.name == name), None)


_SESSION = TargetEntity(
    name="session",
    fields=(
        TargetField("external_id", "string"),
        TargetField("agent_name", "string"),
        TargetField("started_at", "datetime"),
        TargetField("ended_at", "datetime"),
        TargetField("repository_name", "string"),
    ),
    required=frozenset({"external_id"}),
)

_MODEL_CALL = TargetEntity(
    name="model_call",
    fields=(
        TargetField("sequence", "int"),
        TargetField("model_name", "string"),
        TargetField("provider", "string"),
        TargetField("prompt_tokens", "int"),
        TargetField("completion_tokens", "int"),
        TargetField("cached_tokens", "int"),
        TargetField("cost_usd", "float"),
        TargetField("started_at", "datetime"),
        TargetField("ended_at", "datetime"),
        TargetField("status", "call_status"),
        TargetField("error_type", "error_type"),
    ),
    required=frozenset({"model_name"}),
)

_TOOL_CALL = TargetEntity(
    name="tool_call",
    fields=(
        TargetField("sequence", "int"),
        TargetField("tool_name", "string"),
        TargetField("model_call_sequence", "int"),
        TargetField("started_at", "datetime"),
        TargetField("ended_at", "datetime"),
        TargetField("status", "call_status"),
        TargetField("error_type", "error_type"),
        TargetField("input_bytes", "int"),
        TargetField("output_bytes", "int"),
    ),
    required=frozenset({"tool_name"}),
)

#: Entité parente : seules les entités filles portent un ``parent``, toujours vers elle.
PARENT_ENTITY = "session"

#: Schéma cible complet, indexé par nom d'entité. Lecture seule.
TARGET_SCHEMA: Mapping[str, TargetEntity] = MappingProxyType(
    {entity.name: entity for entity in (_SESSION, _MODEL_CALL, _TOOL_CALL)}
)
