// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ChatScreen } from "../../../src/features/chat/ui/ChatScreen";
import { apiClient } from "../../../src/shared/api/client";

vi.mock("../../../src/shared/api/client", () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

// Mock pour ignorer l'absence d'implémentation de scrollIntoView dans jsdom
window.HTMLElement.prototype.scrollIntoView = vi.fn();

describe("ChatScreen UI (I5.5)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("affiche l'historique initial et permet d'envoyer un message", async () => {
    render(<ChatScreen sessionId="test-session" />);

    // Vérification du message de bienvenue initial
    expect(screen.getByText(/Bonjour ! Je suis l'agent AgentScope/i)).toBeDefined();

    const input = screen.getByPlaceholderText("Posez votre question à l'agent...");
    const sendButton = screen.getByRole("button", { name: "Envoyer" });

    // Mock de la réponse de l'agent sans ambiguïté
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      id: "msg-002",
      role: "agent",
      content: "Je peux vous aider à formater ces données.",
      created_at: new Date().toISOString(),
    });

    fireEvent.change(input, { target: { value: "Peux-tu vérifier mon dernier import ?" } });
    fireEvent.click(sendButton);

    // Vérification de l'affichage optimiste du message utilisateur
    expect(screen.getByText("Peux-tu vérifier mon dernier import ?")).toBeDefined();

    // Vérification de la réponse de l'agent
    await waitFor(() => {
      expect(screen.getByText("Je peux vous aider à formater ces données.")).toBeDefined();
    });
  });

  it("met en évidence les ambiguïtés signalées par l'agent", async () => {
    render(<ChatScreen sessionId="test-session" />);

    const input = screen.getByPlaceholderText("Posez votre question à l'agent...");
    const sendButton = screen.getByRole("button", { name: "Envoyer" });

    // Mock d'une réponse nécessitant des clarifications
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      id: "msg-003",
      role: "agent",
      content: "J'ai trouvé plusieurs imports correspondants.",
      created_at: new Date().toISOString(),
      ambiguity_alerts: [
        "Parlez-vous de l'import Tracelab ou CRM ?",
        "Sur quelle plage de date ?",
      ],
    });

    fireEvent.change(input, { target: { value: "Montre moi l'import" } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText("J'ai trouvé plusieurs imports correspondants.")).toBeDefined();

      // Vérification des blocs d'alerte d'ambiguïté
      expect(screen.getByText("Précision requise")).toBeDefined();
      expect(screen.getByText("Parlez-vous de l'import Tracelab ou CRM ?")).toBeDefined();
      expect(screen.getByText("Sur quelle plage de date ?")).toBeDefined();
    });
  });
});
