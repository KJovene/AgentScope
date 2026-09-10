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
  modelCalls: {
    label: "Appels modèles",
    calculation: "COUNT(model_call)",
    unit: "Appels",
    scope: "Tous les appels modèles du périmètre filtré",
    nullMeaning: "Jamais NULL (0 par défaut)",
  },
  toolCalls: {
    label: "Appels outils",
    calculation: "COUNT(tool_call)",
    unit: "Appels",
    scope: "Tous les appels d'outils du périmètre filtré",
    nullMeaning: "Jamais NULL (0 par défaut)",
  },
  medianDuration: {
    label: "Durée médiane",
    calculation: "MEDIAN(ended_at - started_at) par session",
    unit: "Durée",
    scope: "Sessions disposant d'un horodatage de début et de fin",
    nullMeaning: "Aucune session horodatée dans le périmètre filtré",
  },
  cacheHit: {
    label: "Taux de cache",
    calculation: "(cached_tokens / prompt_tokens) * 100",
    unit: "%",
    scope: "Appels modèles dont la source remonte les tokens mis en cache",
    nullMeaning: "La source ne fournit pas le décompte de tokens mis en cache",
  },
};
