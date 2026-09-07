"""Le domaine ne doit tirer AUCUN paquet tiers (DoD de l'issue I1.1).

Complète la règle statique d'``import-linter`` par une vérification à l'exécution,
dans un interpréteur neuf.
"""

from __future__ import annotations

import subprocess
import sys

_FORBIDDEN_TOP_LEVEL = {
    "fastapi",
    "starlette",
    "sqlalchemy",
    "alembic",
    "pydantic",
    "pydantic_settings",
    "httpx",
    "pandas",
    "pyarrow",
    "duckdb",
    "uvicorn",
}


def test_domain_imports_no_third_party() -> None:
    code = (
        "import sys; import agentscope.domain; "
        "print(','.join(sorted(m.split('.')[0] for m in sys.modules)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    loaded = set(result.stdout.strip().split(","))
    leaked = loaded & _FORBIDDEN_TOP_LEVEL
    assert not leaked, f"Le domaine importe des paquets interdits : {sorted(leaked)}"
