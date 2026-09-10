import React from 'react';
import type { ProblemDetails } from "../api/types";

interface ApiErrorBannerProps {
  error: ProblemDetails | null;
  onDismiss?: () => void;
}

export const ApiErrorBanner: React.FC<ApiErrorBannerProps> = ({ error, onDismiss }) => {
  if (!error) return null;

  return (
    <div
      role="alert"
      className="mb-4 border border-danger/60 bg-danger/10 p-4 text-foreground"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold uppercase tracking-wider text-danger">{error.title}</h3>
          {error.detail && <p className="mt-1 text-sm">{error.detail}</p>}
          {error.errors && error.errors.length > 0 && (
            <ul className="mt-2 list-disc pl-5 text-xs">
              {error.errors.map((err, idx) => (
                <li key={idx}>
                  <strong>{err.field} :</strong> {err.message}
                </li>
              ))}
            </ul>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 text-sm font-bold text-foreground-muted hover:text-danger"
            aria-label="Fermer"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};
