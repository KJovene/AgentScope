"""Vérifie le contrat et le déterminisme de FakeLLMProvider (I3.2)."""

from agentscope.application.ports.llm_provider import LLMProvider, MappingProposal
from agentscope.infrastructure.llm.fake_provider import FakeLLMProvider


def test_fake_provider_satisfies_llm_provider_protocol() -> None:
    provider: LLMProvider = FakeLLMProvider()

    assert isinstance(provider, LLMProvider)
    assert provider.name == "fake"


def test_propose_mapping_is_deterministic_for_the_same_sample() -> None:
    provider = FakeLLMProvider()
    sample = [{"session_id": "s1", "agent": "claude"}, {"session_id": "s2", "agent": "codex"}]

    first = provider.propose_mapping(profile=None, sample=sample, target_schema=None)
    second = provider.propose_mapping(profile=None, sample=sample, target_schema=None)

    assert first == second


def test_propose_mapping_derives_fields_from_sample() -> None:
    provider = FakeLLMProvider()
    sample = [{"session_id": "s1", "agent": "claude"}]

    proposal = provider.propose_mapping(profile=None, sample=sample, target_schema=None)

    assert isinstance(proposal, MappingProposal)
    mapped_fields = proposal.definition["entities"]["record"]["fields"]
    assert set(mapped_fields) == {"session_id", "agent"}
    assert {e.target_field for e in proposal.explanations} == {"session_id", "agent"}
    assert proposal.ambiguities == []
    assert proposal.unmapped_fields == []


def test_chat_returns_a_reply_without_revised_proposal() -> None:
    provider = FakeLLMProvider()

    reply = provider.chat(conversation_id="conv-1", messages=[], context=None)

    assert reply.revised_proposal is None
    assert reply.text
