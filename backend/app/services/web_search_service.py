from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from app.schemas.web_search import WebSearchResult


class WebSearchError(RuntimeError):
    pass


class _DuckDuckGoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[WebSearchResult] = []
        self._in_result_link = False
        self._current_href = ""
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attrs_map = {key: value or "" for key, value in attrs}
        classes = attrs_map.get("class", "")
        href = attrs_map.get("href", "")
        if "result__a" in classes and href:
            self._in_result_link = True
            self._current_href = href
            self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._in_result_link:
            value = data.strip()
            if value:
                self._current_text.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self._in_result_link:
            return
        title = " ".join(self._current_text).strip()
        url = _normalize_duckduckgo_url(self._current_href)
        if title and url and not any(item.url == url for item in self.results):
            self.results.append(WebSearchResult(title=title, url=url))
        self._in_result_link = False
        self._current_href = ""
        self._current_text = []


def _normalize_duckduckgo_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlparse(value)
    query = parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return unquote(query["uddg"][0])
    return value


async def search_web(query: str, limit: int = 5) -> list[WebSearchResult]:
    normalized = query.strip()
    if not normalized:
        return []

    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            response = await client.get(
                "https://duckduckgo.com/html/",
                params={"q": normalized},
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
                    )
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise WebSearchError(f"网页搜索失败：{exc}") from exc

    parser = _DuckDuckGoParser()
    parser.feed(response.text)
    return parser.results[:limit]


def format_search_context(results: list[WebSearchResult]) -> str:
    if not results:
        return "网页搜索未返回可用结果。"
    lines = ["网页搜索结果："]
    for index, item in enumerate(results, start=1):
        lines.append(f"{index}. {item.title}\n   {item.url}")
    return "\n".join(lines)
