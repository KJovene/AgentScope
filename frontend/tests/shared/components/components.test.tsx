import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ApiErrorBanner } from '@shared/components/ApiErrorBanner';
import { MetricCard } from '@shared/components/MetricCard';
import { PageHeader } from '@shared/components/PageHeader';
import { UNAVAILABLE } from '@shared/lib/format';

describe('ApiErrorBanner', () => {
  it('renders nothing when there is no error', () => {
    const { container } = render(<ApiErrorBanner error={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders title, detail and field errors, and calls onDismiss', () => {
    const onDismiss = vi.fn();
    render(
      <ApiErrorBanner
        error={{
          title: 'Échec',
          status: 422,
          detail: 'des champs sont invalides',
          errors: [{ field: 'name', message: 'requis' }],
        }}
        onDismiss={onDismiss}
      />,
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Échec')).toBeInTheDocument();
    expect(screen.getByText('des champs sont invalides')).toBeInTheDocument();
    expect(screen.getByText(/requis/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Fermer' }));
    expect(onDismiss).toHaveBeenCalledOnce();
  });

  it('omits the dismiss button when no handler is given', () => {
    render(<ApiErrorBanner error={{ title: 'x', status: 500 }} />);
    expect(screen.queryByRole('button', { name: 'Fermer' })).not.toBeInTheDocument();
  });
});

describe('MetricCard', () => {
  it('renders a value and an optional hint', () => {
    render(<MetricCard label="Sessions" value="128" hint="7 derniers jours" />);
    expect(screen.getByText('Sessions')).toBeInTheDocument();
    expect(screen.getByText('128')).toBeInTheDocument();
    expect(screen.getByText('7 derniers jours')).toBeInTheDocument();
  });

  it('styles an unavailable value as muted', () => {
    render(<MetricCard label="Coût" value={UNAVAILABLE} />);
    expect(screen.getByText(UNAVAILABLE).className).toContain('text-foreground-muted');
  });

  it('links to the indicator definition when definitionId is set', () => {
    render(<MetricCard label="Sessions" value="1" definitionId="sessions" />);
    const link = screen.getByRole('link', { name: 'Définition de Sessions' });
    expect(link).toHaveAttribute('href', '/docs/data/indicators.md#sessions');
  });
});

describe('PageHeader', () => {
  it('renders the title only', () => {
    render(<PageHeader title="Dashboard" />);
    expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument();
  });

  it('renders description and actions when provided', () => {
    render(
      <PageHeader title="T" description="desc" actions={<button type="button">act</button>} />,
    );
    expect(screen.getByText('desc')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'act' })).toBeInTheDocument();
  });
});
