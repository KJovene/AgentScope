"""Registre whitelisté des transformations de mapping."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Callable

from agentscope.domain import InvalidMappingError


class TransformError(ValueError):
    """Une valeur ou des arguments ne respectent pas une transformation."""


Transform = Callable[[Any, Mapping[str, Any], Mapping[str, Any] | None], Any]


def _identity(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> Any:
    return value


def _to_int(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise TransformError(f"impossible de convertir {value!r} en entier") from error


def _to_float(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise TransformError(f"impossible de convertir {value!r} en nombre") from error


def _to_iso8601(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> str | None:
    if value is None:
        return None
    unit = args.get("unit")
    try:
        if unit == "epoch_s":
            moment = datetime.fromtimestamp(float(value), tz=UTC)
        elif unit == "epoch_ms":
            moment = datetime.fromtimestamp(float(value) / 1000, tz=UTC)
        elif unit == "iso":
            text = str(value)
            input_format = args.get("input_format")
            moment = datetime.strptime(text, input_format) if input_format else datetime.fromisoformat(text)
            moment = moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)
        else:
            raise TransformError("to_iso8601 attend unit=epoch_s, epoch_ms ou iso")
    except (TypeError, ValueError, OverflowError) as error:
        if isinstance(error, TransformError):
            raise
        raise TransformError(f"impossible de convertir {value!r} en date ISO-8601") from error
    return moment.isoformat().replace("+00:00", "Z")


def _string_operation(value: Any, operation: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TransformError(f"{operation} attend une chaîne")
    return getattr(value, operation)()


def _lower(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> str | None:
    return _string_operation(value, "lower")


def _upper(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> str | None:
    return _string_operation(value, "upper")


def _trim(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> str | None:
    return _string_operation(value, "strip")


def _json_stringify(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> str | None:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as error:
        raise TransformError("valeur non sérialisable en JSON") from error


def _const(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> Any:
    if "value" not in args:
        raise TransformError("const attend l'argument value")
    return args["value"]


def _coalesce(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> Any:
    fields = args.get("fields")
    if not isinstance(fields, list) or not all(isinstance(field, str) for field in fields):
        raise TransformError("coalesce attend fields=[...]")
    if context is None:
        raise TransformError("coalesce nécessite un contexte d'enregistrement")
    for field in fields:
        candidate = context.get(field)
        if candidate is not None:
            return candidate
    return None


def _map_enum(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> Any:
    mapping = args.get("mapping")
    if not isinstance(mapping, Mapping):
        raise TransformError("map_enum attend mapping={...}")
    if value in mapping:
        return mapping[value]
    if isinstance(value, bool):
        json_key = str(value).lower()
        if json_key in mapping:
            return mapping[json_key]
    return args.get("default")


def _split(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TransformError("split attend une chaîne")
    separator = args.get("sep")
    index = args.get("index")
    if not isinstance(separator, str) or not isinstance(index, int):
        raise TransformError("split attend sep=... et index=...")
    try:
        return value.split(separator)[index]
    except IndexError as error:
        raise TransformError(f"index {index} absent après split") from error


def _regex_extract(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not isinstance(args.get("pattern"), str):
        raise TransformError("regex_extract attend une chaîne et pattern=...")
    group = args.get("group", 1)
    if not isinstance(group, (int, str)):
        raise TransformError("regex_extract attend group entier ou nommé")
    try:
        match = re.search(args["pattern"], value)
    except re.error as error:
        raise TransformError(f"pattern regex invalide : {error}") from error
    if match is None:
        return None
    try:
        return match.group(group)
    except (IndexError, KeyError) as error:
        raise TransformError(f"groupe regex absent : {group!r}") from error


def _cents_to_usd(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> float | None:
    if value is None:
        return None
    try:
        return float(Decimal(str(value)) / Decimal(100))
    except (TypeError, ValueError, ArithmeticError) as error:
        raise TransformError(f"impossible de convertir {value!r} en USD") from error


def _ms_to_s(value: Any, args: Mapping[str, Any], context: Mapping[str, Any] | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value) / 1000
    except (TypeError, ValueError) as error:
        raise TransformError(f"impossible de convertir {value!r} en secondes") from error


TRANSFORM_REGISTRY: dict[str, Transform] = {
    "identity": _identity,
    "to_int": _to_int,
    "to_float": _to_float,
    "to_iso8601": _to_iso8601,
    "lower": _lower,
    "upper": _upper,
    "trim": _trim,
    "json_stringify": _json_stringify,
    "const": _const,
    "coalesce": _coalesce,
    "map_enum": _map_enum,
    "split": _split,
    "regex_extract": _regex_extract,
    "cents_to_usd": _cents_to_usd,
    "ms_to_s": _ms_to_s,
}


def apply_transform(
    name: str,
    value: Any = None,
    args: Mapping[str, Any] | None = None,
    context: Mapping[str, Any] | None = None,
) -> Any:
    """Applique une transformation autorisée, sans jamais exécuter du code fourni."""
    transform = TRANSFORM_REGISTRY.get(name)
    if transform is None:
        raise InvalidMappingError(f"Transformation inconnue ou non whitelistée : {name}")
    return transform(value, args or {}, context)