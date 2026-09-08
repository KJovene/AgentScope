// @vitest-environment jsdom
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, it, expect } from "vitest";

import { metricFiltersSchema } from "@shared/lib/metric-filters";
import { DashboardScreen } from "../../../src/features/dashboard/ui/DashboardScreen";
import { server } from "../../msw/server";
import { renderRouted } from "../../utils";

const INDICATORS = {
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

const INDICATORS_ALL_NULL = {
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

function renderDashboard() {
  return renderRouted(<DashboardScreen />, { validateSearch: metricFiltersSchema });
}

describe("DashboardScreen UI (I5.1 / I5.10)", () => {
  it("affiche les 4 cartes d'indicateurs avec les valeurs réelles", async () => {
    server.use(http.get("/api/metrics/indicators", () => HttpResponse.json(INDICATORS)));

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("42")).toBeDefined();
      expect(screen.getByText(/154[\s\u00a0,]?000/)).toBeDefined();
      expect(screen.getByText("$1.25")).toBeDefined();
      expect(screen.getByText("1.6 %")).toBeDefined();
    });
  });

  it("affiche N/A et le tooltip de définition au survol", async () => {
    server.use(http.get("/api/metrics/indicators", () => HttpResponse.json(INDICATORS_ALL_NULL)));

    renderDashboard();

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

  it("affiche un état vide quand l'activité n'a aucun point", async () => {
    server.use(
      http.get("/api/metrics/indicators", () => HttpResponse.json(INDICATORS)),
      http.get("/api/metrics/timeseries", () =>
        HttpResponse.json({ metric: "sessions", granularity: "day", points: [] }),
      ),
      http.get("/api/metrics/tool-usage", () => HttpResponse.json([])),
      http.get("/api/sessions", () =>
        HttpResponse.json({ items: [], total: 0, limit: 200, offset: 0 }),
      ),
    );

    renderDashboard();

    await waitFor(() => {
      // Le graphe d'activité, la répartition des outils ET la distribution
      // des durées sont vides.
      expect(screen.getAllByText("Aucune donnée disponible")).toHaveLength(3);
    });
  });

  it("recharge la série temporelle quand on bascule Sessions/Tokens", async () => {
    server.use(
      http.get("/api/metrics/indicators", () => HttpResponse.json(INDICATORS)),
      http.get("/api/metrics/timeseries", ({ request }) => {
        const metric = new URL(request.url).searchParams.get("metric");
        return HttpResponse.json({
          metric,
          granularity: "day",
          points: [{ period: "2026-01-01", value: metric === "tokens" ? 999 : 3 }],
        });
      }),
    );

    renderDashboard();

    await waitFor(() => expect(screen.getByText("Activité")).toBeDefined());

    const tokensButton = await screen.findByRole("button", { name: "Tokens" });
    fireEvent.click(tokensButton);

    await waitFor(() => {
      expect(tokensButton.getAttribute("aria-pressed")).toBe("true");
    });
  });

  it("affiche la répartition des outils", async () => {
    server.use(
      http.get("/api/metrics/indicators", () => HttpResponse.json(INDICATORS)),
      http.get("/api/metrics/tool-usage", () =>
        HttpResponse.json([
          { tool_name: "bash", n_calls: 10, n_errors: 2, avg_duration_ms: 120 },
        ]),
      ),
    );

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Répartition des outils")).toBeDefined();
    });
  });

  it("affiche la distribution de la durée des sessions et signale celles sans horodatage", async () => {
    server.use(
      http.get("/api/metrics/indicators", () => HttpResponse.json(INDICATORS)),
      http.get("/api/sessions", () =>
        HttpResponse.json({
          items: [
            { session_id: 1, source_name: "s", agent_name: "a", duration_ms: 1000, model_call_count: 1, tool_call_count: 0, error_count: 0 },
            { session_id: 2, source_name: "s", agent_name: "a", duration_ms: null, model_call_count: 1, tool_call_count: 0, error_count: 0 },
          ],
          total: 2,
          limit: 200,
          offset: 0,
        }),
      ),
    );

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Distribution de la durée des sessions")).toBeDefined();
      expect(
        screen.getByText("1 session(s) sans horodatage, exclue(s) de la distribution."),
      ).toBeDefined();
    });
  });
});
