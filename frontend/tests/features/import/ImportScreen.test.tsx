import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ImportScreen } from "../../../src/features/import/ui/ImportScreen";
import { apiClient } from "../../../src/shared/api/client";

vi.mock("../../shared/api/client", () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

describe("ImportScreen UI (I5.2)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("affiche le formulaire de sélection de fichiers et désactive le bouton si aucun fichier n'est sélectionné", () => {
    render(<ImportScreen />);

    expect(screen.getByText("Importer des traces")).toBeDefined();
    const submitBtn = screen.getByRole("button", { name: "Lancer l'import" }) as HTMLButtonElement;
    expect(submitBtn.disabled).toBe(true);
  });

  it("permet de sélectionner un fichier, prévisualiser son nom et activer l'envoi", async () => {
    render(<ImportScreen />);

const input = screen.getByLabelText(/fichiers sources/i) as HTMLInputElement;
    const file = new File(['{"session_id": "s1"}'], "trace.jsonl", { type: "application/json" });

    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText("trace.jsonl")).toBeDefined();

    const submitBtn = screen.getByRole("button", { name: "Lancer l'import" }) as HTMLButtonElement;
    expect(submitBtn.disabled).toBe(false);
  });

  it("envoie le formulaire et affiche le bilan retourné par l'API", async () => {
    const mockReport = {
      id: "imp-123",
      mapping_id: "tracelab-jsonl",
      status: "completed",
      imported_count: 10,
      duplicate_count: 2,
      rejected_count: 1,
      missing_info_count: 0,
      imported_at: "2026-09-08T10:00:00Z",
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockReport);

    render(<ImportScreen />);

    const input = screen.getByLabelText(/fichiers sources/i, { selector: "input" }) as HTMLInputElement;
    const file = new File(['{"session_id": "s1"}'], "trace.jsonl", { type: "application/json" });
    fireEvent.change(input, { target: { files: [file] } });

    const submitBtn = screen.getByRole("button", { name: "Lancer l'import" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith("/imports", expect.any(FormData));
      expect(screen.getByText("Bilan de l'importation")).toBeDefined();
      expect(screen.getByText("10")).toBeDefined();
      expect(screen.getByText("2")).toBeDefined();
      expect(screen.getByText("1")).toBeDefined();
    });
  });
});
