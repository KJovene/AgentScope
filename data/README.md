# Données

Ce dossier **ne contient pas** d'extraits de datasets par défaut : `.gitignore` exclut tout sauf
ce fichier. N'ajouter un extrait au dépôt que si ses conditions de redistribution le permettent
explicitement.

> À compléter dans l'issue **I0.10** (WS-platform) pour TraceLab, puis pour la 2ᵉ source.

## Sources

| Source | Référence | Format(s) | Version / date de récupération | Méthode de récupération | Sélection de l'extrait |
| --- | --- | --- | --- | --- | --- |
| TraceLab | https://github.com/uw-syfi/TraceLab | JSONL | _à renseigner_ | _à renseigner_ | _à renseigner_ |
| SWE-chat | https://huggingface.co/datasets/SALT-NLP/SWE-chat | _à renseigner_ | _à renseigner_ | _à renseigner_ | _à renseigner_ |
| Trace Commons | https://huggingface.co/datasets/trace-commons/agent-traces | formats natifs variés | _à renseigner_ | _à renseigner_ | test « structure inconnue » (I6.11) |

## Règles

- Utiliser le **fichier JSONL publié** de TraceLab, pas la base DuckDB ni l'app fournie.
- Extraits de **taille raisonnable**, représentatifs, sélection documentée.
- Données fictives autorisées **uniquement** pour les tests, jamais dans les dashboards.
- Aucune donnée sensible ni secret dans le dépôt.
