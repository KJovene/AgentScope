"""Profilage déterministe des champs source."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

from agentscope.domain import FieldProfile, FieldProfileSet, RawRecord
from agentscope.infrastructure.profiling.sensitive_filter import DefaultSensitiveFilter


class DefaultFieldProfiler:
    """Profile les champs imbriqués d'enregistrements bruts."""

    def __init__(self, sensitive_filter: DefaultSensitiveFilter | None = None) -> None:
        self._sensitive_filter = sensitive_filter or DefaultSensitiveFilter()

    def profile(self, records: Iterable[RawRecord], sample_size: int) -> FieldProfileSet:
        if sample_size < 0:
            raise ValueError("sample_size doit être >= 0")

        record_list = list(records)
        values_by_path: dict[str, list[Any]] = defaultdict(list)
        all_paths: set[str] = set()
        for record in record_list:
            safe_payload = self._sensitive_filter.scrub(record.payload)
            flattened = dict(self._flatten(safe_payload))
            all_paths.update(flattened)
            for path in all_paths:
                values_by_path[path].append(flattened.get(path))

            for path in all_paths - flattened.keys():
                values_by_path[path][-1] = None

        profiles = tuple(
            self._make_profile(path, values_by_path[path], sample_size)
            for path in sorted(all_paths)
        )
        return FieldProfileSet(record_count=len(record_list), fields=profiles)

    @classmethod
    def _flatten(cls, value: Mapping[str, Any], prefix: str = "") -> Iterable[tuple[str, Any]]:
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else key
            item = value[key]
            if isinstance(item, Mapping):
                yield from cls._flatten(item, path)
            else:
                yield path, item

    @classmethod
    def _make_profile(cls, path: str, values: list[Any], sample_size: int) -> FieldProfile:
        non_null = [value for value in values if value is not None]
        distinct = {cls._canonical(value) for value in non_null}
        samples: list[Any] = []
        seen_samples: set[str] = set()
        for value in non_null:
            key = cls._canonical(value)
            if key not in seen_samples and len(samples) < sample_size:
                samples.append(value)
                seen_samples.add(key)
        return FieldProfile(
            path=path,
            inferred_type=cls._infer_type(non_null),
            null_ratio=(len(values) - len(non_null)) / len(values) if values else 0.0,
            distinct_count=len(distinct),
            sample_values=tuple(samples),
        )

    @staticmethod
    def _infer_type(values: list[Any]) -> str:
        if not values:
            return "null"
        types = {DefaultFieldProfiler._type_name(value) for value in values}
        return types.pop() if len(types) == 1 else "mixed"

    @staticmethod
    def _type_name(value: Any) -> str:
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, datetime):
            return "datetime"
        if isinstance(value, date):
            return "datetime"
        if isinstance(value, str):
            return "string"
        if isinstance(value, Mapping):
            return "object"
        if isinstance(value, (list, tuple, set)):
            return "array"
        return "object"

    @staticmethod
    def _canonical(value: Any) -> str:
        return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)