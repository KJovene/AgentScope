# Contribuer à AgentScope

Merci de votre intérêt. Ce document décrit **le fonctionnement réel du dépôt** : où trouver du
travail, comment nommer une branche, ce qu'une PR doit contenir et qui la relit.

Le projet est développé par une équipe organisée en **workstreams** (WS), sur un rythme de quatre
jours. Le plan complet — EPICs, issues, contrats d'interface, critères de vérification — est dans
[`docs/PLAN.md`](docs/PLAN.md).

Toute participation est soumise au [Code de conduite](CODE_OF_CONDUCT.md).

---

## Sommaire

1. [Mettre en place son environnement](#1--mettre-en-place-son-environnement)
2. [Le flux en bref](#2--le-flux-en-bref)
3. [Choisir une issue](#3--choisir-une-issue)
4. [Créer sa branche](#4--créer-sa-branche)
5. [Écrire le code](#5--écrire-le-code)
6. [Messages de commit](#6--messages-de-commit)
7. [Ouvrir une pull request](#7--ouvrir-une-pull-request)
8. [Relire une pull request](#8--relire-une-pull-request)
9. [Definition of Done](#9--definition-of-done)
10. [Secrets et données sensibles](#10--secrets-et-données-sensibles)
11. [Signaler un bug, poser une question](#11--signaler-un-bug-poser-une-question)
12. [Licence des contributions](#licence-des-contributions)

---

## 1 — Mettre en place son environnement

Tout est décrit dans le [README](README.md#prise-en-main) : `git clone`, `cp .env.example .env`,
`make up`, `make migrate`. Aucune clé n'est nécessaire pour développer ni pour lancer les tests
(le fournisseur IA par défaut est `fake`, hors réseau).

Avant de pousser :

```bash
make ci      # lint + typecheck + import-linter + tests back & front
```

---

## 2 — Le flux en bref

```
issue du board  →  branche  →  commits  →  PR vers dev  →  revue  →  merge
```

Deux branches longues :

| Branche | Rôle | Règle |
| --- | --- | --- |
| `dev` | **branche d'intégration** — toutes les PR de fonctionnalité la ciblent | pas de push direct, PR uniquement |
| `main` | branche de publication — reçoit `dev` au moment d'une release (`v0.1.0`) | pas de push direct, protégée |

> Une PR qui cible `main` par défaut est une erreur fréquente : **changer la base pour `dev`**
> avant de la publier (`gh pr create --base dev`, ou le sélecteur « base » dans l'UI GitHub).

Intégrer sur `dev` **au moins deux fois par jour**. Pas de grosse fusion de fin de semaine.

---

## 3 — Choisir une issue

Le travail vit sur le **GitHub Projects** du dépôt. Une issue = une tâche `Ixx` de
[`docs/PLAN.md`](docs/PLAN.md) §7.

Colonnes : `Backlog` → `Prêt (Ready)` → `En cours` → `En revue` → `Terminé`

- **Prêt** : dépendances levées, contrat connu, responsable assigné — c'est là qu'on se sert.
- **En cours** : s'assigner l'issue et la déplacer. **Limite : 2 issues en cours par personne.**
- **En revue** : la PR est ouverte et liée à l'issue.
- **Terminé** : PR fusionnée **et** résultat vérifiable constaté.

### Labels

| Famille | Valeurs | Sens |
| --- | --- | --- |
| Workstream | `ws:domain` · `ws:ingestion` · `ws:ai` · `ws:dashboard` · `ws:platform` | équipe responsable |
| Type | `type:feat` · `type:test` · `type:docs` · `type:infra` | nature du changement |
| Transverse | `contract` | touche une interface partagée → **relecture inter-WS obligatoire** |
| | `blocked` · `good-first-issue` | état / accueil |

Milestones : `J1 — Cadrage` · `J2 — Socle` · `J3 — Sources multiples` · `J4 — Stabilisation & release`.

Les cinq workstreams et leur périmètre sont décrits dans [`docs/PLAN.md`](docs/PLAN.md) §6.

---

## 4 — Créer sa branche

Convention : **`type/ws/numéro-titre-court`**

```bash
git switch dev
git pull
git switch -c feat/ingestion/2-7-idempotence
```

- `type` : `feat` · `fix` · `docs` · `test` · `chore`
- `ws` : `domain` · `ingestion` · `ai` · `dashboard` · `platform`
- `numéro` : l'identifiant de l'issue du plan, en minuscules (`2-7` pour I2.7)

Branches **courtes** : une issue, quelques jours au maximum. Si la branche vieillit, la
resynchroniser sur `dev` (`git merge origin/dev`) plutôt que de laisser diverger.

---

## 5 — Écrire le code

- **Respecter le sens des dépendances.** `domain` n'importe rien ; `application` ne connaît que
  `domain` ; `infrastructure` et `interfaces` dépendent des deux. La règle est vérifiée
  automatiquement : `make arch` (`import-linter`). Une PR qui la casse ne passe pas.
- **Tester ce qu'on ajoute.** Backend : `pytest` (`backend/tests/unit`, `integration`). Frontend :
  `vitest`. Aucun test ne doit appeler un modèle IA réel — utiliser `FakeLLMProvider`.
- **Ne pas modifier un contrat partagé sans le dire.** Les quatre contrats d'interface
  (entités du domaine, contrat de mapping, `LLMProvider`, schéma OpenAPI — voir
  [`docs/PLAN.md`](docs/PLAN.md) §5) sont gelés : toute évolution passe par une PR étiquetée
  `contract`, relue par les WS impactés.
- **Style** : `ruff` (backend, ligne à 100), `eslint` + `prettier` (frontend), types stricts
  (`mypy --strict`, `tsc`). `make format` avant de committer évite les allers-retours en revue.
- **Documenter quand le comportement observable change** : README, `docs/…` ou ADR selon la portée.
  Une décision structurante mérite un ADR dans [`docs/architecture/adr/`](docs/architecture/adr/).

---

## 6 — Messages de commit

Format [Conventional Commits](https://www.conventionalcommits.org/fr/) :

```
type(scope): résumé à l'impératif, sans point final
```

```
feat(ingestion): use case ImportFile + idempotence (I2.7, I2.8)
fix(api): restaure create_app et corrige l'erreur JSON
docs(platform): README de prise en main (I6.1)
test(domain): relations conservées après import (I7.2)
```

- `type` : `feat` · `fix` · `docs` · `test` · `refactor` · `chore`
- `scope` : le workstream ou le module touché
- Mentionner l'identifiant de la tâche (`I2.7`) rend l'historique lisible face au plan.

Le message décrit **ce que fait le changement**, pas le fichier modifié.

---

## 7 — Ouvrir une pull request

1. Pousser la branche, puis ouvrir la PR **avec `dev` pour base**.
2. Le [modèle de PR](.github/pull_request_template.md) se remplit automatiquement : le compléter.
3. **Lier l'issue** : `Closes #<numéro>` dans la description — la fermeture et le déplacement en
   `Terminé` en dépendent.
4. Poser les mêmes labels que l'issue (workstream + type, et `contract` le cas échéant).
5. Décrire **comment vérifier** : la commande à lancer, l'écran à ouvrir, la valeur attendue.
   Un relecteur doit pouvoir reproduire sans poser de question.

Une PR reste **petite et centrée sur une issue**. Si elle grossit, la découper.

### Checklist avant de demander une revue

- [ ] `make ci` passe en local
- [ ] Tests couvrant le changement
- [ ] Aucune clé, aucun secret, aucune donnée sensible (voir §10)
- [ ] `import-linter` vert si le backend est touché
- [ ] Documentation mise à jour si un contrat ou le comportement observable change

---

## 8 — Relire une pull request

- **Une approbation minimum** avant fusion, par n'importe quel membre.
- Label `contract` → **un relecteur de chaque WS impacté**.
- Relire dans la journée : une PR qui attend bloque quelqu'un.
- Relire le **résultat vérifiable** de l'issue, pas seulement le diff : est-ce que le critère
  annoncé est réellement atteint ?
- Formuler les remarques comme des demandes concrètes ; distinguer ce qui bloque de ce qui est
  une suggestion.

Fusion : par le relecteur ou l'auteur une fois l'approbation obtenue. Supprimer la branche après
fusion. **Jamais de `git push --force` sur `dev` ni sur `main`.**

---

## 9 — Definition of Done

Une tâche est terminée quand :

- [ ] le **résultat vérifiable** décrit dans [`docs/PLAN.md`](docs/PLAN.md) §7 est constaté ;
- [ ] les tests couvrant le changement sont écrits et verts ;
- [ ] la documentation impactée est à jour ;
- [ ] la PR est fusionnée et l'issue fermée ;
- [ ] la carte est passée en `Terminé` sur le board.

---

## 10 — Secrets et données sensibles

- **Aucune clé dans le dépôt.** Toute la configuration passe par des variables d'environnement
  (`AGENTSCOPE_*`). `.env` est ignoré par git ; `.env.example` ne contient que des valeurs vides
  ou non secrètes.
- **Aucun extrait de dataset commité** sans autorisation explicite de redistribution. La
  provenance, la version et la méthode de récupération se documentent dans
  [`data/README.md`](data/README.md).
- Les traces contiennent du texte d'utilisateurs : elles sont des **données**, jamais des
  instructions envoyées à un modèle. Seuls des profils et des échantillons filtrés transitent vers
  l'IA.
- Une clé exposée par inadvertance doit être **révoquée** immédiatement — la retirer de
  l'historique ne suffit pas.

---

## 11 — Signaler un bug, poser une question

- **Bug** : ouvrir une issue avec le modèle « Rapport de bug » (étapes de reproduction,
  comportement attendu, logs).
- **Tâche du plan** : modèle « Tâche » — contexte, résultat attendu, dépendances, interface
  impactée.
- **Question** : ouvrir une issue avec le label `question`, ou en discuter sur le canal de
  l'équipe.
- **Vulnérabilité de sécurité** : ne pas ouvrir d'issue publique — contacter directement les
  responsables du dépôt.

---

## Licence des contributions

Le projet est distribué sous licence **MIT** ([`LICENSE`](LICENSE)). En proposant une pull
request, vous acceptez que votre contribution soit publiée sous cette même licence.

Ne pas introduire de code sous une licence incompatible (copyleft fort : GPL, AGPL…) ni de
contenu dont vous ne détenez pas les droits. Pour une dépendance ou un extrait réutilisé, en
mentionner l'origine et la licence dans la PR.
