"""Audit local links and media references in the rendered portfolio."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attribute = "src" if tag in {"img", "script", "source"} else "href"
        for name, value in attrs:
            if name == attribute and value:
                self.references.append(value)


def main() -> int:
    pages = sorted(DOCS.rglob("*.html"))
    broken: list[tuple[Path, str]] = []
    for page in pages:
        parser = ReferenceParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for reference in parser.references:
            parsed = urlparse(reference)
            if parsed.scheme or parsed.netloc or reference.startswith(("#", "mailto:", "data:")):
                continue
            target = (page.parent / unquote(parsed.path)).resolve()
            if parsed.path.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                broken.append((page.relative_to(DOCS), reference))
    if broken:
        for page, reference in broken:
            print(f"BROKEN {page}: {reference}")
        return 1
    print(f"Link audit passed: {len(pages)} HTML pages, zero broken local references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
