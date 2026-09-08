"""Gestion des mappings persistés (issue I3.10) : Save / Update / List / Get."""

from __future__ import annotations

import copy
from datetime import UTC, datetime

import pytest

from agentscope.application.use_cases.manage_mappings import (
    GetMapping,
    ListMappings,
    MappingAlreadyExistsError,
    MappingNotFoundError,
    SaveMapping,
    UpdateMapping,
)
from agentscope.domain import FileFormat, InvalidMappingError, SourceMapping

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

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


class _FakeMappingRepository:
    """Adaptateur en mémoire respectant le port `MappingRepository`."""

    def __init__(self) -> None:
        self._rows: list[SourceMapping] = []

    def add(self, mapping: SourceMapping) -> None:
        self._rows.append(mapping)

    def get(self, name: str, version: int | None = None) -> SourceMapping | None:
        candidates = [m for m in self._rows if m.name == name]
        if version is not None:
            return next((m for m in candidates if m.version == version), None)
        active = [m for m in candidates if m.is_active]
        return max(active, key=lambda m: m.version) if active else None

    def list_for_source(self, source_name: str) -> list[SourceMapping]:
        return sorted(
            (m for m in self._rows if m.source_name == source_name),
            key=lambda m: (m.name, m.version),
        )

    def list_all(self) -> list[SourceMapping]:
        return sorted(self._rows, key=lambda m: (m.source_name, m.name, m.version))


def _clock() -> datetime:
    return NOW


def test_save_puis_get_retrouve_le_mapping() -> None:
    repo = _FakeMappingRepository()
    saved = SaveMapping(repo, clock=_clock).execute(
        name="tracelab-jsonl",
        source_name="TraceLab",
        source_format=FileFormat.JSONL,
        definition=VALID_DEFINITION,
    )

    fetched = GetMapping(repo).execute(name="tracelab-jsonl")

    assert saved.version == 1
    assert fetched == saved


def test_save_avec_un_nom_deja_pris_est_refuse() -> None:
    repo = _FakeMappingRepository()
    save = SaveMapping(repo, clock=_clock)
    save.execute(
        name="tracelab-jsonl",
        source_name="TraceLab",
        source_format=FileFormat.JSONL,
        definition=VALID_DEFINITION,
    )

    with pytest.raises(MappingAlreadyExistsError):
        save.execute(
            name="tracelab-jsonl",
            source_name="TraceLab",
            source_format=FileFormat.JSONL,
            definition=VALID_DEFINITION,
        )


def test_save_avec_une_definition_invalide_est_refuse() -> None:
    repo = _FakeMappingRepository()
    broken = {**VALID_DEFINITION, "source_format": "xml"}

    with pytest.raises(InvalidMappingError):
        SaveMapping(repo, clock=_clock).execute(
            name="tracelab-jsonl",
            source_name="TraceLab",
            source_format=FileFormat.JSONL,
            definition=broken,
        )
    assert repo.list_all() == []


def test_update_cree_une_nouvelle_version() -> None:
    repo = _FakeMappingRepository()
    SaveMapping(repo, clock=_clock).execute(
        name="tracelab-jsonl",
        source_name="TraceLab",
        source_format=FileFormat.JSONL,
        definition=VALID_DEFINITION,
    )
    revised = copy.deepcopy(VALID_DEFINITION)
    revised["entities"]["session"]["fields"]["agent_name"] = {
        "from": "agent",
        "transform": "lower",
    }

    updated = UpdateMapping(repo, clock=_clock).execute(
        name="tracelab-jsonl", definition=revised
    )

    assert updated.version == 2
    assert GetMapping(repo).execute(name="tracelab-jsonl") == updated
    assert GetMapping(repo).execute(name="tracelab-jsonl", version=1).version == 1


def test_update_d_un_mapping_inconnu_est_refuse() -> None:
    repo = _FakeMappingRepository()

    with pytest.raises(MappingNotFoundError):
        UpdateMapping(repo, clock=_clock).execute(
            name="does-not-exist", definition=VALID_DEFINITION
        )


def test_update_avec_une_definition_invalide_est_refuse() -> None:
    repo = _FakeMappingRepository()
    SaveMapping(repo, clock=_clock).execute(
        name="tracelab-jsonl",
        source_name="TraceLab",
        source_format=FileFormat.JSONL,
        definition=VALID_DEFINITION,
    )
    broken = {**VALID_DEFINITION, "source_format": "xml"}

    with pytest.raises(InvalidMappingError):
        UpdateMapping(repo, clock=_clock).execute(name="tracelab-jsonl", definition=broken)
    assert GetMapping(repo).execute(name="tracelab-jsonl").version == 1


def test_list_all_et_list_for_source() -> None:
    repo = _FakeMappingRepository()
    SaveMapping(repo, clock=_clock).execute(
        name="tracelab-jsonl",
        source_name="TraceLab",
        source_format=FileFormat.JSONL,
        definition=VALID_DEFINITION,
    )
    other = {**VALID_DEFINITION, "name": "swe-chat-jsonl", "constants": {"source_name": "SweChat"}}
    SaveMapping(repo, clock=_clock).execute(
        name="swe-chat-jsonl",
        source_name="SweChat",
        source_format=FileFormat.JSONL,
        definition=other,
    )

    all_mappings = ListMappings(repo).execute()
    tracelab_only = ListMappings(repo).execute(source_name="TraceLab")

    assert {m.name for m in all_mappings} == {"tracelab-jsonl", "swe-chat-jsonl"}
    assert [m.name for m in tracelab_only] == ["tracelab-jsonl"]


def test_get_mapping_inconnu_renvoie_none() -> None:
    repo = _FakeMappingRepository()

    assert GetMapping(repo).execute(name="does-not-exist") is None
