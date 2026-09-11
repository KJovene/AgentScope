"""``Normalizer`` — applique un mapping validé à des enregistrements bruts (issue I2.6).

Entrée : un flux de ``RawRecord`` + une ``MappingDefinition``.
Sortie : un ``NormalizationResult`` = les entités du domaine produites, la liste
des rejets (avec une raison consultable) et le décompte des valeurs absentes
tolérées.

Principes :

- **Aucune exception ne remonte pour un enregistrement fautif** : il part dans
  ``rejects`` avec un ``RejectReason`` et un message. Le reste du fichier continue.
- **Un enregistrement = une session + ses appels** (imbrication JSON, périmètre v1
  du plan §5). La session est construite en premier ; si elle est rejetée, ses
  appels le sont aussi.
- **Doublons dans le fichier** : une clé naturelle déjà produite est ignorée
  silencieusement (le premier gagne), comme le fera l'``upsert`` en base (I2.7).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from agentscope.application.mapping.contract import (
    EntitySpec,
    FieldSpec,
    IterateSpec,
    MappingDefinition,
    OnError,
    WhereClause,
    WhereOp,
)
from agentscope.application.mapping.target_schema import TARGET_SCHEMA
from agentscope.application.mapping.transforms import TransformError, apply_transform
from agentscope.application.mapping.validator import validate_mapping
from agentscope.domain import (
    CallStatus,
    DomainError,
    ErrorType,
    ImportReject,
    Interval,
    InvalidMappingError,
    ModelCall,
    Provenance,
    RawRecord,
    RejectReason,
    Session,
    TokenUsage,
    ToolCall,
)


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """Résultat complet d'une normalisation (contrat du plan §5.2)."""

    sessions: tuple[Session, ...] = ()
    model_calls: tuple[ModelCall, ...] = ()
    tool_calls: tuple[ToolCall, ...] = ()
    rejects: tuple[ImportReject, ...] = ()
    missing_info: Mapping[str, int] = field(default_factory=dict)


