# Documentation IA

L'IA sert à **une seule chose** dans AgentScope : proposer un mapping quand on présente à
l'application un fichier de traces dont la structure lui est inconnue, et en discuter. Elle ne
calcule aucun chiffre du dashboard et n'écrit jamais en base.

Concrètement, elle n'intervient que sur trois endpoints — `POST /api/v1/analyze`,
`POST /api/v1/chat` et `POST /api/v1/mappings/{id}/preview` (ce dernier sans appel au modèle) —
donc sur l'écran « Source » et l'assistant. Import, indicateurs et dashboard tournent sans elle.

| Document | Contenu | État |
| --- | --- | --- |
| [`providers.md`](providers.md) | le port `LLMProvider`, ses DTO, les adaptateurs, la configuration, comment en ajouter un, les garde-fous | ✅ |
| [`model-switch.md`](model-switch.md) | changer de fournisseur ou de modèle par configuration : procédure, recettes, ce qui ne change pas, dépannage | ✅ |
| [`verification-report.md`](verification-report.md) | le parcours vérifié avec **deux modèles réels** | ⬜ gabarit prêt — à remplir (I3.13 / I6.9) |

Décision de fond : [ADR-0005 — Abstraction IA](../architecture/adr/0005-abstraction-ia.md).
Place de ces composants dans l'architecture :
[`../architecture/components.md`](../architecture/components.md).

## Les trois règles

1. **L'IA propose, elle ne dispose pas.** Sa sortie est convertie vers le contrat de mapping, puis
   validée par l'application. Une proposition non conforme est refusée ; elle n'atteint jamais la
   base.
2. **Le texte d'une trace est une donnée, jamais une consigne.** Ce qui ressemble à une
   instruction dans un fichier importé reste du contenu à analyser.
3. **Rien ne part sans filtrage, et jamais un fichier entier.** On transmet un profil de champs et
   un échantillon passé par `SensitiveFilter` — assez pour reconnaître une structure, pas assez
   pour exfiltrer un jeu de données.
