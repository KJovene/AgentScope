# ADR-0005 — Abstraction IA : port `LLMProvider` et adaptateurs pilotés par configuration

- **Statut :** acceptée
- **Date :** 2026-09-07
- **Décideurs :** WS-ai + WS-platform

## Contexte

L'énoncé exige que le fournisseur d'IA soit **interchangeable** : changer de modèle ne doit pas
demander de toucher au code métier. Trois contraintes s'y ajoutent :

- La CI doit tourner **sans réseau, sans clé et sans budget**.
- Les traces importées peuvent contenir des données sensibles (chemins, adresses, jetons).
- Le texte contenu dans une trace est du contenu **non fiable** : il ne doit jamais être interprété
  comme une consigne adressée au modèle.

## Décision

Un port **`LLMProvider`** est déclaré dans `application/ports/llm_provider.py` avec deux opérations
seulement : `propose_mapping(profile, sample, target_schema) -> MappingProposal` et
`chat(conversation_id, messages, context) -> ChatReply`.

Les implémentations vivent dans `infrastructure/llm/` :

| Adaptateur | Couvre |
| --- | --- |
| `FakeLLMProvider` | Tests et CI — aucun appel réseau. **Défaut** (`AGENTSCOPE_LLM_PROVIDER=fake`). |
| `AnthropicProvider` | API Anthropic. |
| `OpenAICompatibleProvider` | OpenAI, et tout serveur compatible — Ollama, LM Studio — via `base_url`. |

Le choix se fait par **configuration** au démarrage, dans une factory :
`AGENTSCOPE_LLM_PROVIDER`, `AGENTSCOPE_LLM_MODEL`, `AGENTSCOPE_LLM_BASE_URL`,
`AGENTSCOPE_LLM_API_KEY`. **Aucun identifiant de modèle, aucune URL, aucune clé en dur** dans le
code ; aucune clé dans le dépôt.

Deux garde-fous font partie de la décision :

- **La sortie du modèle est une donnée, pas une vérité.** Elle est convertie vers le contrat de
  mapping (ADR-0004), validée par l'application, et n'est jamais exécutée.
- **Rien ne part vers un fournisseur sans passer par `SensitiveFilter`** : on transmet des profils
  de champs et des échantillons filtrés, jamais un fichier entier. Les statistiques affichées dans
  le dashboard sont calculées par le programme en SQL, **jamais demandées au modèle**.

## Alternatives écartées

| Alternative | Raison du rejet |
| --- | --- |
| Appeler le SDK d'un fournisseur directement dans les use cases | Couple le métier à un fournisseur : « IA interchangeable » deviendrait une affirmation invérifiable. Interdit par le contrat `import-linter` de l'ADR-0002. |
| Framework d'orchestration (LangChain & co.) | Dépendance lourde qui impose ses abstractions et masque précisément la frontière que l'on veut rendre visible et testable. |
| Un seul fournisseur, changé par édition du code | Ne satisfait pas le critère d'évaluation. |

## Conséquences

- **Positives** — La CI s'exécute intégralement avec `FakeLLMProvider` : rapide, gratuite, sans
  dépendance réseau. Changer de modèle se réduit à éditer `.env` et redémarrer (procédure dans
  `docs/ai/model-switch.md`). Ajouter un fournisseur = un adaptateur + son raccordement dans la
  factory, sans toucher au moteur d'import.
- **Négatives assumées** — On n'utilise que le **sous-ensemble commun** des API. Les capacités
  spécifiques à un fournisseur (appel d'outil natif, sortie structurée garantie) doivent être
  encapsulées dans l'adaptateur, qui les émule si le fournisseur ne les offre pas. Les différences
  de qualité entre modèles sont réelles : elles sont documentées dans
  `docs/ai/verification-report.md` plutôt que gommées.

## Vérification

Deux configurations distinctes (un modèle distant, un modèle local) produisent une proposition de
mapping valide sur le même fichier ; un mapping enregistré reste applicable après changement de
modèle (I3.14, I6.9).

### Mise en œuvre — écarts de nommage (constaté le 2026-09-11)

La décision est appliquée telle quelle ; seuls deux noms diffèrent de ce qui était écrit ici au
cadrage, et la décision n'est pas réécrite pour autant :

- l'adaptateur compatible OpenAI s'appelle **`OpenAIProvider`** (et non
  `OpenAICompatibleProvider`), dans `infrastructure/llm/openai_provider.py` ;
- la factory est **`create_llm_provider(settings)`**, dans `infrastructure/llm/factory.py`. Elle
  accepte exactement trois valeurs — `fake`, `anthropic`, `openai` — et lève
  `LLMProviderConfigError` sur un nom inconnu ou une configuration incomplète. **Il n'existe pas
  de valeur `ollama`** : Ollama, LM Studio et OpenRouter passent par `openai` + `base_url`, ce qui
  est précisément ce que cette ADR prévoyait.

`DefaultSensitiveFilter` a été déplacé de `infrastructure/profiling/` vers
`application/mapping/` pour ne pas faire dépendre deux adaptateurs l'un de l'autre (contrat 5
d'`import-linter`) — voir [`../review-i7.6.md`](../review-i7.6.md).

## Références

`docs/PLAN.md` §2, §5.2 · `docs/ai/providers.md` · `docs/ai/model-switch.md` ·
`backend/agentscope/infrastructure/config/settings.py` · [ADR-0004](0004-contrat-de-mapping.md)
