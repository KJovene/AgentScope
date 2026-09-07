"""Point d'entrée de l'application : ``uvicorn agentscope.main:app``."""

from agentscope.interfaces.api.app import create_app

app = create_app()
