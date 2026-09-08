# Fournisseurs IA

AgentScope utilise un modèle de langage pour **une seule chose** : proposer un mapping quand on
lui présente un fichier de traces dont la structure est inconnue, et en discuter. Le fournisseur
et le modèle sont choisis **par configuration**, jamais par un `import` dans le code métier
([ADR-0005](../architecture/adr/0005-abstraction-ia.md)).

Pour changer de modèle, voir [`model-switch.md`](model-switch.md).

---

## 1. Le contrat : `LLMProvider`

Un port déclaré dans
[`application/ports/llm_provider.py`](../../backend/agentscope/application/ports/llm_provider.py),
deux opérations, rien de plus :

```python
class LLMProvider(Protocol):
    name: str

    def propose_mapping(
        self,
        profile: FieldProfileSet,        # statistiques calculées par le programme
        sample: list[dict[str, Any]],    # échantillon filtré, pas le fichier
        target_schema: TargetSchema,     # ce que le normalizer sait produire
    ) -> MappingProposal: ...

    def chat(
        self,
        conversation_id: str,
        messages: list[ChatMessage],
        context: MappingContext,
    ) -> ChatReply: ...
```

Les DTO sont **le** contrat ; le `Protocol` n'en est que l'enveloppe.

| DTO | Champs |
| --- | --- |
| `MappingProposal` | `definition: dict` (conforme au contrat de mapping, **non persisté tel quel**), `explanations: list[FieldExplanation]`, `ambiguities: list[str]`, `unmapped_fields: list[str]` |
| `FieldExplanation` | `target_field`, `source_field \| None`, `rationale`, `confidence` (0–1) |
| `ChatReply` | `text`, `revised_proposal: MappingProposal \| None` |

Deux points structurants dans ce contrat :

- **L'agent explique et doute.** `explanations` et `ambiguities` ne sont pas décoratifs : une
  proposition sans justification n'est pas exploitable par la personne qui doit la valider.
- **`unmapped_fields` est une réponse valide.** Un champ que le modèle ne sait pas interpréter est
  déclaré comme tel — c'est exactement ce qu'on veut montrer face à une structure inconnue.

### Ce que l'agent ne fait pas

| Interdit | Pourquoi | Où c'est tenu |
| --- | --- | --- |
| Écrire en base | la proposition passe par la validation applicative et une action humaine | le port n'expose aucun dépôt ; `ChatAboutMapping` n'a pas d'accès en écriture |
| Calculer un chiffre du dashboard | les indicateurs sont calculés en SQL, testés, reproductibles | [`../data/indicators.md`](../data/indicators.md) |
| Exécuter sa propre sortie | la `definition` est convertie vers le contrat de mapping, puis **validée** ; les transformations sont whitelistées | `application/mapping/validator.py`, [ADR-0004](../architecture/adr/0004-contrat-de-mapping.md) |
| Recevoir un fichier entier | seuls un profil de champs et un échantillon filtré partent | `SensitiveFilter`, §5 |

**Le texte contenu dans une trace est une donnée, jamais une consigne.** Une trace peut contenir
n'importe quoi, y compris quelque chose qui ressemble à une instruction adressée au modèle : le
constructeur de prompt la traite comme du contenu à analyser, et la sortie est de toute façon
validée avant d'avoir le moindre effet.

---

## 2. Adaptateurs

Les implémentations vivent dans
[`infrastructure/llm/`](../../backend/agentscope/infrastructure/llm/).

| `AGENTSCOPE_LLM_PROVIDER` | Adaptateur | Couvre | État |
| --- | --- | --- | --- |
| `fake` **(défaut)** | `FakeLLMProvider` | tests, CI, développement hors ligne | ✅ livré |
| `anthropic` | `AnthropicProvider` | API Anthropic | ⬜ I3.3 |
| `openai` | `OpenAICompatibleProvider` | API OpenAI | ⬜ I3.4 |
| `ollama` | `OpenAICompatibleProvider` + `base_url` | Ollama, LM Studio, tout serveur compatible OpenAI — **modèle local, aucune clé** | ⬜ I3.4 |

Un seul adaptateur est actif à la fois, choisi au démarrage par la factory pilotée par la
configuration (I3.5).

### `FakeLLMProvider` — le fournisseur par défaut

Déterministe, aucun appel réseau, aucun état interne. Son comportement exact :

- `propose_mapping` collecte les clés de tous les enregistrements de l'échantillon, les trie, et
  renvoie un **mapping identité** — un champ cible par clé source, transformation `identity` —
  avec une `FieldExplanation` par champ. Le même échantillon donne toujours la même proposition.
- `chat` renvoie une réponse fixe, sans proposition révisée.

Il n'est pas là pour être intelligent, mais pour que **tout le reste du parcours soit testable**
sans clé, sans réseau et sans budget : analyse → proposition → validation → prévisualisation →
import tournent intégralement avec lui.

---

## 3. Configuration

