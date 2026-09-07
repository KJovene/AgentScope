import { ApiError } from '@shared/api/api-error';

import { Button } from './Button';

/** Uniform rendering for any failed query/mutation. Accepts the app's ApiError. */
export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message =
    error instanceof ApiError
      ? (error.problem?.detail ?? error.message)
      : error instanceof Error
        ? error.message
        : 'Une erreur inattendue est survenue.';

  return (
    <div className="rounded-card border border-danger/40 bg-danger/5 p-4 text-sm">
      <p className="font-medium text-danger">Erreur</p>
      <p className="mt-1 text-foreground-muted">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-3" onClick={onRetry}>
          Réessayer
        </Button>
      )}
    </div>
  );
}
