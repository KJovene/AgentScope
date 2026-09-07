# Modèle de données

> Stub — à compléter dans les issues **I1.2 / I1.8** (WS-domain). Base dans `PLAN.md` §4 et §5.4.

À produire ici :

- Diagramme relationnel (mermaid `erDiagram`) : `source`, `import_batch`, `raw_record`,
  `repository`, `session`, `model_call`, `tool_call`, `mapping`, `import_reject`,
  `field_profile`.
- Pour **chaque table** : ce que représente une ligne, clés, contraintes d'unicité.
- Vues agrégées du dashboard : `v_session_metrics`, `v_daily_activity`, `v_tool_usage`,
  `v_data_quality`.
- Justification 3NF et exceptions assumées (colonnes JSON, valeurs dérivées).
- Traçabilité : lien de chaque enregistrement normalisé vers `raw_record` et `import_batch`.
- Idempotence : `file_sha256` + clé naturelle (ou `external_id` synthétisé).
- Vocabulaires contrôlés : `status`, `error_type`, `reason_code`.
