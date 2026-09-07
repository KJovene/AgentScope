# Fixture — TraceLab (session Claude Code)

## Source

- Projet : [TraceLab](https://github.com/uw-syfi/TraceLab) — SyFI Lab, University of Washington.
- Fichiers récupérés : `example_sessions/claude/trace.json` et `example_sessions/claude/explanation.md`.
- Commit récupéré : `11b8b14c6005808ab272b3431487066832582414` (branche `main`, daté 2026-08-22).
- Date de récupération : 2026-09-07.
- Licence : Apache-2.0 (voir la licence du dépôt TraceLab pour le détail exact).

## Contenu de ce dossier

| Fichier | Origine | Description |
| --- | --- | --- |
| `trace.json` | copie brute de TraceLab | Segment de 64 enregistrements JSONL, mis en forme lisible par TraceLab avec des séparateurs `===== record NNNN =====`. **Ce n'est pas du JSON/JSONL valide tel quel.** |
| `explanation.md` | copie brute de TraceLab | Documentation du format de trace Claude Code (types de records, accounting des tokens avec cache, etc.). |
| `trace.jsonl` | généré localement | Le même contenu que `trace.json`, nettoyé des séparateurs et des commentaires d'en-tête, une ligne = un objet JSON valide. **C'est ce fichier qu'il faut utiliser comme entrée du `SourceReader`/du pipeline d'import.** |

## Génération de `trace.jsonl`

`trace.jsonl` a été produit à partir de `trace.json` en :
1. retirant les lignes de commentaire (`#...`) en tête de fichier ;
2. découpant sur les séparateurs `===== record NNNN =====` ;
3. réencodant chaque bloc JSON multi-lignes en une seule ligne compacte.

Reproductible avec :

```bash
python3 - <<'EOF'
import json, re

with open("trace.json") as f:
    content = f.read()

blocks = re.split(r"^===== record \d+ =====\s*$", content, flags=re.MULTILINE)
records = [json.loads(b.strip()) for b in blocks if b.strip() and not b.strip().startswith("#")]

with open("trace.jsonl", "w") as out:
    for r in records:
        out.write(json.dumps(r, ensure_ascii=False) + "\n")
EOF
```

64 enregistrements, tous validés individuellement comme JSON.

## Usage

Cet échantillon sert de fixture de test pour :
- écrire et valider le contrat de mapping (§5.1 du plan) contre un format réel de session Claude Code ;
- tester le `SourceReader` JSONL, le profileur de champs, et le use case `AnalyzeUnknownFile` (WS-C).

Ne pas ajouter d'autres fichiers TraceLab dans ce dossier sans mettre à jour ce README (source, version, date).
