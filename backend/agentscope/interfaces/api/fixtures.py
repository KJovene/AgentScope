"""
Fixtures statiques servies par les endpoints stub (I4.1).

Objectif de cette issue : débloquer le frontend (I0.6) avec une spec OpenAPI
complète et des réponses de forme correcte, AVANT que les use cases réels
(EPIC 1/2/3) soient branchés. Rien ici ne touche une base de données.
Le câblage réel (I4.10) remplacera ces fonctions par des appels aux use cases
via `interfaces/api/dependencies.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime

_NOW = datetime(2026, 9, 7, 9, 30, tzinfo=UTC)

IMPORT_REPORT = {
    "id": "imp_0001",
    "source_id": "src_tracelab",
    "mapping_id": "map_tracelab_v1",
    "status": "success",
    "imported_count": 128,
    "duplicate_count": 0,
    "rejected_count": 3,
    "missing_info_count": {"model_call.prompt_tokens": 2},
    "imported_at": _NOW,
}

REJECTS = [
    {
        "record_index": 42,
        "reason_code": "missing_required_field",
        "reason_detail": "Champ requis 'model' absent de l'événement.",
        "payload": {"type": "model", "usage": {"input_tokens": 12}},
    },
    {
        "record_index": 57,
        "reason_code": "unparseable_record",
        "reason_detail": "Ligne JSONL invalide (JSON malformé).",
        "payload": {},
    },
]

FIELD_PROFILE_SET = {
    "record_count": 500,
    "fields": [
        {
            "path": "session_id",
            "inferred_type": "string",
            "null_ratio": 0.0,
            "distinct_count": 128,
            "sample_values": ["sess_a1", "sess_a2"],
        },
        {
            "path": "usage.input_tokens",
            "inferred_type": "int",
            "null_ratio": 0.04,
            "distinct_count": 87,
            "sample_values": [120, 340, 58],
        },
    ],
}

MAPPING_PROPOSAL = {
    "definition": {
        "mapping_id": "draft",
        "name": "tracelab-jsonl",
        "version": 1,
        "source_format": "jsonl",
        "constants": {"source_name": "TraceLab"},
        "entities": {},
        "unmapped_fields": ["debug"],
    },
    "explanations": [
        {
            "target_field": "model_call.prompt_tokens",
            "source_field": "usage.input_tokens",
            "rationale": "Nom et type cohérents avec un compteur de tokens en entrée.",
            "confidence": 0.92,
        }
    ],
    "ambiguities": ["'agent' pourrait être un nom d'agent ou un identifiant utilisateur."],
    "unmapped_fields": ["debug", "internal_flags"],
}

MAPPING = {
    "mapping_id": "map_tracelab_v1",
    "name": "tracelab-jsonl",
    "version": 1,
    "source_format": "jsonl",
    "definition": MAPPING_PROPOSAL["definition"],
    "is_active": True,
    "created_at": _NOW,
    "created_by": "stub",
}

PREVIEW_RESULT = {
    "rows": [
        {"entity": "session", "row": {"external_id": "sess_a1", "agent_name": "claude-code"}},
        {"entity": "model_call", "row": {"model_name": "claude-sonnet-5", "prompt_tokens": 340}},
    ],
    "rejects": REJECTS[:1],
}

CHAT_REPLY = {
    "text": (
        "J'ai mappé 'usage.input_tokens' vers prompt_tokens avec une confiance élevée. "
        "Le champ 'agent' reste ambigu : dois-je le traiter comme nom d'agent ?"
    ),
    "revised_proposal": None,
}

INDICATORS = {
    "sessions": 128,
    "tokens_in": 45210,
    "tokens_out": 18904,
    "tokens_cached": 6100,
    "cost_usd": 12.47,
    "median_session_duration_s": 94.5,
    "error_rate": 0.031,
    "cache_hit_rate": 0.135,
}

TIMESERIES = [
    {"timestamp": _NOW, "value": 12},
    {"timestamp": _NOW, "value": 18},
]

TOOL_USAGE = [
    {"tool_name": "read_file", "n_calls": 210, "n_errors": 4, "avg_duration_ms": 82.3},
    {"tool_name": "run_tests", "n_calls": 64, "n_errors": 9, "avg_duration_ms": 4310.0},
]

SESSION_ROW = {
    "id": "sess_a1",
    "source": "TraceLab",
    "agent": "claude-code",
    "model": "claude-sonnet-5",
    "started_at": _NOW,
    "duration_ms": 94500,
    "n_model_calls": 6,
    "n_tool_calls": 11,
    "total_tokens": 4200,
    "cached_tokens": 600,
    "total_cost_usd": 0.87,
    "n_errors": 0,
}

SESSION_DETAIL = {
    **SESSION_ROW,
    "model_calls": [
        {
            "id": "mc_1",
            "model_name": "claude-sonnet-5",
            "prompt_tokens": 340,
            "completion_tokens": 210,
            "total_tokens": 550,
            "status": "success",
            "started_at": _NOW,
            "duration_ms": 1200,
        }
    ],
    "tool_calls": [
        {
            "id": "tc_1",
            "tool_name": "read_file",
            "status": "success",
            "started_at": _NOW,
            "duration_ms": 40,
        }
    ],
    "raw_record_ref": "raw_0042",
}

SOURCES = [
    {"id": "src_tracelab", "name": "TraceLab"},
    {"id": "src_swechat", "name": "SWE-chat"},
]

DATA_QUALITY = [
    {
        "source_id": "src_tracelab",
        "imported_count": 128,
        "duplicate_count": 0,
        "rejected_count": 3,
        "completeness_ratio": 0.97,
    }
]
