export interface IndicatorsResponse {
  session_count: number;
  model_call_count: number;
  tool_call_count: number;
  error_count: number;
  total_tokens: number | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  cached_tokens: number | null;
  total_cost_usd: number | null;
  error_rate: number | null;
  cache_hit_ratio: number | null;
  median_session_duration_ms: number | null;
}

export interface MetricDefinition {
  label: string;
  calculation: string;
  unit: string;
  scope: string;
  nullMeaning: string;
}

export const METRIC_DEFINITIONS: Record<string, MetricDefinition> = {
  sessions: {
    label: "Sessions totales",
    calculation: "COUNT(DISTINCT session_id)",
    unit: "Sessions",
    scope: "Toutes les sessions correspondant aux filtres actifs",
    nullMeaning: "Jamais NULL (0 par défaut)",
  },
  tokens: {
    label: "Tokens consommés",
    calculation: "SUM(prompt_tokens + completion_tokens)",
    unit: "Tokens",
    scope: "Appels modèles valides du périmètre",
    nullMeaning: "Non disponible si la source ne fournit pas le décompte de tokens",
  },
  cost: {
    label: "Coût estimé",
    calculation: "SUM(cost_usd) calculé selon la grille tarifaire modèle",
    unit: "USD ($)",
    scope: "Appels modèles avec modèle identifié",
    nullMeaning: "Non disponible si le modèle est inconnu ou sans tarif renseigné",
  },
  errorRate: {
    label: "Taux d'erreur",
    calculation: "(COUNT(erreurs) / COUNT(appels totaux)) * 100",
    unit: "%",
    scope: "Ensemble des appels modèles et outils",
    nullMeaning: "Aucun appel enregistré dans la période sélectionnée",
  },
};
