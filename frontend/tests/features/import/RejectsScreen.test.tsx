// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { RejectsScreen } from "../../../src/features/import/ui/RejectsScreen";
import { apiClient } from "../../../src/shared/api/client";

vi.mock("../../../src/shared/api/client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe("RejectsScreen UI (I5.4)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("affiche la liste des rejets avec la qualification du reason_code", async () => {
    const mockRejects = {
      items: [
        {
          record_index: 12,
          reason_code: "MISSING_FIELD",
          reason_detail: "Champ session_id absent",
          payload: { raw_line: "invalid json string" },
        },
      ],
      total: 1,
      limit: 100,
      offset: 0,
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockRejects);

    render(<RejectsScreen importId="batch-123" />);

    await waitFor(() => {
      expect(screen.getByText("MISSING_FIELD")).toBeDefined();
      expect(screen.getByText("Champ session_id absent")).toBeDefined();
    });
  });

  it("ouvre le panneau d'explication lisible au clic sur 'Inspecter'", async () => {
    const mockRejects = {
      items: [
        {
          record_index: 12,
          reason_code: "INVALID_DATETIME",
          reason_detail: "Format date invalide '2026-13-45'",
          payload: { date: "2026-13-45" },
        },
      ],
      total: 1,
      limit: 100,
      offset: 0,
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockRejects);

    render(<RejectsScreen importId="batch-123" />);

    await waitFor(() => {
      expect(screen.getByText("INVALID_DATETIME")).toBeDefined();
    });

    fireEvent.click(screen.getByText("Inspecter"));

    await waitFor(() => {
      expect(screen.getByText("Format de date invalide")).toBeDefined();
      expect(screen.getByText(/ISO-8601/)).toBeDefined();
    });
  });
});
