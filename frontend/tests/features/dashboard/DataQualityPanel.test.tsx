// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { DataQualityPanel } from "@features/dashboard/ui/DataQualityPanel";
import type { DataQualityMetrics } from "@features/dashboard/types";

describe("DataQualityPanel UI (I5.8)", () => {
  const mockMetrics: DataQualityMetrics = {
    globalCompleteness: 85.5,
    globalRejectionRate: 4.2,
    sources: [
      {
        id: "src-1",
        sourceName: "Export_CRM_2026.csv",
        totalRows: 1000,
        validRows: 950,
        rejectedRows: 50,
        completeness: 92.0,
        missingFields: [
          { field: "num_telephone", emptyCount: 150, percentage: 15.0 },
        ],
      },
      {
        id: "src-2",
        sourceName: "API_Facturation",
        totalRows: 500,
        validRows: 300,
        rejectedRows: 200,
        completeness: 65.4,
        missingFields: [
          { field: "adresse_livraison", emptyCount: 200, percentage: 40.0 },
          { field: "code_postal", emptyCount: 180, percentage: 36.0 },
        ],
      }
    ],
  };

  it("affiche correctement les métriques globales", () => {
    render(<DataQualityPanel metrics={mockMetrics} />);

    expect(screen.getByText("85.5%")).toBeDefined(); // Complétude globale
    expect(screen.getByText("4.2%")).toBeDefined(); // Taux de rejet
  });

  it("affiche les cartes des sources avec leurs statistiques", () => {
    render(<DataQualityPanel metrics={mockMetrics} />);

    // Source 1
    expect(screen.getByText("Export_CRM_2026.csv")).toBeDefined();
    expect(screen.getByText("92.0% complet")).toBeDefined();
    expect(screen.getByText("950")).toBeDefined(); // valides
    expect(screen.getByText("⚠️ num_telephone")).toBeDefined();

    // Source 2 (Mauvaise qualité)
    expect(screen.getByText("API_Facturation")).toBeDefined();
    expect(screen.getByText("65.4% complet")).toBeDefined();
    expect(screen.getByText("200")).toBeDefined(); // rejets
    expect(screen.getByText("⚠️ adresse_livraison")).toBeDefined();
    expect(screen.getByText(/40.0% vide/)).toBeDefined();
  });

  it("affiche un message si aucune source n'est fournie", () => {
    render(
      <DataQualityPanel
        metrics={{ globalCompleteness: 0, globalRejectionRate: 0, sources: [] }}
      />
    );
    expect(screen.getByText("Aucune source de données analysée pour le moment.")).toBeDefined();
  });
});
