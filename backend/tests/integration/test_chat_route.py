"""I4.4 — route ``POST /chat`` branchée sur ``MappingWorkbenchService.chat``.

Vérifie le relais, la conversion des DTO, l'absence d'effet de bord DB, et le
comportement multi-tours (proposition révisée reportée par le client).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agentscope.application.ports.llm_provider import MappingProposal as PortProposal
from agentscope.application.use_cases.chat_about_mapping import ChatResult
from agentscope.infrastructure.config.settings import Settings
from agentscope.interfaces.api.app import create_app
from agentscope.interfaces.api.dependencies import get_workbench_service

_DEFINITION = {"source_format": "jsonl", "entities": {}}
_PROPOSAL_PAYLOAD = {
    "definition": _DEFINITION,
    "explanations": [
        {
            "target_field": "session.external_id",
            "source_field": "session_id",
            "rationale": "clé",
            "confidence": 0.8,
        }
    ],
    "ambiguities": ["`agent` ambigu"],
    "unmapped_fields": ["debug"],
}


class StubWorkbench:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def analyze(self, *a, **k):  # pragma: no cover
        raise NotImplementedError

    def preview(self, *a, **k):  # pragma: no cover
        raise NotImplementedError

    def chat(self, conversation_id, messages, current_proposal) -> ChatResult:
        self.calls.append((conversation_id, tuple(m.role for m in messages)))
        # Révise en vidant les ambiguïtés.
        revised = PortProposal(
            definition=current_proposal.definition,
            explanations=current_proposal.explanations,
            ambiguities=[],
            unmapped_fields=current_proposal.unmapped_fields,
        )
        return ChatResult(
            text=f"{len(messages)} message(s) reçu(s).",
            current_proposal=revised,
            revised_proposal=revised,
        )


@pytest.fixture
def stub() -> StubWorkbench:
    return StubWorkbench()


@pytest.fixture
def client(stub: StubWorkbench):
    app = create_app()
    app.dependency_overrides[get_workbench_service] = lambda: stub
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_chat_relays_and_returns_reply_with_current_proposal(
    client: TestClient, stub: StubWorkbench
) -> None:
    resp = client.post(
        "/api/v1/chat",
        json={
            "conversation_id": "conv-1",
            "messages": [{"role": "user", "text": "pourquoi ce mapping ?"}],
            "current_proposal": _PROPOSAL_PAYLOAD,
            "file_ref": "profile-42",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["text"] == "1 message(s) reçu(s)."
    assert body["revised_proposal"]["ambiguities"] == []
    assert body["current_proposal"]["ambiguities"] == []
    assert body["current_proposal"]["definition"] == _DEFINITION
    assert stub.calls == [("conv-1", ("user",))]


def test_chat_requires_messages_and_a_proposal(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/chat",
        json={"conversation_id": "c", "message": "hello", "file_ref": "x"},
    )
    assert resp.status_code == 422


def test_chat_with_real_container_and_fake_provider_returns_200() -> None:
    """FakeLLMProvider.chat renvoie une réponse valide sans révision."""
    app = create_app(Settings(llm_provider="fake"))
    with TestClient(app) as c:
        resp = c.post(
            "/api/v1/chat",
            json={
                "conversation_id": "conv-1",
                "messages": [{"role": "user", "text": "explique"}],
                "current_proposal": _PROPOSAL_PAYLOAD,
            },
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body["text"], str) and body["text"]
    assert body["revised_proposal"] is None
    assert body["current_proposal"]["definition"] == _DEFINITION
