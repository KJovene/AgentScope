<!--
Base de la PR : `dev` (sauf release vers `main`).
Titre : convention Conventional Commits — ex. `feat(ingestion): use case ImportFile (I2.8)`
-->

Closes #

## Ce que fait cette PR

<!-- En quelques lignes : le problème résolu, l'approche retenue. Pas la liste des fichiers. -->

## Comment vérifier

<!--
La procédure exacte pour reproduire le résultat, sans avoir à poser de question :
commande à lancer, écran à ouvrir, valeur attendue.
Ex. : `make test` puis `curl http://localhost:8000/api/v1/metrics/indicators` → …
-->

## Interface impactée

<!-- Port, schéma DB, OpenAPI, contrat de mapping — ou « aucune ».
     Si une interface partagée bouge : poser le label `contract`. -->

aucune

## Checklist

- [ ] `make ci` passe en local (lint + types + `import-linter` + tests)
- [ ] Tests couvrant le changement
- [ ] Aucun secret, aucune clé API, aucune donnée sensible
- [ ] Documentation mise à jour (README / `docs/…` / ADR) si le comportement observable change
- [ ] Labels posés (workstream + type, `contract` si applicable)
- [ ] Relecteur d'un autre workstream demandé si label `contract`
