// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MappingPreview } from "@features/mapping-agent/ui/MappingPreview";
import type { DryRunResult } from "@features/mapping-agent/types";

describe("MappingPreview UI (I5.7 Dry-Run)", () => {
  const mockDryRunData: DryRunResult = {
    totalRows: 3,
    validRowsCount: 2,
    rejectedRowsCount: 1,
    rows: [
      {
        rowIndex: 1,
        sourceData: { raw_date: "2026-09-08" },
        transformedData: { created_at: "2026-09-08T00:00:00Z", status: "ACTIVE" },
        isValid: true,
      },
      {
        rowIndex: 2,
        sourceData: { raw_date: "2026-09-09" },
        transformedData: { created_at: "2026-09-09T00:00:00Z", status: "ACTIVE" },
        isValid: true,
      },
      {
        rowIndex: 3,
        sourceData: { raw_date: "invalid-date" },
        transformedData: { created_at: "INVALID", status: "PENDING" },
        isValid: false,
        rejectReason: "Format de date invalide pour ISO",
      },
    ],
  };

  it("affiche la synthèse et l'onglet des lignes valides par défaut", () => {
    render(
      <MappingPreview
        dryRunResult={mockDryRunData}
        onBackToEdit={vi.fn()}
        onConfirmImport={vi.fn()}
      />
    );

    expect(screen.getByText("2026-09-08T00:00:00Z")).toBeDefined();
    expect(screen.queryByText("Format de date invalide pour ISO")).toBeNull();
  });

  it("bascule sur l'onglet des rejets simulés", () => {
    render(
      <MappingPreview
        dryRunResult={mockDryRunData}
        onBackToEdit={vi.fn()}
        onConfirmImport={vi.fn()}
      />
    );

    const rejetsTab = screen.getByRole("button", { name: /Rejets simulés/i });
    fireEvent.click(rejetsTab);

    expect(screen.getByText("Format de date invalide pour ISO")).toBeDefined();
    expect(screen.getByText("#3")).toBeDefined();
  });

  it("déclenche les actions de retour et de validation", () => {
    const handleBack = vi.fn();
    const handleConfirm = vi.fn();

    render(
      <MappingPreview
        dryRunResult={mockDryRunData}
        onBackToEdit={handleBack}
        onConfirmImport={handleConfirm}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /← Modifier le mapping/i }));
    expect(handleBack).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: /Valider et lancer l'import/i }));
    expect(handleConfirm).toHaveBeenCalledTimes(1);
  });
});
