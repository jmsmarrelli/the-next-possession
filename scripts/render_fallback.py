"""Render the Quarto-flavored portfolio with Pandoc when Quarto cache is unavailable."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PANDOC = Path("/Applications/quarto/bin/tools/pandoc")
INCLUDE = re.compile(r"\{\{<\s+include\s+([^>]+?)\s*>\}\}")
FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TITLE = re.compile(r'^title:\s*["\']?(.+?)["\']?\s*$', re.MULTILINE)

PAGES = [
    Path("index.qmd"),
    Path("methodology.qmd"),
    Path("data.qmd"),
    *sorted(path.relative_to(ROOT) for path in (ROOT / "projects").glob("*/index.qmd")),
]


def expand_includes(source: Path, text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        include_path = (source.parent / match.group(1).strip()).resolve()
        return include_path.read_text(encoding="utf-8")

    return INCLUDE.sub(replace, text)


def navigation(depth: int) -> str:
    prefix = "../" * depth
    return f"""<nav class="fallback-nav">
<a class="brand" href="{prefix}index.html">THE NEXT POSSESSION</a>
<a href="{prefix}index.html#explore-the-portfolio">Projects</a>
<a href="{prefix}methodology.html">Methods</a>
<a href="{prefix}data.html">Data</a>
</nav>"""


def footer() -> str:
    return """<footer class="fallback-footer">Built with Python, R, Quarto source, and public basketball data. Educational portfolio; not affiliated with the NBA or San Antonio Spurs.</footer>"""


def copy_artifacts() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "assets", DOCS / "assets", dirs_exist_ok=True)
    shutil.copy2(ROOT / "SOURCES.md", DOCS / "SOURCES.md")
    shutil.copy2(ROOT / "VALIDATION.md", DOCS / "VALIDATION.md")
    for project in sorted((ROOT / "projects").iterdir()):
        if not project.is_dir():
            continue
        target = DOCS / "projects" / project.name
        target.mkdir(parents=True, exist_ok=True)
        for pattern in ("*.csv", "*.py", "*.R", "README.md"):
            for source in project.glob(pattern):
                shutil.copy2(source, target / source.name)


def render_page(relative: Path) -> None:
    source = ROOT / relative
    destination = DOCS / relative.with_suffix(".html")
    destination.parent.mkdir(parents=True, exist_ok=True)
    depth = len(relative.parent.parts)
    css = "../" * depth + "assets/styles.css"
    source_content = source.read_text(encoding="utf-8")
    front_matter = FRONT_MATTER.match(source_content)
    title_match = TITLE.search(front_matter.group(1) if front_matter else "")
    title = title_match.group(1) if title_match else "The Next Possession"
    content = FRONT_MATTER.sub("", source_content, count=1)
    if relative != Path("index.qmd"):
        content = f"# {title}\n\n{content}"
    content = expand_includes(source, content)
    with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as temporary:
        temporary_path = Path(temporary)
        expanded = temporary_path / "page.qmd"
        before = temporary_path / "before.html"
        after = temporary_path / "after.html"
        expanded.write_text(content, encoding="utf-8")
        before.write_text(navigation(depth), encoding="utf-8")
        after.write_text(footer(), encoding="utf-8")
        subprocess.run(
            [
                str(PANDOC),
                str(expanded),
                "--standalone",
                "--from=markdown+yaml_metadata_block+raw_html",
                "--to=html5",
                "--metadata",
                f"pagetitle={title}",
                "--css",
                css,
                "--include-before-body",
                str(before),
                "--include-after-body",
                str(after),
                "--resource-path",
                str(ROOT),
                "--output",
                str(destination),
            ],
            check=True,
        )


def main() -> None:
    if not PANDOC.exists():
        raise FileNotFoundError(f"Pandoc not found at {PANDOC}")
    (ROOT / ".cache").mkdir(parents=True, exist_ok=True)
    copy_artifacts()
    for page in PAGES:
        render_page(page)
    print(f"Rendered {len(PAGES)} pages to {DOCS}")


if __name__ == "__main__":
    main()
