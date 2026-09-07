# Fournisseurs IA pris en charge

> Stub — à compléter dans l'issue **I3.14** (WS-ai). Base dans `PLAN.md` §2 (ADR-0005) et §5.2.

À produire ici :

- Interface commune `LLMProvider` (`propose_mapping`, `chat`) et contrat `MappingProposal`.
- Adaptateurs livrés : `FakeLLMProvider` (tests/CI), Anthropic, OpenAI-compatible (OpenAI +
  Ollama / LM Studio via `base_url`).
- Configuration : variables d'environnement `AGENTSCOPE_LLM_*` (provider, model, base_url,
  api_key). Aucun identifiant de modèle en dur, aucune clé dans le dépôt.
- Comment ajouter un fournisseur : un nouvel adaptateur + son raccordement dans la factory,
  sans toucher au code métier ni au moteur d'import.
- Garde-fous : statistiques calculées par le programme ; seuls profils + échantillons filtrés
  sont transmis ; le texte des traces est une donnée, jamais une instruction.
