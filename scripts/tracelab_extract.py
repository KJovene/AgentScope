#!/usr/bin/env python3
"""Récupère l'extrait TraceLab épinglé et en tire un échantillon déterministe.

Issue I0.10 (WS-platform). Le dataset complet (357 161 rounds, 617 Mio décompressés)
n'est pas commité : ce script le télécharge, vérifie son empreinte publiée, puis en
extrait un sous-ensemble reproductible.

Méthode de sélection — voir `data/README.md` :

* on travaille **par session entière** (toutes les lignes d'une session retenue sont
  conservées) : une session tronquée fausserait la normalisation et les indicateurs ;
* une session est retenue si ``sha1(session_id) % modulo == 0`` — déterministe, sans
  graine, rejouable à l'identique par n'importe qui depuis le même fichier épinglé ;
* la sélection est appliquée **séparément par provider** (`claude`, `codex`) afin que
  les deux soient représentés quelle que soit la taille de l'échantillon.

Exemples
--------
    python scripts/tracelab_extract.py --fetch --modulo 32 \
        --out data/tracelab/extract-dev.jsonl

    python scripts/tracelab_extract.py --modulo 32 --max-sessions-per-provider 2 \
        --out backend/tests/fixtures/tracelab/sample.jsonl
"""

from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

# Release épinglée. Voir data/README.md pour la justification du choix de version.
RELEASE_TAG = "v0.0.1"
ASSET_NAME = "syfi_coding_trace.jsonl.gz"
ASSET_URL = f"https://github.com/uw-syfi/TraceLab/releases/download/{RELEASE_TAG}/{ASSET_NAME}"
ASSET_SHA256 = "9d265eae69a31cae203848bea936f018148eed7ca8bf56050c5abe96da0b4e6b"

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = REPO_ROOT / "data" / "tracelab" / ASSET_NAME


def fetch(archive: Path) -> None:
    """Télécharge l'archive épinglée si elle manque, puis vérifie son empreinte."""
    if not archive.exists():
        archive.parent.mkdir(parents=True, exist_ok=True)
        print(f"Téléchargement de {ASSET_URL}", file=sys.stderr)
        with urllib.request.urlopen(ASSET_URL) as response, archive.open("wb") as out:
            while chunk := response.read(1 << 20):
                out.write(chunk)

    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        while chunk := stream.read(1 << 20):
            digest.update(chunk)
    if digest.hexdigest() != ASSET_SHA256:
        raise SystemExit(
            f"Empreinte SHA256 inattendue pour {archive}.\n"
            f"  attendue : {ASSET_SHA256}\n  obtenue  : {digest.hexdigest()}\n"
            "Supprimez le fichier et relancez avec --fetch."
        )
    print(f"{archive} — SHA256 conforme à la release {RELEASE_TAG}.", file=sys.stderr)


def _display_path(path: Path) -> str:
    """Chemin relatif au dépôt quand c'est possible, absolu sinon."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def is_selected(session_id: str, modulo: int) -> bool:
    return int(hashlib.sha1(session_id.encode("utf-8")).hexdigest(), 16) % modulo == 0


def extract(archive: Path, out: Path, modulo: int, cap: int | None) -> dict[str, Any]:
    """Écrit l'échantillon et renvoie son bilan chiffré."""
    kept_sessions: dict[str, set[str]] = collections.defaultdict(set)
    rounds: collections.Counter[str] = collections.Counter()
    tools: collections.Counter[str] = collections.Counter()
    models: collections.Counter[str] = collections.Counter()
    users: set[str] = set()
    total_rows = 0
    written = 0

    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with (
        gzip.open(archive, "rt", encoding="utf-8") as source,
        out.open("w", encoding="utf-8", newline="\n") as sink,
    ):
        for line in source:
            total_rows += 1
            row = json.loads(line)
            provider, session_id = row["provider"], row["session_id"]

            if session_id not in kept_sessions[provider]:
                if not is_selected(session_id, modulo):
                    continue
                if cap is not None and len(kept_sessions[provider]) >= cap:
                    continue
                kept_sessions[provider].add(session_id)

            sink.write(line if line.endswith("\n") else line + "\n")
            written += 1
            rounds[provider] += 1
            tools[provider] += len(row.get("tools") or [])
            models[row.get("model") or "?"] += 1
            if row.get("user"):
                users.add(row["user"])

    return {
        "source": {
            "release": RELEASE_TAG,
            "asset": ASSET_NAME,
            "sha256": ASSET_SHA256,
            "rows_scanned": total_rows,
        },
        "selection": {
            "rule": "sha1(session_id) % modulo == 0",
            "modulo": modulo,
            "max_sessions_per_provider": cap,
        },
        "extract": {
            "path": _display_path(out),
            "rounds": written,
            "bytes": out.stat().st_size,
            "sessions": {p: len(s) for p, s in sorted(kept_sessions.items())},
            "rounds_by_provider": dict(sorted(rounds.items())),
            "tool_records_by_provider": dict(sorted(tools.items())),
            "distinct_models": len(models),
            "distinct_users": len(users),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--archive", type=Path, default=DEFAULT_ARCHIVE,
        help="archive .jsonl.gz épinglée (défaut : data/tracelab/)",
    )
    parser.add_argument("--fetch", action="store_true", help="télécharge l'archive si elle manque")
    parser.add_argument("--out", type=Path, required=True, help="fichier JSONL à écrire")
    parser.add_argument(
        "--modulo", type=int, default=32, help="1 session retenue sur N (défaut : 32)"
    )
    parser.add_argument(
        "--max-sessions-per-provider", type=int, default=None,
        help="plafonne le nombre de sessions retenues par provider",
    )
    args = parser.parse_args()

    if args.fetch:
        fetch(args.archive)
    elif not args.archive.exists():
        raise SystemExit(f"{args.archive} absent — relancez avec --fetch.")

    report = extract(args.archive, args.out, args.modulo, args.max_sessions_per_provider)
    args.out.with_suffix(args.out.suffix + ".meta.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
