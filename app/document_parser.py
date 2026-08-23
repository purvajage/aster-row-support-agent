from pathlib import Path
from typing import Any

from app.models import RetrievedPassage, Source


KNOWLEDGE_BASE_DIR = (
    Path(__file__).resolve().parent.parent / "knowledge-base"
)


def _parse_front_matter(
    lines: list[str],
) -> tuple[dict[str, Any], int]:
    """
    Parse simple YAML-style front matter.

    Returns:
        metadata, index of the first line after the front matter.
    """
    if not lines or lines[0].strip() != "---":
        return {}, 0

    metadata: dict[str, Any] = {}
    end_index = None

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

        line = lines[index].strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)

        key = key.strip()
        value = value.strip()

        metadata[key] = _parse_metadata_value(value)

    if end_index is None:
        return {}, 0

    return metadata, end_index + 1


def _parse_metadata_value(value: str) -> Any:
    """Convert simple YAML-like values into useful Python values."""
    if value.lower() == "true":
        return True

    if value.lower() == "false":
        return False

    if value.lower() in {"null", "none"}:
        return None

    if value.startswith("[") and value.endswith("]"):
        items = value[1:-1].split(",")
        return [
            item.strip().strip("'\"")
            for item in items
            if item.strip()
        ]

    return value.strip("'\"")


def _build_sections(
    lines: list[str],
    start_index: int,
) -> list[tuple[str, str]]:
    """
    Split a Markdown document into heading-based sections.

    Each section contains the text under its most recent heading.
    """
    sections: list[tuple[str, str]] = []

    current_heading = "Document"
    current_lines: list[str] = []

    for line in lines[start_index:]:
        stripped = line.strip()

        if stripped.startswith("#"):
            heading_level = len(stripped) - len(
                stripped.lstrip("#")
            )

            if heading_level <= 3:
                if current_lines:
                    text = "\n".join(current_lines).strip()

                    if text:
                        sections.append(
                            (current_heading, text)
                        )

                current_heading = stripped.lstrip("#").strip()
                current_lines = []
                continue

        current_lines.append(line)

    if current_lines:
        text = "\n".join(current_lines).strip()

        if text:
            sections.append((current_heading, text))

    return sections


def parse_document(path: Path) -> list[RetrievedPassage]:
    """Parse one Markdown knowledge-base document."""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    metadata, content_start = _parse_front_matter(lines)

    sections = _build_sections(
        lines,
        content_start,
    )

    passages: list[RetrievedPassage] = []

    for heading, text in sections:
        passages.append(
            RetrievedPassage(
                text=text,
                source=Source(
                    filename=path.name,
                    heading=heading,
                ),
                metadata=metadata.copy(),
                score=0.0,
            )
        )

    return passages


def load_knowledge_base(
    directory: Path = KNOWLEDGE_BASE_DIR,
) -> list[RetrievedPassage]:
    """Load all Markdown documents from the knowledge base."""
    passages: list[RetrievedPassage] = []

    for path in sorted(directory.glob("*.md")):
        passages.extend(parse_document(path))

    return passages