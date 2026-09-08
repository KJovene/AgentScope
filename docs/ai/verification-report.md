# Compte rendu — parcours d'identification et d'import avec deux modèles IA

> **À remplir** dans les issues **I3.13 / I6.9** (WS-ai), une fois les adaptateurs réels et la
> factory livrés (I3.3, I3.4, I3.5). Ce document est **joint au rendu**.
>
> Règle absolue : **aucune clé, aucun secret, aucune donnée personnelle** dans ce fichier. Les
> échantillons reproduits ici sont ceux qui sont déjà passés par `SensitiveFilter`.

Objectif : montrer que le parcours **fichier inconnu → profil → proposition de mapping →
correction → prévisualisation → import** fonctionne avec **deux configurations de modèle
distinctes**, et que le fournisseur est réellement interchangeable.

Deux configurations à couvrir, idéalement contrastées : **un modèle distant** et **un modèle
local** (voir les recettes dans [`model-switch.md`](model-switch.md)).

---

## Configuration A — *(fournisseur, modèle)*

### Contexte

| | |
| --- | --- |
| Fournisseur (`AGENTSCOPE_LLM_PROVIDER`) | |
| Modèle (`AGENTSCOPE_LLM_MODEL`) | |
| Endpoint (`AGENTSCOPE_LLM_BASE_URL`) | *sans clé* |
| Date de la vérification | |
| Fichier utilisé | provenance, format, nombre de lignes, extrait |

### Ce qui a été transmis au modèle

Résumé du profil de champs (nombre de champs, types inférés, taux de nuls) et taille de
l'échantillon. Préciser que l'échantillon est filtré.

### Proposition obtenue

- Champs correctement mappés : *n* / *total*
- Explications fournies par l'agent : extrait représentatif
- **Ambiguïtés signalées** par l'agent
- **`unmapped_fields`** : la liste, et si elle est justifiée

### Corrections apportées

Ce qui a dû être repris dans l'interface d'édition, et pourquoi.

### Prévisualisation puis import

| | |
| --- | --- |
| Lignes lues | |
| Importées | |
| Doublons | |
| Rejetées (avec `reason_code`) | |
| Informations manquantes | |

### Verdict

Le parcours aboutit-il ? Qu'est-ce que cette configuration fait bien, mal, ou pas du tout ?

---

## Configuration B — *(fournisseur, modèle)*

*Même structure que la configuration A.*

---

## Comparaison

| Critère | Configuration A | Configuration B |
| --- | --- | --- |
| Champs correctement devinés | | |
| Qualité des explications | | |
| Ambiguïtés pertinentes signalées | | |
| Erreurs / réponses malformées (`LLMError`) | | |
| Latence ressentie | | |
| Parcours mené jusqu'à l'import | | |

## Interchangeabilité — la vérification qui compte

- [ ] Un mapping **enregistré avec la configuration A** est rechargé et réappliqué **sous la
      configuration B**, sans passer par l'agent, et produit le même import.
- [ ] Aucun identifiant de modèle, aucune URL, aucune clé n'apparaît dans le code ni dans le
      dépôt — la bascule n'a demandé que l'édition de `.env` et un redémarrage.
- [ ] La suite de tests reste verte avec `AGENTSCOPE_LLM_PROVIDER=fake`, sans réseau.

## Limites connues

Ce que ces deux configurations ne démontrent pas, et ce qui reste à vérifier plus tard.
