# Fixture TraceLab — attribution

`sample.jsonl` est un extrait du **jeu de données public TraceLab**, redistribué ici au
titre de la licence **CC BY 4.0** qui l'autorise explicitement, à des fins de test.

| | |
| --- | --- |
| Œuvre | TraceLab — SyFI public coding-agent trace |
| Auteurs | SyFI Lab, University of Washington (K. Zhu, M. Jacob, C. Ma, Y. Pan, S. Wang, A. Krishnamurthy, B. Kasikci) |
| Source | https://github.com/uw-syfi/TraceLab — release `v0.0.1`, asset `syfi_coding_trace.jsonl.gz` |
| Licence des données | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Article | *TraceLab: Characterizing Coding Agent Workloads for LLM Serving*, arXiv:2606.30560 |
| Modification | **Extraction seule**, aucune transformation du contenu : 2 sessions sur 4 265 (1 `claude`, 1 `codex`), toutes leurs lignes conservées telles quelles. |

Le jeu amont est déjà **assaini** par ses auteurs : identifiants pseudonymisés, chemins
locaux (`home`, `cwd`, `workdir`, `session_file`) retirés, `tools[].input` supprimé au
profit de `input_chars`. Aucune ré-identification n'est tentée ni permise.

## Régénérer

```bash
make fixtures      # ou :
python scripts/tracelab_extract.py --fetch \
  --modulo 32 --max-sessions-per-provider 1 \
  --out backend/tests/fixtures/tracelab/sample.jsonl
```

Le bilan chiffré de l'extraction est dans `sample.jsonl.meta.json`. La méthode de
sélection et le choix de la version sont documentés dans `data/README.md`.