class _RecordRejectedError(Exception):
    """Signal interne : l'enregistrement courant doit être rejeté."""

    def __init__(self, reason: RejectReason, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


class _Accumulator:
    """Collecte les lignes produites en dédupliquant sur la clé naturelle."""

    def __init__(self) -> None:
        self.sessions: list[Session] = []
        self.model_calls: list[ModelCall] = []
        self.tool_calls: list[ToolCall] = []
        self.rejects: list[ImportReject] = []
        self.missing_info: dict[str, int] = {}
        self._seen: set[tuple[str, ...]] = set()
        self._sequences: dict[tuple[str, str], int] = {}

    def add_session(self, session: Session) -> None:
        if self._first_time(("session", session.source_name, session.external_id)):
            self.sessions.append(session)

    def register_child(
        self, entity: str, session_external_id: str, identity: tuple[str, ...]
    ) -> bool:
        """Marque une ligne fille comme vue. ``False`` = déjà connue (à ignorer).

        La clé est l'``identity.key_fields`` du mapping — **stable** quelle que soit
        la position dans le fichier —, pas le ``sequence`` positionnel.
        """
        return self._first_time((entity, session_external_id, *identity))

    def add_model_call(self, call: ModelCall) -> None:
        self.model_calls.append(call)

    def add_tool_call(self, call: ToolCall) -> None:
        self.tool_calls.append(call)

    def reject(self, record: RawRecord, reason: RejectReason, detail: str) -> None:
        self.rejects.append(
            ImportReject(
                record_index=record.index,
                reason=reason,
                detail=detail,
                payload=record.payload,
            )
        )

    def note_missing(self, target: str) -> None:
        self.missing_info[target] = self.missing_info.get(target, 0) + 1

    def next_sequence(self, session_external_id: str, entity: str) -> int:
        """Numéro d'ordre auto quand le mapping ne fournit pas de ``sequence``."""
        key = (session_external_id, entity)
        current = self._sequences.get(key, 0)
        self._sequences[key] = current + 1
        return current

    def _first_time(self, key: tuple[str, ...]) -> bool:
        if key in self._seen:
            return False
        self._seen.add(key)
        return True

    def backfill_session_intervals(self) -> None:
        """Déduit l'enveloppe temporelle d'une session de ses appels quand le
        mapping ne la fournit pas.

        Beaucoup de sources itèrent par tour/round : on ne voit alors jamais la
        session en entier, et ``session.started_at`` / ``ended_at`` restent NULL —
        donc ``duration_ms`` aussi. Ici on ne fait que **combler les trous** :
        ``started_at`` absent → plus tôt des ``started_at``/``ended_at`` des appels ;
        ``ended_at`` absent → plus tard. Une borne déjà mappée est conservée.
        """
        starts: dict[str, list[datetime]] = {}
        ends: dict[str, list[datetime]] = {}
        for call in (*self.model_calls, *self.tool_calls):
            if call.interval.started_at is not None:
                starts.setdefault(call.session_external_id, []).append(call.interval.started_at)
            if call.interval.ended_at is not None:
                ends.setdefault(call.session_external_id, []).append(call.interval.ended_at)

        for position, session in enumerate(self.sessions):
            current = session.interval
            if current.started_at is not None and current.ended_at is not None:
                continue
            moments = starts.get(session.external_id, []) + ends.get(session.external_id, [])
            if not moments:
                continue
            new_start = current.started_at or min(moments)
            new_end = current.ended_at or max(moments)
            if new_end < new_start or (new_start, new_end) == (
                current.started_at,
                current.ended_at,
            ):
                continue
            self.sessions[position] = replace(
                session, interval=Interval(started_at=new_start, ended_at=new_end)
            )

        for target, attr in (
            ("session.started_at", "started_at"),
            ("session.ended_at", "ended_at"),
        ):
            still_missing = sum(1 for s in self.sessions if getattr(s.interval, attr) is None)
            if still_missing:
                self.missing_info[target] = still_missing
            else:
                self.missing_info.pop(target, None)

    def result(self) -> NormalizationResult:
        return NormalizationResult(
            sessions=tuple(self.sessions),
            model_calls=tuple(self.model_calls),
            tool_calls=tuple(self.tool_calls),
            rejects=tuple(self.rejects),
            missing_info=dict(self.missing_info),
        )


class Normalizer:
    """Transforme des ``RawRecord`` en entités du domaine selon un mapping."""

    def normalize(
        self, records: Iterable[RawRecord], mapping: MappingDefinition
    ) -> NormalizationResult:
        validate_mapping(mapping)  # défense en profondeur ; l'appelant a déjà validé
        source_name = str(mapping.constants["source_name"])
        session_spec = _require_entity(mapping, "session")
        child_specs = [e for e in mapping.entities if e.name != "session"]

        acc = _Accumulator()
        for record in records:
            self._process_record(record, source_name, session_spec, child_specs, acc)
        acc.backfill_session_intervals()
        return acc.result()

    # ------------------------------------------------------------------

    def _process_record(
        self,
        record: RawRecord,
        source_name: str,
        session_spec: EntitySpec,
        child_specs: list[EntitySpec],
        acc: _Accumulator,
    ) -> None:
        if record.parse_error is not None:
            acc.reject(record, RejectReason.UNPARSEABLE_RECORD, record.parse_error)
            return

        provenance = Provenance(record_index=record.index, record_sha256=record.sha256)
        try:
            session = self._build_session(record, source_name, session_spec, provenance, acc)
            for spec in child_specs:
                self._build_children(
                    record, source_name, spec, session.external_id, provenance, acc
                )
        except _RecordRejectedError as rejection:
            acc.reject(record, rejection.reason, rejection.detail)

    def _build_session(
        self,
        record: RawRecord,
        source_name: str,
        spec: EntitySpec,
        provenance: Provenance,
        acc: _Accumulator,
    ) -> Session:
        resolver = _Resolver(row=record.payload, root=record.payload)
        values = self._produce_fields(spec, resolver, acc)
        external_id = values.get("external_id") or _synthesize_id(
            source_name, spec.name, spec.key_fields, resolver
        )
        try:
            session = Session(
                source_name=source_name,
                external_id=str(external_id),
                provenance=provenance,
                agent_name=values.get("agent_name"),
                interval=Interval(values.get("started_at"), values.get("ended_at")),
                repository_name=values.get("repository_name"),
            )
        except (DomainError, ValueError) as error:
            raise _RecordRejectedError(
                RejectReason.SCHEMA_VIOLATION, f"session invalide : {error}"
            ) from error
        acc.add_session(session)
        return session

    def _build_children(
        self,
        record: RawRecord,
        source_name: str,
        spec: EntitySpec,
        session_external_id: str,
        provenance: Provenance,
        acc: _Accumulator,
    ) -> None:
        rows = _resolve_rows(record.payload, spec.iterate)
        for row in rows:
            resolver = _Resolver(row=row, root=record.payload)
            identity = _identity_values(spec.key_fields, resolver)
            if not acc.register_child(spec.name, session_external_id, identity):
                continue  # ligne déjà vue (doublon dans le fichier) — le premier gagne

            values = self._produce_fields(spec, resolver, acc)
            mapped_sequence = values.get("sequence")
            sequence = (
                int(mapped_sequence)
                if mapped_sequence is not None
                else acc.next_sequence(session_external_id, spec.name)
            )
            try:
                entity = _assemble_child(
                    spec.name, source_name, session_external_id, sequence, provenance, values
                )
            except (DomainError, ValueError) as error:
                raise _RecordRejectedError(
                    RejectReason.SCHEMA_VIOLATION, f"{spec.name} invalide : {error}"
                ) from error
            if isinstance(entity, ModelCall):
                acc.add_model_call(entity)
            else:
                acc.add_tool_call(entity)

    def _produce_fields(
        self, spec: EntitySpec, resolver: _Resolver, acc: _Accumulator
    ) -> dict[str, Any]:
        schema = TARGET_SCHEMA[spec.name]
        values: dict[str, Any] = {}
        for fs in spec.fields:
            outcome = _produce_one_field(fs, resolver)
            if outcome.skip:
                continue
            if outcome.missing:
                acc.note_missing(f"{spec.name}.{fs.target}")
                values[fs.target] = None
                continue
            target_field = schema.field(fs.target)
            expected_type = target_field.type if target_field else "string"
            values[fs.target] = _coerce(outcome.value, expected_type, spec.name, fs.target)

        for required_target in schema.required:
            if required_target == "external_id":
                continue  # synthétisé depuis identity.key_fields si absent
            if values.get(required_target) is None:
                raise _RecordRejectedError(
                    RejectReason.MISSING_REQUIRED_FIELD,
                    f"champ requis `{spec.name}.{required_target}` absent",
                )
        return values


# ---------------------------------------------------------------------------
# Résolution de chemins et de filtres
# ---------------------------------------------------------------------------


class _Resolver:
    """Lit un champ ``a.b.c`` d'abord dans la ligne courante, puis dans la racine."""

    def __init__(self, row: Any, root: Mapping[str, Any]) -> None:
        self._row = row
        self._root = root

    @property
    def root(self) -> Mapping[str, Any]:
        return self._root

    def get(self, path: str | None) -> Any:
        if not path:
            return None
        found = _dig(self._row, path)
        if found is None and self._row is not self._root:
            found = _dig(self._root, path)
        return found


def _dig(payload: Any, path: str) -> Any:
    """Lit ``a.b.c`` dans des dicts imbriqués. Un segment entier indexe une liste
    (``timing_events.0.timestamp``), négatif compris (``timing_events.-1.timestamp``)."""
    current = payload
    for part in path.split("."):
        if isinstance(current, Sequence) and not isinstance(current, (str, bytes)):
            try:
                index = int(part)
            except ValueError:
                return None
            if not -len(current) <= index < len(current):
                return None
            current = current[index]
            continue
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _resolve_rows(payload: Mapping[str, Any], iterate: IterateSpec) -> list[dict[str, Any]]:
    if not iterate.path:
        candidates: list[Any] = [payload]
    else:
        target = _dig(payload, iterate.path)
        candidates = list(target) if isinstance(target, list) else []
    rows = [row for row in candidates if isinstance(row, Mapping)]
    return [dict(row) for row in rows if _matches(row, iterate.where)]


def _matches(row: Mapping[str, Any], clauses: tuple[WhereClause, ...]) -> bool:
    return all(_matches_one(row, clause) for clause in clauses)


def _matches_one(row: Mapping[str, Any], clause: WhereClause) -> bool:
    actual = _dig(row, clause.field)
    match clause.op:
        case WhereOp.EQ:
            return bool(actual == clause.value)
        case WhereOp.NE:
            return bool(actual != clause.value)
        case WhereOp.IN:
            return isinstance(clause.value, (list, tuple)) and actual in clause.value
        case WhereOp.EXISTS:
            return (actual is not None) == bool(clause.value)
        case WhereOp.GT:
            return actual is not None and clause.value is not None and bool(actual > clause.value)
        case WhereOp.LT:
            return actual is not None and clause.value is not None and bool(actual < clause.value)
    return False


# ---------------------------------------------------------------------------
# Production d'un champ
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _FieldOutcome:
    value: Any = None
    missing: bool = False
    skip: bool = False


_NO_SOURCE_TRANSFORMS = {"const", "coalesce"}


def _produce_one_field(fs: FieldSpec, resolver: _Resolver) -> _FieldOutcome:
    raw = None if fs.transform in _NO_SOURCE_TRANSFORMS else resolver.get(fs.source)

    if raw is None and fs.transform not in _NO_SOURCE_TRANSFORMS:
        if fs.required:
            raise _RecordRejectedError(
                RejectReason.MISSING_REQUIRED_FIELD,
                f"champ requis `{fs.target}` absent (source `{fs.source}`)",
            )
        return _on_error(fs, f"valeur absente pour `{fs.target}`")

    try:
        value = apply_transform(fs.transform, raw, fs.args, context=resolver.root)
    except TransformError as error:
        if fs.required:
            raise _RecordRejectedError(
                RejectReason.TRANSFORM_FAILED, f"`{fs.target}` : {error}"
            ) from error
        return _on_error(fs, f"`{fs.target}` : {error}")

    if value is None and not fs.required:
        return _on_error(fs, f"transformation vide pour `{fs.target}`")
    return _FieldOutcome(value=value)


def _on_error(fs: FieldSpec, detail: str) -> _FieldOutcome:
    match fs.on_error:
        case OnError.REJECT:
            raise _RecordRejectedError(RejectReason.TRANSFORM_FAILED, detail)
        case OnError.SKIP:
            return _FieldOutcome(skip=True)
        case _:
            return _FieldOutcome(missing=True)


# ---------------------------------------------------------------------------
# Coercition vers les types du domaine
# ---------------------------------------------------------------------------


def _coerce(value: Any, expected: str, entity: str, target: str) -> Any:
    try:
        match expected:
            case "int":
                return int(value)
            case "float":
                return float(value)
            case "datetime":
                return _to_datetime(value)
            case "call_status":
                return CallStatus(value)
            case "error_type":
                return ErrorType(value)
            case _:
                return value
    except (TypeError, ValueError) as error:
        raise _RecordRejectedError(
            RejectReason.SCHEMA_VIOLATION,
            f"`{entity}.{target}` : {value!r} n'est pas un(e) {expected} valide",
        ) from error


def _to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


# ---------------------------------------------------------------------------
# Assemblage des entités filles
# ---------------------------------------------------------------------------


def _assemble_child(
    name: str,
    source_name: str,
    session_external_id: str,
    sequence: int,
    provenance: Provenance,
    values: Mapping[str, Any],
) -> ModelCall | ToolCall:
    interval = Interval(values.get("started_at"), values.get("ended_at"))
    if name == "model_call":
        return ModelCall(
            source_name=source_name,
            session_external_id=session_external_id,
            sequence=sequence,
            model_name=str(values.get("model_name")),
            provenance=provenance,
            provider=values.get("provider"),
            tokens=TokenUsage(
                prompt_tokens=values.get("prompt_tokens"),
                completion_tokens=values.get("completion_tokens"),
                cached_tokens=values.get("cached_tokens"),
            ),
            cost_usd=values.get("cost_usd"),
            interval=interval,
            status=values.get("status") or CallStatus.UNKNOWN,
            error_type=values.get("error_type"),
        )
    return ToolCall(
        source_name=source_name,
        session_external_id=session_external_id,
        sequence=sequence,
        tool_name=str(values.get("tool_name")),
        provenance=provenance,
        model_call_sequence=values.get("model_call_sequence"),
        interval=interval,
        status=values.get("status") or CallStatus.UNKNOWN,
        error_type=values.get("error_type"),
        input_bytes=values.get("input_bytes"),
        output_bytes=values.get("output_bytes"),
    )


# ---------------------------------------------------------------------------


def _require_entity(mapping: MappingDefinition, name: str) -> EntitySpec:
    spec = mapping.entity(name)
    if spec is None:  # pragma: no cover - garanti par validate_mapping
        raise InvalidMappingError(f"entité `{name}` absente du mapping")
    return spec


def _identity_values(key_fields: tuple[str, ...], resolver: _Resolver) -> tuple[str, ...]:
    """Valeurs de ``identity.key_fields`` — l'identité stable de la ligne dans la source."""
    return tuple(str(resolver.get(key)) for key in key_fields)


def _synthesize_id(
    source_name: str, entity: str, key_fields: tuple[str, ...], resolver: _Resolver
) -> str:
    parts = []
    for key in key_fields:
        value = resolver.get(key)
        if value is None:
            raise _RecordRejectedError(
                RejectReason.MISSING_REQUIRED_FIELD,
                f"clé naturelle incomplète : `{key}` absent (identity.key_fields)",
            )
        parts.append(str(value))
    seed = "|".join([source_name, entity, *parts])
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()
