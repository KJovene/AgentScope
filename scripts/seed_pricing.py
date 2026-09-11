#!/usr/bin/env python3
"""Charge la grille tarifaire (``docs/data/model-pricing.json``) dans la stack via
``POST /api/v1/model-pricing`` — idempotent (upsert).

Le dashboard estime alors ``cost_usd`` = ``tokens × tarif`` pour les appels dont
la source ne déclare pas de coût (``docs/data/indicators.md`` §3.4).

    python3 scripts/seed_pricing.py --api http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API = "http://localhost:8000"
DEFAULT_FILE = REPO_ROOT / "docs" / "data" / "model-pricing.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default=DEFAULT_API, help=f"racine API (défaut : {DEFAULT_API})")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="grille JSON")
    args = parser.parse_args()

    if not args.file.exists():
        raise SystemExit(f"grille introuvable : {args.file}")
    prices = json.loads(args.file.read_text(encoding="utf-8")).get("prices", [])
    if not prices:
        raise SystemExit(f"{args.file} : aucune entrée sous `prices`")

    url = f"{args.api.rstrip('/')}/api/v1/model-pricing"
    req = urllib.request.Request(
        url,
        data=json.dumps(prices).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"échec ({exc.code}) : {exc.read().decode('utf-8', 'replace')}"
        ) from exc

    print(f"  grille tarifaire : {result.get('upserted')} modèles chargés", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
