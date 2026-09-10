// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SessionTimeline } from "../../../src/features/session-detail/ui/SessionDetailPage";
import type { SessionDetails } from "../../../src/features/session-detail/types";

describe("SessionTimeline UI", () => {
  const mockSession: SessionDetails = {
    id: "sess-123",
    status: "completed",
    createdAt: "2026-09-10T09:00:00Z",
    totalTokens: 1542,
    totalCost: 0.0345,
    events: [
      {
        id: "evt-1",
        timestamp: "2026-09-10T09:00:05Z",
        type: "model_call",
        model: "gpt-4",
        promptSummary: "Trouver la source des données...",
        responseSummary: "J'utilise l'outil de recherche...",
        tokens: { prompt: 100, completion: 50, total: 150 },
        cost: 0.0045,
      },
      {
        id: "evt-2",
        timestamp: "2026-09-10T09:00:10Z",
        type: "tool_call",
        toolName: "fetch_schema",
        arguments: { table: "users" },
        result: "Colonnes: id, email, created_at",
        provenanceLink: "https://schema-registry.local/users",
      },
      {
        id: "evt-3",
        timestamp: "2026-09-10T09:00:15Z",
        type: "error",
        errorMessage: "Timeout lors de la connexion à la base de données",
        step: "Extraction cible",
      }
    ],
  };

  it("affiche l'en-tête et les totaux de la session", () => {
    render(<SessionTimeline session={mockSession} />);

    expect(screen.getByText(/Session ID: sess-123/i)).toBeDefined();
    expect(screen.getByText("1542")).toBeDefined(); // Tokens
    expect(screen.getByText("$0.0345")).toBeDefined(); // Cost
  });

  it("affiche chronologiquement les événements (LLM, Outils, Erreurs)", () => {
    render(<SessionTimeline session={mockSession} />);

    // LLM Call
    expect(screen.getByText("🤖 Appel LLM (gpt-4)")).toBeDefined();
    expect(screen.getByText(/Trouver la source/i)).toBeDefined();

    // Tool Call
    expect(screen.getByText("🛠️ Exécution Outil: fetch_schema")).toBeDefined();
    expect(screen.getByText(/Colonnes: id/i)).toBeDefined();

    // Provencance Link
    const link = screen.getByRole("link", { name: /Lien provenance/i });
    expect(link.getAttribute("href")).toBe("https://schema-registry.local/users");

    // Error
    expect(screen.getByText("❌ Erreur")).toBeDefined();
    expect(screen.getByText("Timeout lors de la connexion à la base de données")).toBeDefined();
  });
});
