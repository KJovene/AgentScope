"""Parcours complet analyse -> validation -> sauvegarde -> import (issue I3.12).

Vérifie que l'enchaînement ``AnalyzeUnknownFile`` -> ``SaveMapping``/``UpdateMapping``
-> ``ImportFile`` fonctionne de bout en bout **sans aucun appel réseau**
(fournisseurs de test déterministes, jamais de SDK/HTTP réel), et qu'un mapping
enregistré reste utilisable — et évolutif — après un changement de modèle :
``ImportFile`` ne dépend structurellement d'aucun ``LLMProvider``, le mapping
persisté suffit pour tous les imports suivants.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from agentscope.application.ports.llm_provider import (
    ChatReply,
    MappingContext,
    MappingProposal,
    TargetSchema,
)
from agentscope.application.use_cases.analyze_unknown_file import AnalyzeUnknownFile
from agentscope.application.use_cases.import_file import ImportFile
from agentscope.application.use_cases.manage_mappings import SaveMapping, UpdateMapping
from agentscope.domain import FieldProfileSet, FileFormat, ImportStatus, RawRecord, Source
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from agentscope.infrastructure.profiling.field_profiler import DefaultFieldProfiler
from agentscope.infrastructure.readers.jsonl_reader import JsonlReader

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
MakeUow = Callable[[], SqlAlchemyUnitOfWork]

_DEFINITION_V1: dict[str, Any] = {
    "name": "demo-jsonl",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "demo"},
    "entities": {
        "session": {
            "iterate": {"path": "", "where": []},
            "identity": {"key_fields": ["sid"]},
            "fields": {
                "external_id": {
                    "from": "sid",
                    "transform": "identity",
                    "required": True,
                    "on_error": "reject",
                },
            },
        },
    },
}

_DEFINITION_V2: dict[str, Any] = {
    **_DEFINITION_V1,
    "entities": {
        "session": {
            **_DEFINITION_V1["entities"]["session"],
            "fields": {
                **_DEFINITION_V1["entities"]["session"]["fields"],
                "agent_name": {"from": "agent", "transform": "lower"},
            },
        },
    },
}

ROWS: list[dict[str, Any]] = [
    {"sid": "s1", "agent": "Claude"},
    {"sid": "s2", "agent": "Codex"},
]


class _StubModelV1:
    """Fournisseur déterministe (aucun appel réseau) simulant un premier modèle."""

    name = "stub-model-v1"

    def propose_mapping(
        self,
        profile: FieldProfileSet,
        sample: list[dict[str, Any]],
        target_schema: TargetSchema,
    ) -> MappingProposal:
        return MappingProposal(
            definition=_DEFINITION_V1, explanations=[], ambiguities=[], unmapped_fields=[]
        )

    def chat(self, conversation_id: str, messages: list[Any], context: MappingContext) -> ChatReply:
        raise NotImplementedError("non utilisé dans ce parcours")


class _StubModelV2:
    """Fournisseur déterministe simulant un second modèle (« changement de modèle »)."""

    name = "stub-model-v2"

    def propose_mapping(
        self,
        profile: FieldProfileSet,
        sample: list[dict[str, Any]],
        target_schema: TargetSchema,
    ) -> MappingProposal:
        return MappingProposal(
            definition=_DEFINITION_V2, explanations=[], ambiguities=[], unmapped_fields=[]
        )

    def chat(self, conversation_id: str, messages: list[Any], context: MappingContext) -> ChatReply:
        raise NotImplementedError("non utilisé dans ce parcours")


def _jsonl(rows: list[dict[str, Any]]) -> bytes:
    return ("\n".join(json.dumps(row) for row in rows)).encode("utf-8")


def _raw_records(rows: list[dict[str, Any]]) -> list[RawRecord]:
    return [RawRecord(index=i, payload=row, sha256=f"sha-{i}") for i, row in enumerate(rows)]


def _import_file(make_uow: MakeUow) -> ImportFile:
    return ImportFile(uow_factory=make_uow, readers=[JsonlReader()], clock=lambda: NOW)


def test_parcours_analyse_validation_sauvegarde_import_sans_reseau(make_uow: MakeUow) -> None:
    analyze = AnalyzeUnknownFile(profiler=DefaultFieldProfiler(), llm_provider=_StubModelV1())
    result = analyze.execute(_raw_records(ROWS))

    with make_uow() as uow:
        uow.reference.add_source(Source(name="demo", display_name="Demo"))
        SaveMapping(uow.mappings, clock=lambda: NOW).execute(
            name="demo-jsonl",
            source_name="demo",
            source_format=FileFormat.JSONL,
            definition=result.proposal.definition,
            created_by=_StubModelV1.name,
        )
        uow.commit()

    report = _import_file(make_uow).execute(
        content=_jsonl(ROWS),
        original_filename="demo.jsonl",
        file_format=FileFormat.JSONL,
        mapping_name="demo-jsonl",
    )

    assert report.status is ImportStatus.SUCCEEDED
    assert report.imported_count == 2  # 2 sessions ; seule `external_id` est mappée en v1
    assert report.rejected_count == 0


def test_mapping_enregistre_reste_utilisable_apres_changement_de_modele(
    make_uow: MakeUow,
) -> None:
    # Mapping v1 sauvegardé après analyse par un premier modèle.
    proposal_v1 = (
        AnalyzeUnknownFile(profiler=DefaultFieldProfiler(), llm_provider=_StubModelV1())
        .execute(_raw_records(ROWS))
        .proposal
    )

    with make_uow() as uow:
        uow.reference.add_source(Source(name="demo", display_name="Demo"))
        SaveMapping(uow.mappings, clock=lambda: NOW).execute(
            name="demo-jsonl",
            source_name="demo",
            source_format=FileFormat.JSONL,
            definition=proposal_v1.definition,
            created_by=_StubModelV1.name,
        )
        uow.commit()

    # Premier import : réussit sans jamais solliciter de `LLMProvider` — `ImportFile`
    # n'en dépend structurellement pas (cf. sa signature).
    first_report = _import_file(make_uow).execute(
        content=_jsonl(ROWS),
        original_filename="import-1.jsonl",
        file_format=FileFormat.JSONL,
        mapping_name="demo-jsonl",
    )
    assert first_report.status is ImportStatus.SUCCEEDED

    # Changement de modèle : un second fournisseur propose une meilleure définition.
    proposal_v2 = (
        AnalyzeUnknownFile(profiler=DefaultFieldProfiler(), llm_provider=_StubModelV2())
        .execute(_raw_records(ROWS))
        .proposal
    )
    assert "agent_name" in proposal_v2.definition["entities"]["session"]["fields"]

    with make_uow() as uow:
        updated = UpdateMapping(uow.mappings, clock=lambda: NOW).execute(
            name="demo-jsonl", definition=proposal_v2.definition, created_by=_StubModelV2.name
        )
        uow.commit()
    assert updated.version == 2

    # Le mapping mis à jour est repris automatiquement (dernière version active) pour
    # un nouvel import, toujours sans repasser par aucun `LLMProvider`.
    second_rows = [{"sid": "s3", "agent": "Gemini"}]
    second_report = _import_file(make_uow).execute(
        content=_jsonl(second_rows),
        original_filename="import-2.jsonl",
        file_format=FileFormat.JSONL,
        mapping_name="demo-jsonl",
    )
    assert second_report.status is ImportStatus.SUCCEEDED
    assert second_report.imported_count == 1
