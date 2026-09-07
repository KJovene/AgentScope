"""Exporte la spécification OpenAPI vers un fichier JSON.

Utilisé par le frontend pour générer son client typé (``npm run api:generate``).
Lancer : ``python -m agentscope.interfaces.api.openapi`` ou ``agentscope-openapi``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from agentscope.interfaces.api.app import create_app

DEFAULT_OUTPUT = Path("openapi.json")


def export(output: Path = DEFAULT_OUTPUT) -> Path:
    spec = create_app().openapi()
    output.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    path = export(target)
    print(f"OpenAPI écrit dans {path.resolve()}")


if __name__ == "__main__":
    main()
