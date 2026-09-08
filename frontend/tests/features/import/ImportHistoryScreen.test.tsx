// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ImportHistoryScreen } from "../../../src/features/import/ui/ImportHistoryScreen";
import { apiClient } from "../../../src/shared/api/client";

vi.mock("../../../src/shared/api/client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe("ImportHistoryScreen UI (I5.3)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("affiche la liste des imports récents", async () => {
    const mockImports = {
      items: [
        {
          id: "batch-001",
          source_id: "src-tracelab",
          mapping_id: "tracelab-jsonl",
          status: "completed",
          imported_count: 100,
          duplicate_count: 2,
          rejected_count: 0,
          missing_info_count: 0,
          imported_at: "2026-09-08T09:00:00Z",
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockImports);

    render(<ImportHistoryScreen />);

    await waitFor(() => {
      expect(screen.getByText("batch-001")).toBeDefined();
      expect(screen.getByText("Réussi")).toBeDefined();
    });
  });

  it("affiche le détail du bilan et les rejets au clic sur un lot", async () => {
    const mockImports = {
      items: [
        {
          id: "batch-002",
          source_id: "src-tracelab",
          mapping_id: "tracelab-jsonl",
          status: "partial",
          imported_count: 50,
          duplicate_count: 1,
          rejected_count: 1,
          missing_info_count: 0,
          imported_at: "2026-09-08T09:30:00Z",
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    };

    const mockRejects = {
      items: [
        {
          record_index: 4,
          reason_code: "MISSING_FIELD",
          reason_detail: "Champ session_id manquant",
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockImports);
    vi.mocked(apiClient.get).mockResolvedValueOnce(mockRejects);

    render(<ImportHistoryScreen />);

    await waitFor(() => {
      expect(screen.getByText("batch-002")).toBeDefined();
    });

    fireEvent.click(screen.getByText("batch-002"));

    await waitFor(() => {
      expect(screen.getByText("Bilan : batch-002")).toBeDefined();
      expect(screen.getByText("Champ session_id manquant")).toBeDefined();
    });
  });
});
