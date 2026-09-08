"""Vérifie le use case ChatAboutMapping (I3.8)."""

import inspect

from agentscope.application.ports.llm_provider import ChatMessage, ChatReply, MappingProposal
from agentscope.application.use_cases.chat_about_mapping import ChatAboutMapping, ChatResult
from agentscope.infrastructure.llm.fake_provider import FakeLLMProvider


def _proposal(ambiguities: list[str]) -> MappingProposal:
    return MappingProposal(
        definition={"source_format": "jsonl", "entities": {}},
        explanations=[],
        ambiguities=ambiguities,
        unmapped_fields=[],
    )


class _StubChatProvider:
    """Rejoue une suite de réponses fixées à l'avance, un tour après l'autre."""

    name = "stub-chat"

    def __init__(self, replies: list[ChatReply]) -> None:
        self._replies = list(replies)
        self.seen_contexts: list = []

    def propose_mapping(self, profile, sample, target_schema):
        raise NotImplementedError

    def chat(self, conversation_id, messages, context):
        self.seen_contexts.append(context)
        return self._replies.pop(0)


def test_no_db_dependency_can_be_injected() -> None:
    """Garantie structurelle : le constructeur n'accepte qu'un LLMProvider."""
    params = inspect.signature(ChatAboutMapping.__init__).parameters
    assert set(params) == {"self", "llm_provider"}


def test_execute_returns_text_and_keeps_ambiguities_without_revision() -> None:
    provider = _StubChatProvider([ChatReply(text="Voici pourquoi.", revised_proposal=None)])
    use_case = ChatAboutMapping(llm_provider=provider)
    proposal = _proposal(ambiguities=["champ `agent` ambigu entre agent_name et model_name"])

    result = use_case.execute(
        conversation_id="conv-1",
        messages=[ChatMessage(role="user", text="pourquoi ce mapping ?")],
        current_proposal=proposal,
    )

    assert isinstance(result, ChatResult)
    assert result.text == "Voici pourquoi."
    assert result.current_proposal is proposal
    assert result.ambiguities == ["champ `agent` ambigu entre agent_name et model_name"]


def test_execute_carries_the_revised_proposal_across_turns() -> None:
    """Échange multi-tours : la révision du tour 1 sert de base au tour 2."""
    revised = _proposal(ambiguities=[])
    provider = _StubChatProvider(
        [
            ChatReply(text="Je corrige.", revised_proposal=revised),
            ChatReply(text="Confirmé.", revised_proposal=None),
        ]
    )
    use_case = ChatAboutMapping(llm_provider=provider)
    original = _proposal(ambiguities=["ambiguïté initiale"])

    turn_1 = use_case.execute(
        conversation_id="conv-1",
        messages=[ChatMessage(role="user", text="corrige le champ X")],
        current_proposal=original,
    )
    assert turn_1.current_proposal is revised
    assert turn_1.ambiguities == []

    turn_2 = use_case.execute(
        conversation_id="conv-1",
        messages=[ChatMessage(role="user", text="c'est bon ?")],
        current_proposal=turn_1.current_proposal,
    )

    assert turn_2.current_proposal is revised
    assert provider.seen_contexts[1].proposal is revised


def test_execute_works_with_the_real_fake_provider() -> None:
    use_case = ChatAboutMapping(llm_provider=FakeLLMProvider())
    proposal = _proposal(ambiguities=[])

    result = use_case.execute(
        conversation_id="conv-1",
        messages=[ChatMessage(role="user", text="explique-moi ce mapping")],
        current_proposal=proposal,
    )

    assert isinstance(result, ChatResult)
    assert result.current_proposal is proposal  # FakeLLMProvider ne révise jamais
