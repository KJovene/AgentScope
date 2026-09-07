import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Layout } from "./App"

describe("Layout & Navigation UI (I5.1)", () => {
  it("affiche la navigation latérale et bascule entre les zones", () => {
    render(<Layout />);

    expect(screen.getByText("AgentScope")).toBeDefined();
    expect(screen.getByRole("navigation")).toBeDefined();

    const importTab = screen.getByText("Imports & Ingestion");
    fireEvent.click(importTab);

    expect(screen.getByText(/Zone active :/i)).toBeDefined();
    expect(screen.getByText("imports")).toBeDefined();
  });

  it("affiche les erreurs API via la bannière dédiée", () => {
    const errorSample = {
      title: "Échec de l'importation",
      status: 400,
      detail: "Le fichier transmis est corrompu.",
    };

    render(
      <Layout>
        {({ setError }: { setError: (error: { title: string; status: number; detail: string }) => void }) => (
          <button onClick={() => setError(errorSample)}>Déclencher erreur</button>
        )}
      </Layout>
    );

    fireEvent.click(screen.getByText("Déclencher erreur"));

    expect(screen.getByRole("alert")).toBeDefined();
    expect(screen.getByText("Échec de l'importation")).toBeDefined();
    expect(screen.getByText("Le fichier transmis est corrompu.")).toBeDefined();
  });
});
