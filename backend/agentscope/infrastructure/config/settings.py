"""Configuration centralisée, lue depuis l'environnement.

Aucune valeur secrète par défaut. Préfixe des variables : ``AGENTSCOPE_``.
Le cœur métier ne lit jamais l'environnement directement — il reçoit ces valeurs
via l'injection de dépendances (I0.5 / I4.10).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENTSCOPE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Métadonnées applicatives.
    app_name: str = "AgentScope API"
    debug: bool = False

    # Base de données — SQLite par défaut (reproductible depuis un clone),
    # PostgreSQL via configuration (cf. ADR-0003).
    database_url: str = "sqlite:///./agentscope.db"
    db_echo: bool = False

    # Origines autorisées pour le frontend. `NoDecode` : la valeur brute de l'env
    # (CSV) arrive au validateur au lieu d'être décodée en JSON par pydantic-settings.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    # Fournisseur IA interchangeable (cf. ADR-0005). "fake" = aucun appel externe.
    llm_provider: str = "fake"
    llm_model: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Accepte une liste d'origines séparées par des virgules."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Instance unique, mémoïsée pour la durée du process."""
    return Settings()
