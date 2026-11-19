"""Read-only acquisition adapter for the public LM Studio Model Catalog.

The public catalog is a website, distinct from the local LM Studio /api/v1/models
inventory. This adapter reads same-origin model pages and never downloads weights.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from typing import Any, Callable, Iterable

DEFAULT_CATALOG_URL = "https://lmstudio.ai/models"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_PAGE_BYTES = 3 * 1024 * 1024
DEFAULT_MAX_MODELS = 100
ALLOWED_HOST = "lmstudio.ai"


class LMStudioCatalogError(ValueError):
    """Raised when the public LM Studio catalog cannot be safely parsed."""


@dataclass(frozen=True, slots=True)
class LMStudioCatalogEntry:
    key: str
    display_name: str
    details_url: str
    summary: str
    availability: tuple[str, ...]
    capability_tags: tuple[str, ...]
    parameter_sizes: tuple[str, ...]
    max_context: str | None
    minimum_memory: str | None
    download_count: str | None
    star_count: str | None
    updated: str | None
    license_text: str | None
    artifact_links: tuple[dict[str, str], ...]
    detail_text: str
    publisher: str | None = None
    model_type: str = "catalog_model"
    architecture: str | None = None
    quantization: dict[str, Any] | None = None
    size_bytes: int | None = None
    params_string: str | None = None
    max_context_length: int | None = None
    format: str | None = None
    capabilities: dict[str, Any] | None = None
    reasoning: dict[str, Any] | None = None
    has_vision_adapter: bool | None = None
    description: str | None = None
    variants: tuple[str, ...] = ()
    selected_variant: str | None = None
    loaded_instances: tuple[dict[str, Any], ...] = ()


class _CatalogLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._active: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            href = dict(attrs).get("href") or ""
            self._active.append({"href": href, "text": ""})

    def handle_data(self, data: str) -> None:
        for item in self._active:
            item["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._active:
            item = self._active.pop()
            if item["href"]:
                self.links.append((item["href"], " ".join(item["text"].split())))


class _DetailText(HTMLParser):
    BLOCKS = {"p", "li", "h1", "h2", "h3", "h4", "tr", "section"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self.anchors: list[dict[str, str]] = []
        self._current: list[str] = []
        self._anchor: dict[str, str] | None = None
        self._ignored = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._ignored += 1
            return
        if self._ignored:
            return
        if tag in self.BLOCKS:
            self._flush()
        if tag == "a":
            href = dict(attrs).get("href") or ""
            self._anchor = {"href": href, "text": ""}

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self._ignored:
            self._ignored -= 1
            return
        if self._ignored:
            return
        if tag == "a" and self._anchor is not None:
            self._anchor["text"] = " ".join(self._anchor["text"].split())
            if self._anchor["href"]:
                self.anchors.append(self._anchor)
            self._anchor = None
        if tag in self.BLOCKS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._ignored:
            return
        text = " ".join(data.split())
        if text:
            self._current.append(text)
            if self._anchor is not None:
                self._anchor["text"] += " " + text

    def _flush(self) -> None:
        line = " ".join(" ".join(self._current).split())
        if line and (not self.lines or self.lines[-1] != line):
            self.lines.append(line)
        self._current = []

    def result(self) -> tuple[str, tuple[dict[str, str], ...]]:
        self._flush()
        return "\n".join(self.lines), tuple(self.anchors)


def _safe_catalog_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise LMStudioCatalogError("catalog URL contains an invalid port") from exc
    if (parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST
            or parsed.username or parsed.password or port not in (None, 443)
            or parsed.query or parsed.fragment):
        raise LMStudioCatalogError("only clean HTTPS URLs on lmstudio.ai are permitted")
    return urllib.parse.urlunsplit(("https", ALLOWED_HOST, parsed.path or "/models", "", ""))


def _fetch_page(url: str, timeout: float, max_bytes: int) -> str:
    request = urllib.request.Request(url, headers={"Accept": "text/html", "User-Agent": "UAIE-Prime/0.1"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname != ALLOWED_HOST:
                raise LMStudioCatalogError("catalog redirected outside the approved LM Studio origin")
            raw = response.read(max_bytes + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LMStudioCatalogError(f"catalog request failed: {type(exc).__name__}") from exc
    if len(raw) > max_bytes:
        raise LMStudioCatalogError("catalog page exceeds the configured response limit")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LMStudioCatalogError("catalog page is not valid UTF-8") from exc


def _extract_card_value(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _build_entry(slug: str, detail_url: str, card_text: str, detail_html: str) -> LMStudioCatalogEntry:
    parser = _DetailText()
    parser.feed(detail_html)
    detail_text, anchors = parser.result()
    lines = detail_text.splitlines()
    title = next((line for line in lines if line), slug.replace("-", " ").title())
    summary = next((line for line in lines[1:] if len(line) > 35), card_text)
    combined = card_text + "\n" + detail_text
    lower = combined.casefold()
    tags = tuple(tag for tag, needles in (
        ("tool_use", ("tool use", "tool calling", "tool calls")),
        ("reasoning", ("reasoning",)),
        ("vision", ("vision", "visual understanding")),
        ("audio", ("audio",)),
        ("video", ("video",)),
    ) if any(needle in lower for needle in needles))
    availability = tuple(value for value, pattern in (("local", r"\\blocal\\s*[—-]\\s*available"), ("cloud", r"\\bcloud\\s*[—-]\\s*available"))
                         if re.search(pattern, card_text, flags=re.IGNORECASE))
    params = tuple(dict.fromkeys(re.findall(r"\b\d+(?:\.\d+)?\s*(?:B|M)\b", combined, flags=re.I)))
    context = _extract_card_value(combined, r"\b(\d+(?:\.\d+)?\s*[KMB])\s*(?:token\s+)?context")
    memory = _extract_card_value(combined, r"(?:at least\s+)?(\d+(?:\.\d+)?\s*(?:GB|MB|TB))\s+(?:of\s+)?RAM")
    downloads = _extract_card_value(card_text, r"(\d+(?:\.\d+)?\s*[KMB]?)\s+downloads?")
    stars = _extract_card_value(card_text, r"(\d+(?:\.\d+)?\s*[KMB]?)\s+stars?")
    updated = _extract_card_value(card_text, r"(updated\s+[^.]+)")
    license_text = None
    for index, line in enumerate(lines):
        if line.casefold() == "license":
            license_text = lines[index + 1] if index + 1 < len(lines) else None
            break
    artifact_links = []
    for anchor in anchors:
        absolute = urllib.parse.urljoin(detail_url, anchor["href"])
        parsed = urllib.parse.urlsplit(absolute)
        if parsed.scheme in {"https"} and parsed.hostname in {"huggingface.co", ALLOWED_HOST}:
            if absolute != detail_url:
                artifact_links.append({"text": anchor["text"], "url": absolute})
    return LMStudioCatalogEntry(
        key=slug, display_name=title, details_url=detail_url, summary=summary,
        availability=availability, capability_tags=tags, parameter_sizes=params,
        max_context=context, minimum_memory=memory, download_count=downloads,
        star_count=stars, updated=updated, license_text=license_text,
        artifact_links=tuple(artifact_links), detail_text=detail_text,
        capabilities={tag: True for tag in tags},
        description=summary,
    )


def discover_catalog(
    catalog_url: str = DEFAULT_CATALOG_URL,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_page_bytes: int = DEFAULT_MAX_PAGE_BYTES,
    max_models: int = DEFAULT_MAX_MODELS,
    fetcher: Callable[[str, float, int], str] | None = None,
) -> tuple[LMStudioCatalogEntry, ...]:
    """Discover model detail pages from the official LM Studio catalog page."""
    if timeout <= 0 or timeout > 60:
        raise LMStudioCatalogError("timeout must be greater than 0 and no more than 60 seconds")
    if max_page_bytes < 1 or max_page_bytes > 8 * 1024 * 1024:
        raise LMStudioCatalogError("max_page_bytes must be between 1 byte and 8 MiB")
    if not 1 <= max_models <= 500:
        raise LMStudioCatalogError("max_models must be between 1 and 500")
    start_url = _safe_catalog_url(catalog_url)
    get_page = fetcher or _fetch_page
    catalog_html = get_page(start_url, timeout, max_page_bytes)
    parser = _CatalogLinks()
    parser.feed(catalog_html)
    found: dict[str, str] = {}
    for href, card_text in parser.links:
        absolute = urllib.parse.urljoin(start_url, href)
        parsed = urllib.parse.urlsplit(absolute)
        if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
            continue
        match = re.fullmatch(r"/models/([a-zA-Z0-9][a-zA-Z0-9._-]*)/?", parsed.path)
        if not match:
            continue
        slug = match.group(1)
        if slug.casefold() == "models":
            continue
        found.setdefault(slug, card_text)
    if not found:
        raise LMStudioCatalogError("no model detail links found; catalog markup may have changed")
    if len(found) > max_models:
        raise LMStudioCatalogError("catalog model count exceeds the configured safety limit")
    entries = []
    for slug, card_text in sorted(found.items()):
        detail_url = f"https://{ALLOWED_HOST}/models/{slug}"
        detail_html = get_page(detail_url, timeout, max_page_bytes)
        entries.append(_build_entry(slug, detail_url, card_text, detail_html))
    return tuple(entries)


def assimilate_public_catalog(
    engine: Any,
    catalog_url: str = DEFAULT_CATALOG_URL,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_page_bytes: int = DEFAULT_MAX_PAGE_BYTES,
    max_models: int = DEFAULT_MAX_MODELS,
    fetcher: Callable[[str, float, int], str] | None = None,
    afi_adapter: Any | None = None,
) -> tuple[tuple[Any, ...], tuple[Any, ...]]:
    """Persist public catalog entries and AFI PRIME profiles; never fetch model weights."""
    from .afi import AFIPrimeFusionAdapter

    entries = discover_catalog(catalog_url, timeout, max_page_bytes, max_models, fetcher)
    afi = afi_adapter or AFIPrimeFusionAdapter()
    catalog_records = []
    afi_records = []
    for entry in entries:
        key = urllib.parse.quote(entry.key, safe="._-")
        catalog_records.append(engine.ingest_object(asdict(entry), source=entry.details_url))
        profile = afi.fuse_model(entry)
        afi_records.append(engine.ingest_object(
            afi.to_record(profile), source=f"afi-prime://lm-studio-public-catalog/{key}"))
    return tuple(catalog_records), tuple(afi_records)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only UAIE acquisition from the public LM Studio Model Catalog")
    parser.add_argument("--catalog-url", default=os.environ.get("LM_STUDIO_CATALOG_URL", DEFAULT_CATALOG_URL))
    parser.add_argument("--max-models", type=int, default=DEFAULT_MAX_MODELS)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)
    try:
        entries = discover_catalog(args.catalog_url, timeout=args.timeout, max_models=args.max_models)
    except LMStudioCatalogError as exc:
        print(f"UAIE LM Studio catalog error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"source": _safe_catalog_url(args.catalog_url), "read_only": True,
                      "entries": [asdict(entry) for entry in entries]},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
