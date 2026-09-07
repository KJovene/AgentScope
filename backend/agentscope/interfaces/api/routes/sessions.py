from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from agentscope.interfaces.api import fixtures
from agentscope.interfaces.api.schemas.common import Paginated
from agentscope.interfaces.api.schemas.sessions import SessionDetail, SessionRow

router = APIRouter(tags=["sessions"])


@router.get("/sessions", response_model=Paginated[SessionRow])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    sources: list[str] = Query(default=[]),
    agents: list[str] = Query(default=[]),
    models: list[str] = Query(default=[]),
) -> Paginated[SessionRow]:
    limit = min(limit, 200)
    item = SessionRow(**fixtures.SESSION_ROW)
    return Paginated(items=[item], total=1, limit=limit, offset=offset)


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session_detail(session_id: str) -> SessionDetail:
    if session_id != fixtures.SESSION_ROW["id"]:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' introuvable.")
    return SessionDetail(**fixtures.SESSION_DETAIL)
