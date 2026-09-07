"""Vérifie qu'une implémentation minimale respecte le contrat LLMProvider."""

from agentscope.application.ports.llm_provider import (
    ChatReply,
    LLMProvider,
    MappingProposal,
)


class _StubLLMProvider:
    """Implémentation minimale, utilisée uniquement pour tester le contrat."""

    name = "stub"

    def propose_mapping(
        self, profile: object, sample: list, target_schema: object
    ) -> MappingProposal:
        return MappingProposal(definition={}, explanations=[], ambiguities=[], unmapped_fields=[])

    def chat(self, conversation_id: str, messages: list, context: object) -> ChatReply:
        return ChatReply(text="", revised_proposal=None)


def test_stub_provider_satisfies_llm_provider_protocol() -> None:
    provider: LLMProvider = _StubLLMProvider()

    assert isinstance(provider, LLMProvider)
    assert provider.name == "stub"


def test_propose_mapping_returns_mapping_proposal() -> None:
    provider: LLMProvider = _StubLLMProvider()

    proposal = provider.propose_mapping(profile=None, sample=[], target_schema=None)

    assert isinstance(proposal, MappingProposal)
    assert proposal.unmapped_fields == []


def test_chat_returns_chat_reply() -> None:
    provider: LLMProvider = _StubLLMProvider()

    reply = provider.chat(conversation_id="conv-1", messages=[], context=None)

    assert isinstance(reply, ChatReply)
    assert reply.revised_proposal is None
