# Mappings de sources

Une fiche par source intégrée : **comment un fichier de cette source devient des lignes du modèle
relationnel**, ce qui a été laissé de côté, et le résultat du test bout-en-bout sur l'extrait réel.

Le format d'un mapping — JSON versionné, transformations whitelistées — est décrit dans
[ADR-0004](../../architecture/adr/0004-contrat-de-mapping.md) et `docs/PLAN.md` §5.1. Le schéma
cible est celui de [`relational-model.md`](../relational-model.md).

## État

| Source | Fiche | Mapping | Issue |
| --- | --- | --- | --- |
| TraceLab | ⬜ `tracelab.md` | ⬜ à écrire | I2.11 |
| SWE-chat | ⬜ `swe-chat.md` | ⬜ à écrire | I2.12 |
| Trace Commons | — | test « structure inconnue », pas d'intégration | I6.11 |

Deux sources distinctes sont **exigées** pour la release (`docs/PLAN.md` §11).

## Ce que contient une fiche

Reprendre ce plan tel quel — c'est ce que I6.5 attend dans `docs/data/`.

### 1. Identité de la source

Nom, référence (URL du dataset), licence des données, format(s) de fichier, version et date de
l'extrait utilisé. Doit correspondre à la ligne de [`data/README.md`](../../../data/README.md).

### 2. Ce qu'est une ligne du fichier

La question décisive : **une ligne du fichier source = quoi ?** Un aller-retour avec le modèle ?
Une session entière ? Un événement ? C'est ce qui détermine la structure `iterate` du mapping et
la façon dont on lit ensuite l'indicateur « nombre de sessions ».

### 3. Correspondances champ par champ

| Champ cible | Chemin source | Transformation | Notes |
| --- | --- | --- | --- |
| `session.external_id` | … | `identity` | … |
| `model_call.prompt_tokens` | … | `to_int` | … |

Une ligne par champ cible réellement alimenté, y compris les constantes.

### 4. Champs non mappés (`unmapped_fields`)

La liste des champs du fichier source qu'on **n'a pas** repris, et **pourquoi** : hors périmètre,
redondant, non interprétable. C'est une information de premier ordre, pas un oubli à cacher.

### 5. Ce que la source ne fournit pas

Les champs cibles laissés à `NULL` — coût, `cached_tokens`, `ended_at`… — et l'effet sur les
indicateurs : quel chiffre du dashboard sera « non disponible » pour cette source.
Voir [`indicators.md`](../indicators.md) §3 pour les conséquences de chaque absence.

### 6. Résultat du test bout-en-bout

Sur l'extrait réel : lignes lues, importées, en doublon, rejetées (avec les `reason_code`
rencontrés), et les lignes produites par entité. Le test correspondant, dans `backend/tests/`.

### 7. Comparabilité

Ce qui est comparable avec les autres sources et ce qui ne l'est pas — bornes de session,
granularité des appels, nommage des outils.
