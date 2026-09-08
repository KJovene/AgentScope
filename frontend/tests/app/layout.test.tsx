import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { Layout } from '@app/Layout';

describe('Layout & Navigation UI (I5.1)', () => {
  it('affiche la navigation latérale et bascule entre les zones', () => {
    render(<Layout />);

    expect(screen.getByText('AgentScope')).toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeInTheDocument();

    // Default active tab.
    expect(screen.getByText(/Zone active :/i)).toBeInTheDocument();
    expect(screen.getByText('dashboard')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Imports & Ingestion'));
    expect(screen.getByText('imports')).toBeInTheDocument();
  });

  it('rend le contenu fourni via la render-prop et expose setError', () => {
    render(
      <Layout>
        {({ activeTab, setError }) => (
          <button
            type="button"
            onClick={() =>
              setError({ title: "Échec de l'importation", status: 400, detail: 'Fichier corrompu.' })
            }
          >
            {`tab:${activeTab}`}
          </button>
        )}
      </Layout>,
    );

    fireEvent.click(screen.getByText('tab:dashboard'));
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText("Échec de l'importation")).toBeInTheDocument();
    expect(screen.getByText('Fichier corrompu.')).toBeInTheDocument();
  });

  it('efface l’erreur globale au changement d’onglet', () => {
    render(
      <Layout>
        {({ setError }) => (
          <button type="button" onClick={() => setError({ title: 'Boom', status: 500 })}>
            trigger
          </button>
        )}
      </Layout>,
    );
    fireEvent.click(screen.getByText('trigger'));
    expect(screen.getByRole('alert')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Tableau de bord'));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
