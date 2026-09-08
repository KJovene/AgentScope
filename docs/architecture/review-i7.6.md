# Revue d'architecture I7.6

Date : 2026-09-08

## Vérifications

- Le domaine reste indépendant de l'application, de l'infrastructure, des frameworks et des SDK.
- L'application dépend uniquement du domaine et expose les ports utilisés par les cas d'utilisation.
- L'infrastructure implémente les ports applicatifs ; les adaptateurs ne s'appellent pas entre eux.
- Les routes et schémas d'interface passent par les ports injectés et ne construisent pas directement les adaptateurs.
- Le point de composition conserve la responsabilité du câblage concret.

## Écart corrigé

`infrastructure.llm.factory` importait directement `infrastructure.profiling.sensitive_filter`, ce qui couplait deux adaptateurs indépendants. `DefaultSensitiveFilter` est maintenant porté par `application.mapping`; l'ancien module de profilage le réexporte pour préserver les imports existants.

## Preuve

Commande : `docker compose run --rm backend lint-imports`

Résultat : **5 contrats conservés, 0 contrat cassé**.
