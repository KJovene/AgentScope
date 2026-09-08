// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DashboardScreen } from "../../../src/features/dashboard/ui/DashboardScreen";
import { apiClient } from "../../../src/shared/api/client";

vi.mock("../../../src/shared/api/client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe("DashboardScreen UI (I5.1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("affiche les 4 cartes d'indicateurs avec les valeurs réelles", async () => {
    const mockMetrics = {
      session_count: 42,
      model_call_count: 120,
      tool_call_count: 80,
      error_count: 2,
      total_tokens: 154000,
      prompt_tokens: 100000,
      completion_tokens: 54000,
      cached_tokens: null,
      total_cost_usd: 1.25,
      error_rate: 0.016,
      cache_hit_ratio: null,
      median_session_duration_ms: 3200.0,
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockMetrics);

    render(<DashboardScreen />);

    await waitFor(() => {
      expect(screen.getByText("42")).toBeDefined();
      expect(screen.getByText(/154[\s\u00a0,]?000/)).toBeDefined();
      expect(screen.getByText("$1.25")).toBeDefined();
      expect(screen.getByText("1.6 %")).toBeDefined();
    });
  });

  it("affiche N/A et le tooltip de définition au survol", async () => {
    const mockMetricsNulls = {
      session_count: 10,
      model_call_count: 0,
      tool_call_count: 0,
      error_count: 0,
      total_tokens: null,
      prompt_tokens: null,
      completion_tokens: null,
      cached_tokens: null,
      total_cost_usd: null,
      error_rate: null,
      cache_hit_ratio: null,
      median_session_duration_ms: null,
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockMetricsNulls);

    render(<DashboardScreen />);

    await waitFor(() => {
      expect(screen.getByText("10")).toBeDefined();
      expect(screen.getAllByText("N/A").length).toBeGreaterThanOrEqual(3);
    });

    const infoBtn = screen.getByLabelText("Définition de Tokens consommés");
    fireEvent.mouseEnter(infoBtn);

    await waitFor(() => {
      expect(screen.getByRole("tooltip")).toBeDefined();
      expect(screen.getByText(/Non disponible si la source ne fournit pas/)).toBeDefined();
    });
  });
});
