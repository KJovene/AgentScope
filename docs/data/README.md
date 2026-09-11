# Documentation des données

Tout ce qui décrit **la donnée** d'AgentScope : sa structure, ce que valent les chiffres qu'on en
tire, et comment chaque source y entre.

| Document | Contenu | État |
| --- | --- | --- |
| [`relational-model.md`](relational-model.md) | schéma relationnel v1 : diagramme, table par table, clés naturelles, contraintes, vues, justification 3NF | ✅ |
| [`indicators.md`](indicators.md) | une fiche par indicateur : calcul à la ligne près, unité, périmètre, traitement des `NULL`, comparabilité inter-sources | ✅ |
| [`mappings/`](mappings/) | une fiche par source intégrée : correspondances, champs non mappés, résultat du test bout-en-bout | ✅ TraceLab et SWE-chat, avec leur définition JSON exécutable |

Ailleurs dans le dépôt :

- [`data/README.md`](../../data/README.md) — **provenance** des extraits : dataset, version, date
  de récupération, licence, méthode de sélection. Les extraits eux-mêmes ne sont pas commités.
- [`../architecture/components.md`](../architecture/components.md) — où vivent le moteur de
  mapping, les dépôts et les vues dans l'architecture.
- [ADR-0003](../architecture/adr/0003-base-de-donnees.md) (SQLite / PostgreSQL),
  [ADR-0004](../architecture/adr/0004-contrat-de-mapping.md) (contrat de mapping),
  [ADR-0006](../architecture/adr/0006-provenance.md) (provenance et rétention).

## Le principe qui tient tout

**Une valeur absente n'est pas zéro.** Elle reste `NULL` de la table jusqu'à l'écran, où elle
s'affiche « non disponible ». C'est vrai des tokens, du coût, des horodatages, et de tout
indicateur qui en dépend. Un dashboard qui affiche `0 $` pour une source qui ne communique pas ses
coûts ment ; AgentScope affiche « non disponible ».
