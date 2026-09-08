# Changer de modèle IA

Changer de fournisseur ou de modèle est une **modification de configuration** : quatre variables
d'environnement et un redémarrage. Aucun code à toucher, aucun mapping à refaire.

Le contrat que respectent tous les fournisseurs est décrit dans [`providers.md`](providers.md).

---

## 1. La procédure

```bash
# 1. Éditer .env  (à la racine du dépôt ; ignoré par git)
AGENTSCOPE_LLM_PROVIDER=anthropic
AGENTSCOPE_LLM_MODEL=<identifiant du modèle>
AGENTSCOPE_LLM_API_KEY=<votre clé>

# 2. Redémarrer le backend — la configuration est lue au démarrage
docker compose up -d backend

# 3. Vérifier : ouvrir l'écran « Ajouter une source », déposer un fichier inconnu,
#    et constater qu'une proposition de mapping revient avec ses explications.
```

C'est tout. Le reste de l'application — import, dashboard, indicateurs — ne dépend d'aucun appel
IA et n'est pas affecté.

---

## 2. Les variables

| Variable | Rôle | Obligatoire |
| --- | --- | --- |
| `AGENTSCOPE_LLM_PROVIDER` | `fake` · `anthropic` · `openai` (voir note ci-dessous pour Ollama/LM Studio) | oui (défaut `fake`) |
| `AGENTSCOPE_LLM_MODEL` | identifiant du modèle chez ce fournisseur | oui sauf pour `fake` |
| `AGENTSCOPE_LLM_BASE_URL` | endpoint, pour les serveurs compatibles OpenAI | pour un serveur local |
| `AGENTSCOPE_LLM_API_KEY` | clé secrète | pour `anthropic` ; optionnelle pour `openai` (un serveur local n'en demande pas) |

> Il n'existe **pas** de valeur `ollama` pour `AGENTSCOPE_LLM_PROVIDER`. Ollama et LM Studio sont
> des serveurs compatibles avec l'API OpenAI : on les utilise avec `AGENTSCOPE_LLM_PROVIDER=openai`
> et `AGENTSCOPE_LLM_BASE_URL` pointé vers ce serveur — même code, aucune branche dédiée
> (ADR-0005). Voir la recette ci-dessous.

Ces valeurs sont lues **au démarrage du processus** : un changement dans `.env` ne prend effet
qu'après redémarrage du backend.

---

## 3. Recettes

### Modèle distant — Anthropic

```bash
AGENTSCOPE_LLM_PROVIDER=anthropic
AGENTSCOPE_LLM_MODEL=<identifiant du modèle>
AGENTSCOPE_LLM_API_KEY=<clé>
# AGENTSCOPE_LLM_BASE_URL : inutile
```

### Modèle distant — OpenAI

```bash
AGENTSCOPE_LLM_PROVIDER=openai
AGENTSCOPE_LLM_MODEL=<identifiant du modèle>
AGENTSCOPE_LLM_API_KEY=<clé>
```

### Modèle local — Ollama ou LM Studio *(aucune clé)*

```bash
AGENTSCOPE_LLM_PROVIDER=openai
AGENTSCOPE_LLM_MODEL=<modèle servi localement>
AGENTSCOPE_LLM_BASE_URL=http://host.docker.internal:11434/v1
# AGENTSCOPE_LLM_API_KEY : inutile, laisser vide ou absent
```

> Depuis un conteneur, `localhost` désigne le conteneur lui-même : utiliser
> **`host.docker.internal`** pour joindre un serveur qui tourne sur la machine hôte. En exécution
> locale hors Docker, `http://localhost:11434/v1` convient.

### Revenir au fournisseur factice

```bash
AGENTSCOPE_LLM_PROVIDER=fake
```

Aucun appel réseau, réponses déterministes — c'est la configuration des tests et de la CI, et
celle qu'il faut pour développer sans consommer de budget.

---

## 4. Ce qui ne change pas quand on change de modèle

C'est la garantie que l'abstraction doit tenir :

- **Un mapping enregistré reste applicable.** Un mapping est un document JSON versionné, conforme
  au contrat ([ADR-0004](../architecture/adr/0004-contrat-de-mapping.md)) et stocké en base. Il ne
  contient aucune référence au modèle qui l'a proposé : on peut le réappliquer après un changement
  de fournisseur, ou même sans aucun fournisseur configuré.
- **Les imports déjà faits ne bougent pas.** Le moteur d'ingestion n'appelle aucun modèle.
- **Les indicateurs ne bougent pas.** Ils sont calculés en SQL, jamais demandés au modèle.
- **Le contrat de sortie est le même.** Quel que soit le fournisseur, l'application reçoit une
  `MappingProposal` validée, ou une `LLMError`.

Ce qui change, en revanche : la **qualité** des propositions — champs correctement devinés,
pertinence des explications, ambiguïtés signalées. C'est précisément ce que compare le
[compte rendu de vérification](verification-report.md).

---

## 5. Vérifier qu'un changement a bien pris

1. Contrôler la configuration réellement chargée par le backend — **sans afficher la clé** :

   ```bash
   docker compose exec backend python -c \
     "from agentscope.infrastructure.config.settings import get_settings as g; s=g(); \
      print(s.llm_provider, s.llm_model, s.llm_base_url)"
   ```

2. Déposer le **même** fichier inconnu qu'avec la configuration précédente, sur l'écran
   « Ajouter une source ».
3. Comparer : les propositions doivent différer (ou converger) de façon explicable, et dans les
   deux cas mener à un import réussi après validation.
4. Reprendre un mapping enregistré avec l'ancienne configuration et le réappliquer : il doit
   fonctionner à l'identique.

Ces quatre points sont exactement ce que consigne le compte rendu I3.13 / I6.9.

---

## 6. Dépannage

| Symptôme | Cause probable |
| --- | --- |
| L'agent répond toujours la même chose, très mécaniquement | `AGENTSCOPE_LLM_PROVIDER` est resté à `fake` (défaut) |
| Erreur d'authentification | clé absente ou invalide — vérifier que `.env` est bien pris en compte (`docker compose config` montre les variables résolues) |
| Endpoint injoignable depuis Docker | utiliser `host.docker.internal` plutôt que `localhost` (§3) |
| `LLMError : réponse malformée` | le modèle n'a pas produit une proposition conforme au contrat — l'application refuse proprement plutôt que d'écrire n'importe quoi. Réessayer, ou changer de modèle |
| Le changement de `.env` ne fait rien | la configuration est lue au démarrage : redémarrer le backend |

---

## 7. État actuel

| Élément | État |
| --- | --- |
| Variables de configuration `AGENTSCOPE_LLM_*` | ✅ lues par `Settings` |
| `FakeLLMProvider` | ✅ livré |
| Factory pilotée par la configuration | ✅ livrée (I3.5) — la procédure ci-dessus est opérante |
| Adaptateurs réels (Anthropic, OpenAI-compatible) | ✅ livrés (I3.3, I3.4) |
| Deux configurations vérifiées bout en bout | ⬜ I3.13 — [`verification-report.md`](verification-report.md) |

La procédure ci-dessus est celle prévue par [ADR-0005](../architecture/adr/0005-abstraction-ia.md).
