from pydantic import BaseModel, Field


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str | None = None


class WebSearchResponse(BaseModel):
    ok: bool = True
    query: str = Field(min_length=1)
    results: list[WebSearchResult]
