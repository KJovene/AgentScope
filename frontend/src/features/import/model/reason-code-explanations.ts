export const REASON_CODE_EXPLANATIONS: Record<
  string,
  { label: string; explanation: string; action: string }
> = {
  MISSING_FIELD: {
    label: "Champ requis manquant",
    explanation: "Un champ obligatoire défini par le schéma source est absent de l'enregistrement.",
    action: "Vérifiez que le fichier source contient toutes les colonnes requises.",
  },
  INVALID_DATETIME: {
    label: "Format de date invalide",
    explanation: "Le horodatage fourni ne respecte pas la norme ISO-8601 attendue.",
    action: "Reformatez les dates au format YYYY-MM-DDTHH:mm:ssZ.",
  },
  TYPE_MISMATCH: {
    label: "Incompatibilité de type",
    explanation: "La valeur fournie ne correspond pas au type de donnée spécifié (ex. texte au lieu de nombre).",
    action: "Corrigez le type de la colonne dans la donnée brute.",
  },
  DUPLICATE_RECORD: {
    label: "Enregistrement en doublon",
    explanation: "Une trace identique avec le même identifiant externe existe déjà en base.",
    action: "Aucune action requise si l'ignorance des doublons est voulue.",
  },
  REJECTED_RECORD: {
    label: "Erreur de validation générale",
    explanation: "L'enregistrement n'a pas pu être normalisé selon les règles du mapping actif.",
    action: "Inspectez la donnée brute ci-dessous pour identifier l'anomalie.",
  },
};
