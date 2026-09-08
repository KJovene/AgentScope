// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MappingEditor } from "@features/mapping-agent";
import type { MappingRow } from "@features/mapping-agent";

describe("MappingEditor UI (I5.6)", () => {
  const mockSources = ["col_a", "col_b", "col_c"];
  const mockTargets = ["id", "email", "created_at"];
  const initialRows: MappingRow[] = [
    { id: "1", sourceField: "col_a", targetField: "id", transform: "none" },
    { id: "2", sourceField: "col_b", targetField: "email", transform: "trim" },
  ];

  it("affiche la table avec les données initiales", () => {
    render(
      <MappingEditor
        initialRows={initialRows}
        availableSourceFields={mockSources}
        availableTargetFields={mockTargets}
      />
    );

    expect(screen.getByDisplayValue("col_a")).toBeDefined();
    expect(screen.getByDisplayValue("email")).toBeDefined();
    expect(screen.getByText("✅ Toutes les correspondances sont valides.")).toBeDefined();
  });

it("détecte en direct un doublon de champ cible", () => {
    render(
      <MappingEditor
        initialRows={initialRows}
        availableSourceFields={mockSources}
        availableTargetFields={mockTargets}
      />
    );

    const selects = screen.getAllByRole("combobox");

    // Assigner "id" au champ cible de la 2ème ligne (index 4)
    fireEvent.change(selects[4]!, { target: { value: "id" } });

    // Utilisation de getAllByText car il y a 2 messages d'erreur dans le DOM
    const duplicateErrors = screen.getAllByText(/assigné plusieurs fois/i);
    expect(duplicateErrors.length).toBeGreaterThan(0);

    // Vérification que le bouton de sauvegarde reste désactivé
    expect(screen.getByRole("button", { name: "Enregistrer le mapping" })).toBeDisabled();
  });

  it("valide la présence des champs cibles requis", () => {
    render(
      <MappingEditor
        initialRows={initialRows}
        availableSourceFields={mockSources}
        availableTargetFields={mockTargets}
        requiredTargetFields={["created_at"]}
      />
    );

    expect(
      screen.getByText(/Le champ requis « created_at » n'est pas associé/i)
    ).toBeDefined();
    expect(screen.getByRole("button", { name: "Enregistrer le mapping" })).toBeDisabled();
  });

  it("permet d'ajouter une ligne et d'enregistrer après correction", () => {
    const handleSave = vi.fn();

    render(
      <MappingEditor
        initialRows={initialRows}
        availableSourceFields={mockSources}
        availableTargetFields={mockTargets}
        requiredTargetFields={["created_at"]}
        onSave={handleSave}
      />
    );

    // Ajouter une ligne
    fireEvent.click(screen.getByRole("button", { name: "+ Ajouter un champ" }));

    const selects = screen.getAllByRole("combobox");
    // Sélectionner 'created_at' sur la nouvelle ligne (dernier select de cible)
    const lastTargetSelect = selects[selects.length - 2];
    fireEvent.change(lastTargetSelect!, { target: { value: "created_at" } });

    // Le formulaire repasse au vert
    expect(screen.getByText("✅ Toutes les correspondances sont valides.")).toBeDefined();

    const saveBtn = screen.getByRole("button", { name: "Enregistrer le mapping" });
    expect(saveBtn).not.toBeDisabled();
    fireEvent.click(saveBtn);

    expect(handleSave).toHaveBeenCalledTimes(1);
  });
});
