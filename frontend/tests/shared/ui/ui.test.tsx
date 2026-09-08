import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ApiError } from '@shared/api/api-error';
import { Button, Card, CardHeader, CardTitle, EmptyState, ErrorState, Spinner } from '@shared/ui';

describe('Button', () => {
  it('defaults to type=button and primary variant', () => {
    render(<Button>Go</Button>);
    const btn = screen.getByRole('button', { name: 'Go' });
    expect(btn).toHaveAttribute('type', 'button');
    expect(btn.className).toContain('bg-primary');
  });

  it('applies variant + size + custom class and forwards clicks', () => {
    const onClick = vi.fn();
    render(
      <Button variant="danger" size="sm" className="mt-3" onClick={onClick}>
        X
      </Button>,
    );
    const btn = screen.getByRole('button', { name: 'X' });
    expect(btn.className).toContain('bg-danger');
    expect(btn.className).toContain('h-8');
    expect(btn.className).toContain('mt-3');
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalledOnce();
  });
});

describe('Card', () => {
  it('renders card, header and title', () => {
    render(
      <Card data-testid="c">
        <CardHeader>
          <CardTitle>Titre</CardTitle>
        </CardHeader>
      </Card>,
    );
    expect(screen.getByTestId('c').className).toContain('rounded-card');
    expect(screen.getByRole('heading', { name: 'Titre' })).toBeInTheDocument();
  });
});

describe('EmptyState', () => {
  it('uses the default title', () => {
    render(<EmptyState />);
    expect(screen.getByText('Donnée non disponible')).toBeInTheDocument();
  });

  it('renders a custom title + description', () => {
    render(<EmptyState title="Rien" description="pour le moment" />);
    expect(screen.getByText('Rien')).toBeInTheDocument();
    expect(screen.getByText('pour le moment')).toBeInTheDocument();
  });
});

describe('Spinner', () => {
  it('exposes an accessible status role', () => {
    render(<Spinner />);
    expect(screen.getByRole('status', { name: 'Chargement' })).toBeInTheDocument();
  });
});

describe('ErrorState', () => {
  it('shows the ApiError problem detail', () => {
    const err = new ApiError({
      message: 'fallback',
      status: 500,
      kind: 'http',
      problem: { type: 'about:blank', title: 'T', status: 500, detail: 'détail serveur' },
    });
    render(<ErrorState error={err} />);
    expect(screen.getByText('détail serveur')).toBeInTheDocument();
  });

  it('falls back to an ApiError message when there is no detail', () => {
    const err = new ApiError({ message: 'plain message', status: 0, kind: 'network' });
    render(<ErrorState error={err} />);
    expect(screen.getByText('plain message')).toBeInTheDocument();
  });

  it('handles a generic Error and an unknown value, and wires retry', () => {
    const onRetry = vi.fn();
    const { rerender } = render(<ErrorState error={new Error('oops')} onRetry={onRetry} />);
    expect(screen.getByText('oops')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    expect(onRetry).toHaveBeenCalledOnce();

    rerender(<ErrorState error={'weird'} />);
    expect(screen.getByText('Une erreur inattendue est survenue.')).toBeInTheDocument();
  });
});
