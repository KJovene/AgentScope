#!/usr/bin/env python3
"""Convertit un export de session "pi" (pi-coding-agent) vers un JSONL plat.

Le format "pi" (https://github.com/badlogic/pi-mono) journalise une session comme
une chaîne d'événements reliés par ``parentId`` : seul l'événement racine
(``type: "session"``) porte l'identifiant réel de la session ; tous les
événements suivants (``model_change``, ``message``, ...) n'ont **aucun** champ
qui la référence directement.

Le normaliseur d'AgentScope traite chaque ligne JSONL indépendamment (aucune
mémoire entre les lignes) : il a besoin qu'**une** clé de session soit présente
sur chaque ligne, comme le fait TraceLab/SWE-chat avec `session_id`. Ce script
fait exactement ça : il résout, pour chaque événement, l'identifiant de sa
session en remontant la chaîne `parentId` jusqu'à l'événement racine, puis
réécrit chaque ligne avec un champ `session_id` ajouté.

Tolérant aux lignes cassées (JSON illisible) : elles sont comptées et ignorées
plutôt que de faire échouer toute la conversion — pratique face à un export
partiellement corrompu (copié-collé incomplet, troncature, ...).

Usage
-----
    python scripts/convert_pi_session_jsonl.py session.jsonl --out session.flat.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_records(path: Path) -> tuple[list[dict[str, Any]], int]:
    records: list[dict[str, Any]] = []
    skipped = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if not isinstance(obj, dict):
                skipped += 1
                continue
            records.append(obj)
    return records, skipped


def _resolve_session_ids(records: list[dict[str, Any]]) -> dict[int, str | None]:
    """Associe l'index de chaque enregistrement à l'id de session résolu.

    Remonte `parentId` jusqu'à un événement `type == "session"`. Si la chaîne
    est incomplète (parent manquant, boucle), retombe sur le premier événement
    `session` vu dans le fichier — en pratique un fichier "pi" ne contient
    qu'une session.
    """
    by_id = {rec["id"]: rec for rec in records if isinstance(rec.get("id"), str)}
    fallback_session_id = next(
        (
            rec["id"]
            for rec in records
            if rec.get("type") == "session" and isinstance(rec.get("id"), str)
        ),
        None,
    )

    resolved: dict[int, str | None] = {}
    for index, rec in enumerate(records):
        if rec.get("type") == "session" and isinstance(rec.get("id"), str):
            resolved[index] = rec["id"]
            continue

        seen: set[str] = set()
        current = rec
        session_id: str | None = None
        while True:
            parent_id = current.get("parentId")
            if not isinstance(parent_id, str) or parent_id in seen:
                break
            seen.add(parent_id)
            parent = by_id.get(parent_id)
            if parent is None:
                break
            if parent.get("type") == "session":
                session_id = parent.get("id")
                break
            current = parent
        resolved[index] = session_id or fallback_session_id

    return resolved


def convert(input_path: Path, output_path: Path) -> tuple[int, int, int]:
    """Retourne (lignes écrites, lignes ignorées car illisibles, lignes sans session résolue)."""
    records, skipped = _load_records(input_path)
    session_ids = _resolve_session_ids(records)

    unresolved = 0
    with output_path.open("w", encoding="utf-8") as out:
        for index, rec in enumerate(records):
            session_id = session_ids.get(index)
            if session_id is None:
                unresolved += 1
                continue
            enriched = {**rec, "session_id": session_id}
            out.write(json.dumps(enriched, ensure_ascii=False) + "\n")

    return len(records) - unresolved, skipped, unresolved


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", type=Path, help="Fichier session.jsonl au format pi")
    parser.add_argument("--out", type=Path, required=True, help="Fichier JSONL plat à écrire")
    args = parser.parse_args()

    written, skipped, unresolved = convert(args.input, args.out)
    print(f"{written} ligne(s) écrite(s) dans {args.out}", file=sys.stderr)
    if skipped:
        print(f"{skipped} ligne(s) illisible(s) ignorée(s)", file=sys.stderr)
    if unresolved:
        print(f"{unresolved} ligne(s) sans session résolue, ignorée(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
