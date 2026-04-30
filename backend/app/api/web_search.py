from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import get_current_user
from app.schemas.auth import UserPublic
from app.schemas.web_search import WebSearchResponse
from app.services.web_search_service import WebSearchError, search_web

router = APIRouter(prefix="/search", tags=["web-search"])


@router.get("/web", response_model=WebSearchResponse)
async def web_search(
    q: str = Query(min_length=1),
    current_user: UserPublic = Depends(get_current_user),
) -> WebSearchResponse:
    try:
        results = await search_web(q)
    except WebSearchError as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "message": str(exc)}) from exc
    return WebSearchResponse(query=q, results=results)
