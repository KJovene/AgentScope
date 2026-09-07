# ADR-0003 — Base de données : SQLite par défaut, PostgreSQL en option

- **Statut :** acceptée
- **Date :** 2026-09-07
- **Décideurs :** WS-platform + WS-domain

## Contexte

Deux exigences se rencontrent :

- **Reproductibilité** — la publication open source est évaluée : quelqu'un qui clone le dépôt doit
  pouvoir lancer l'application et importer un extrait sans installer ni configurer un serveur de
  base de données.
- **Crédibilité technique** — le modèle relationnel (4 points) doit tenir sur un vrai SGBD, pas
  seulement sur un fichier de démonstration.

Les volumes visés sont modestes : des extraits de traces, pas un entrepôt.

## Décision

**SQLite est le moteur par défaut.** `Settings.database_url` vaut `sqlite:///./agentscope.db` ; le
passage à **PostgreSQL se fait par une seule variable d'environnement**
(`AGENTSCOPE_DATABASE_URL=postgresql+psycopg://...`), sans changement de code. Le `docker-compose`
fournit le service Postgres pour ceux qui veulent ce mode.

Conséquences directes sur la façon d'écrire le SQL :

- **SQL standard uniquement.** Pas de type ni de fonction propriétaire : les colonnes JSON
  (`payload_json`, `definition_json`, `sample_values_json`) sont stockées en **texte**, pas en
  `JSONB` ; les agrégats temporels des vues restent portables.
- **Alembic est la seule source de vérité du schéma.** Pas de `create_all()` en production ; toute
  évolution est une migration, accompagnée d'une note dans `docs/data/relational-model.md`.
- Les vues agrégées du dashboard (`v_session_metrics`, `v_daily_activity`, `v_tool_usage`,
  `v_data_quality`) doivent s'exécuter à l'identique sur les deux moteurs.
- Les tests d'intégration de la CI tournent sur SQLite (aucun service à lever).

## Alternatives écartées

| Alternative | Raison du rejet |
| --- | --- |
| PostgreSQL obligatoire | Impose une installation ou Docker avant le premier import ; pénalise la reproductibilité, qui est un critère noté. |
| DuckDB comme base principale | Excellent en lecture analytique, mais orienté colonne et peu adapté aux écritures transactionnelles et à l'ORM. Conservé en revanche comme **outil de profilage** de fichiers (ADR-0001). |
| Pas de migrations (schéma créé par l'ORM) | Rend toute évolution de schéma non traçable et non rejouable — incompatible avec un travail à plusieurs sur le même modèle. |

## Conséquences

- **Positives** — `git clone && make dev` suffit pour importer un fichier. Le même code sert la
  démo locale et un déploiement Postgres.
- **Négatives assumées** — On renonce à `JSONB` et à ses index : les recherches à l'intérieur d'un
  `payload_json` se font en Python après lecture, pas en SQL. Les différences de dialecte
  (`ILIKE`, `date_trunc`, syntaxe d'upsert) doivent être évitées, ce qui contraint l'écriture des
  vues.
- **Risque suivi** — Une divergence SQLite/Postgres peut n'apparaître qu'au déploiement. Parade :
  ajouter un job de CI qui rejoue les tests d'intégration sur Postgres dès que le planning le
  permet.

## Vérification

`make migrate` crée toutes les tables et contraintes (I1.3) ; les tests d'intégration des
repositories passent sur SQLite (I1.5).

## Références

`docs/PLAN.md` §2, §4, §5.4 · `backend/agentscope/infrastructure/config/settings.py` · `docker-compose.yml`
