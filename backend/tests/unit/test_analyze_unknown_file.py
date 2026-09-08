"""Vérifie le use case AnalyzeUnknownFile (I3.7)."""

import pytest

from agentscope.application.ports.llm_provider import MappingProposal
from agentscope.application.use_cases.analyze_unknown_file import (
    AnalysisFailedError,
    AnalysisResult,
    AnalyzeUnknownFile,
)
from agentscope.domain import FieldProfileSet, RawRecord
from agentscope.infrastructure.llm.fake_provider import FakeLLMProvider
from agentscope.infrastructure.profiling.field_profiler import DefaultFieldProfiler

_VALID_DEFINITION = {
    "name": "test-mapping",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "TestSource"},
    "entities": {
        "session": {
            "iterate": {"path": "", "where": []},
            "identity": {"key_fields": ["session_id"]},
            "fields": {
                "external_id": {"from": "session_id", "transform": "identity"},
            },
        }
    },
}


class _StubValidProvider:
    """Renvoie toujours un mapping conforme au contrat."""

    name = "stub-valid"

    def propose_mapping(self, profile, sample, target_schema):
        return MappingProposal(
            definition=_VALID_DEFINITION,
            explanations=[],
            ambiguities=[],
            unmapped_fields=[],
        )

    def chat(self, conversation_id, messages, context):
        raise NotImplementedError


def _records() -> list[RawRecord]:
    return [
        RawRecord(index=0, payload={"session_id": "s1"}, sha256="a"),
        RawRecord(index=1, payload={"session_id": "s2"}, sha256="b"),
    ]


def test_execute_returns_validated_proposal_on_success() -> None:
    use_case = AnalyzeUnknownFile(
        profiler=DefaultFieldProfiler(),
        llm_provider=_StubValidProvider(),
    )

    result = use_case.execute(_records())

    assert isinstance(result, AnalysisResult)
    assert result.proposal.definition == _VALID_DEFINITION


def test_execute_raises_explicit_error_on_invalid_proposal() -> None:
    """FakeLLMProvider propose un mapping "record" plat, non conforme au schéma cible."""
    use_case = AnalyzeUnknownFile(
        profiler=DefaultFieldProfiler(),
        llm_provider=FakeLLMProvider(),
    )

    with pytest.raises(AnalysisFailedError, match="fake"):
        use_case.execute(_records())


def test_execute_profiles_the_given_records() -> None:
    seen_profile: dict[str, FieldProfileSet] = {}

    class _CapturingProfiler:
        def profile(self, records, sample_size):
            profile = DefaultFieldProfiler().profile(records, sample_size)
            seen_profile["value"] = profile
            return profile

    use_case = AnalyzeUnknownFile(
        profiler=_CapturingProfiler(),
        llm_provider=_StubValidProvider(),
    )

    use_case.execute(_records())

    profile = seen_profile["value"]
    assert profile.record_count == 2
    assert profile.by_path("session_id") is not None
