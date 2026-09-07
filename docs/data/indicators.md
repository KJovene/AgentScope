# Définitions des indicateurs

> Stub — à compléter dans l'issue **I6.5** (WS-platform + WS-dashboard). Base dans `PLAN.md` §4.

Pour **chaque indicateur** du dashboard, une fiche :

| Champ | Contenu attendu |
| --- | --- |
| Nom | libellé affiché |
| Calcul | formule / requête, à la ligne près |
| Unité | tokens, USD, s, %, nombre… |
| Périmètre | filtres appliqués, sources concernées |
| Valeurs manquantes | comment `NULL` est traité — **jamais** transformé en `0` |
| Comparabilité inter-sources | comparable / à signaler / à garder séparé |

Indicateurs prévus : Sessions, Tokens consommés (in/out/cached), Coût estimé, Répartition des
outils, Durée médiane de session, Taux d'erreur, Taux d'utilisation du cache.