Quatre variables, préfixe `AGENTSCOPE_`, lues par
[`infrastructure/config/settings.py`](../../backend/agentscope/infrastructure/config/settings.py)
— le seul endroit du code qui touche à l'environnement.

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `AGENTSCOPE_LLM_PROVIDER` | `fake` | quel adaptateur instancier |
| `AGENTSCOPE_LLM_MODEL` | — | identifiant du modèle, **jamais en dur dans le code** |
| `AGENTSCOPE_LLM_BASE_URL` | — | endpoint, pour les serveurs compatibles OpenAI |
| `AGENTSCOPE_LLM_API_KEY` | — | **clé secrète** — jamais commitée, jamais journalisée |

`.env` est ignoré par git et `.env.example` ne contient que des valeurs vides ou non secrètes.
Les recettes par fournisseur sont dans [`model-switch.md`](model-switch.md).

---

## 4. Ajouter un fournisseur

Le but de l'abstraction : un nouveau fournisseur ne touche **ni** le domaine, **ni** les cas
d'utilisation, **ni** le moteur d'import.

1. **Créer l'adaptateur** dans `infrastructure/llm/<fournisseur>_provider.py` :

   ```python
   class MonProvider:
       name = "mon-fournisseur"

       def __init__(self, model: str, api_key: str | None, base_url: str | None) -> None:
           ...  # le SDK ne vit qu'ici

       def propose_mapping(self, profile, sample, target_schema) -> MappingProposal:
           ...

       def chat(self, conversation_id, messages, context) -> ChatReply:
           ...
   ```

   Pas d'héritage : `LLMProvider` est un `Protocol`, il suffit d'avoir les bonnes signatures.

2. **Convertir la réponse vers le contrat commun.** Le modèle renvoie du texte ; l'adaptateur en
   extrait une `MappingProposal`. Une réponse malformée lève **`LLMError`**
   (`domain/errors.py`) — jamais un crash, jamais une proposition à moitié remplie.

3. **Traduire les erreurs du fournisseur** — réseau coupé, quota dépassé, délai dépassé,
   authentification refusée — en `LLMError` avec un message exploitable. Le reste de
   l'application ne connaît que ce type.

4. **Le raccorder à la factory**, sur une valeur de `AGENTSCOPE_LLM_PROVIDER`. Aucune clé, aucune
   URL, aucun identifiant de modèle en dur.

5. **Écrire les tests** — sur le modèle de `tests/unit/test_fake_llm_provider.py` :
   conformité au `Protocol` (`isinstance(provider, LLMProvider)`, il est `runtime_checkable`),
   conversion d'une réponse type, et `LLMError` sur une réponse malformée. **Aucun test
   n'appelle le fournisseur réel** : la CI reste hors réseau.

6. **Documenter** : une ligne dans le tableau du §2, la recette dans
   [`model-switch.md`](model-switch.md), et le compte rendu de vérification si ce fournisseur
   sert à l'une des deux configurations testées.

Contrainte vérifiée automatiquement (`make arch`) : le SDK du fournisseur ne doit apparaître que
dans `infrastructure/llm/`. `domain` et `application` ne peuvent pas l'importer — les contrats 2
et 3 d'`import-linter` échouent sinon.

---

## 5. Garde-fous

- **Rien ne part sans filtrage.** Les échantillons transmis passent par `SensitiveFilter`
  (masquage des adresses, clés, jetons, chemins personnels) avant de rejoindre le prompt. On
  n'envoie **jamais** le fichier complet : un profil de champs et un échantillon suffisent.
- **Les statistiques sont calculées par le programme**, en SQL testé — jamais demandées au modèle.
  Un chiffre du dashboard ne dépend d'aucun appel IA.
- **La sortie du modèle est une donnée**, convertie puis validée par
  `application/mapping/validator.py`. Un mapping non conforme est refusé avec la liste des
  problèmes ; il n'atteint jamais la base.
- **Aucune clé dans le dépôt ni dans les journaux.** La configuration passe par l'environnement ;
  une clé exposée par accident se **révoque**, la retirer de l'historique ne suffit pas.
- **La CI n'appelle aucun modèle réel** : `fake` par défaut, donc aucune dépendance réseau,
  aucun coût, et des tests reproductibles.

---

## 6. État actuel

| Élément | État |
| --- | --- |
| Port `LLMProvider`, DTO (`MappingProposal`, `FieldExplanation`, `ChatReply`), `LLMError` | ✅ livrés et testés (I3.1) |
| `FakeLLMProvider` | ✅ livré et testé (I3.2) |
| Adaptateurs Anthropic / OpenAI-compatible | ⬜ I3.3, I3.4 |
| Factory pilotée par la configuration | ⬜ I3.5 — **tant qu'elle n'existe pas, changer `AGENTSCOPE_LLM_PROVIDER` reste sans effet** |
| Constructeur de prompt + `SensitiveFilter` | ⬜ I3.6, I2.14 |
| Use cases `AnalyzeUnknownFile`, `ChatAboutMapping`, `PreviewMapping` | ⬜ EPIC 3 |
| Vérification avec 2 modèles réels | ⬜ I3.13 — [`verification-report.md`](verification-report.md) |

Ce document décrit le contrat figé au cadrage : il est ce que les adaptateurs doivent respecter,
et il ne bougera pas quand ils arriveront.
