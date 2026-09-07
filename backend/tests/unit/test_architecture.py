"""Garde d'architecture : la règle des dépendances casse les tests, pas seulement le lint.

`make arch` lance déjà `lint-imports` en local. Ces tests rejouent les mêmes contrats
— ceux déclarés dans `pyproject.toml` — pour qu'une PR qui remonte une dépendance
échoue avec le reste de la suite, et donc dans la CI. Voir ADR-0002 et l'issue I0.11.
"""

from __future__ import annotations

import importlib
import sys
import tomllib
from pathlib import Path

import pytest
from importlinter import configuration
from importlinter.application.use_cases import lint_imports

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"

# `lint-imports` fait cet appel avant toute chose : sans lui, les lecteurs de
# configuration ne sont pas enregistrés et `lint_imports` renvoie False pour une
# raison qui n'a rien à voir avec l'architecture.
configuration.configure()


def _importlinter_config() -> dict:
    with PYPROJECT.open("rb") as stream:
        return tomllib.load(stream)["tool"]["importlinter"]


def _check(config_filename: Path) -> bool:
    return lint_imports(config_filename=str(config_filename), cache_dir=None, no_logo=True)


def test_les_contrats_sont_declares() -> None:
    """Un pyproject amputé de ses contrats ne doit pas donner un test vert."""
    config = _importlinter_config()

    assert config["root_package"] == "agentscope"
    # Sans cette option, grimp exclut les paquets tiers du graphe et les contrats
    # « aucun framework » deviennent silencieusement vides.
    assert config["include_external_packages"] is True
    assert len(config["contracts"]) >= 5


def test_la_regle_des_dependances_est_respectee() -> None:
    assert _check(PYPROJECT), (
        "Règle des dépendances violée. Détail : `make arch` (ou `lint-imports` depuis backend/)."
    )


def test_un_import_interdit_serait_bien_detecte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Méta-test : prouve que la garde n'est pas vide.

    On construit un paquet jetable à deux couches, on vérifie qu'il passe, puis on
    fait remonter une dépendance et on vérifie qu'il est refusé. Sans les deux
    moitiés, une configuration devenue inopérante — qui échouerait toujours, ou ne
    verrait plus rien — passerait inaperçue.
    """
    package = tmp_path / "fauxpaquet"
    (package / "domain").mkdir(parents=True)
    (package / "infrastructure").mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "infrastructure" / "__init__.py").write_text("", encoding="utf-8")
    domain_init = package / "domain" / "__init__.py"
    domain_init.write_text("", encoding="utf-8")

    config = tmp_path / "pyproject.toml"
    config.write_text(
        "[tool.importlinter]\n"
        'root_package = "fauxpaquet"\n\n'
        "[[tool.importlinter.contracts]]\n"
        'name = "Sens des dependances"\n'
        'type = "layers"\n'
        'layers = ["fauxpaquet.infrastructure", "fauxpaquet.domain"]\n',
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop("fauxpaquet", None)
    importlib.invalidate_caches()

    assert _check(config), "Le paquet témoin respecte pourtant ses couches."

    domain_init.write_text("import fauxpaquet.infrastructure\n", encoding="utf-8")
    sys.modules.pop("fauxpaquet", None)
    importlib.invalidate_caches()

    assert not _check(config), "Un import remontant de couche n'a pas été détecté."
