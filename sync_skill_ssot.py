#!/usr/bin/env python3
"""
Synchronize MaraudersMap skill artifacts from a single source of truth.

SSOT:
- SKILL.md

Generated artifacts:
- docs/MaraudersMap/<docId>/sections/*.md
- docs/MaraudersMap/<docId>/index.json
- docs/MaraudersMap/<docId>/ai-map.md
- docs/MaraudersMap/<docId>/shards.json
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from shards_to_json import main_with_args as build_shards_with_args


AI_HINT_PATTERN = re.compile(r"^\s*>\s*\[(AI RULE|AI DECISION|AI TODO|AI CONTEXT)\]")
URL_PATTERN = re.compile(r"https?://[^\s)]+")
MD_LINK_PATTERN = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")
CODE_TERM_PATTERN = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class Section:
    title: str
    slug: str
    start_line: int
    end_line: int
    content: str
    filename: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _source_generated_iso(source_path: Path) -> str:
    dt = datetime.fromtimestamp(source_path.stat().st_mtime, tz=timezone.utc)
    return dt.replace(microsecond=0).isoformat()


def _source_generated_date(source_path: Path) -> str:
    dt = datetime.fromtimestamp(source_path.stat().st_mtime, tz=timezone.utc)
    return dt.date().isoformat()


def _token_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "section"


def _parse_sections(skill_text: str) -> list[Section]:
    lines = skill_text.splitlines()
    heading_rows: list[tuple[int, str]] = []
    for idx, line in enumerate(lines, start=1):
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            heading_rows.append((idx, match.group(1).strip()))

    sections: list[Section] = []
    for i, (start_line, title) in enumerate(heading_rows, start=1):
        end_line = heading_rows[i][0] - 1 if i < len(heading_rows) else len(lines)
        content = "\n".join(lines[start_line - 1 : end_line]).rstrip() + "\n"
        slug = _slugify(title)
        filename = f"{i:02d}-{slug}.md"
        sections.append(
            Section(
                title=title,
                slug=slug,
                start_line=start_line,
                end_line=end_line,
                content=content,
                filename=filename,
            )
        )
    return sections


def _extract_links(text: str) -> list[str]:
    links = set(URL_PATTERN.findall(text))
    links.update(MD_LINK_PATTERN.findall(text))
    return sorted(links)


def _extract_ai_hints(text: str) -> list[str]:
    hints: list[str] = []
    for line in text.splitlines():
        match = AI_HINT_PATTERN.match(line)
        if match:
            hints.append(f"[{match.group(1)}]")
    # preserve order, dedupe
    seen = set()
    ordered = []
    for hint in hints:
        if hint not in seen:
            seen.add(hint)
            ordered.append(hint)
    return ordered


def _extract_keywords(title: str, text: str) -> list[str]:
    values: list[str] = []
    values.append(title)
    for item in CODE_TERM_PATTERN.findall(text):
        token = item.strip()
        if token and len(token) <= 80 and not token.startswith("http"):
            values.append(token)
    # include well-known AI hint categories as searchable keywords
    for hint in _extract_ai_hints(text):
        values.append(hint)

    seen = set()
    deduped = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _summary_from_section(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("<!--"):
            continue
        if stripped.startswith("- ") or stripped.startswith("|"):
            continue
        if stripped.startswith("```"):
            continue
        return stripped[:180]
    return "Section content."


def _render_section_file(source_path: Path, section: Section) -> str:
    header = (
        f"<!-- Section from: {source_path} | Lines: "
        f"{section.start_line}-{section.end_line} -->\n\n"
    )
    return header + section.content


def _build_index(source_path: Path, sections: Iterable[Section]) -> dict:
    entries = []
    for section in sections:
        ai_hints = _extract_ai_hints(section.content)
        entries.append(
            {
                "section": section.title,
                "slug": section.slug,
                "lineRange": [section.start_line, section.end_line],
                "tokens": _token_count(section.content),
                "keywords": _extract_keywords(section.title, section.content),
                "links": _extract_links(section.content),
                "summary": _summary_from_section(section.content),
                "aiHints": ai_hints,
            }
        )

    return {
        "version": 1,
        "source": str(source_path),
        "generated": _source_generated_iso(source_path),
        "totalTokens": sum(item["tokens"] for item in entries),
        "entries": entries,
    }


def _render_ai_map(source_path: Path, sections: Iterable[Section]) -> str:
    section_list = list(sections)
    total_tokens = sum(_token_count(section.content) for section in section_list)
    date_str = _source_generated_date(source_path)

    table_rows = [
        f"| {section.title} | {section.start_line}-{section.end_line} | "
        f"{_token_count(section.content)} | {_summary_from_section(section.content)} |"
        for section in section_list
    ]
    details = []
    for section in section_list:
        details.append(f"### {section.title}")
        details.append("")
        details.append(f"- **Lines**: {section.start_line}-{section.end_line}")
        details.append(f"- **Tokens**: {_token_count(section.content)}")
        details.append(f"- **Summary**: {_summary_from_section(section.content)}")
        details.append("")

    return "\n".join(
        [
            f"# AI Map: {source_path}",
            "",
            f"**Source Path**: {source_path}",
            f"**Generated**: {date_str}",
            f"**Total Tokens**: {total_tokens}",
            "",
            "## Document Structure",
            "",
            "| Section | Lines | Tokens | Summary |",
            "|---------|-------|--------|----------|",
            *table_rows,
            "",
            "## Section Details",
            "",
            *details,
        ]
    ).rstrip() + "\n"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _files_differ(path: Path, desired: str) -> bool:
    if not path.exists():
        return True
    return _read_text(path) != desired


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync SKILL.md-derived artifacts to enforce SSOT."
    )
    parser.add_argument(
        "--source",
        default="SKILL.md",
        help="Path to source SKILL.md (single source of truth).",
    )
    parser.add_argument(
        "--doc-id",
        default="SKILL",
        help="Target doc id under docs/MaraudersMap/<docId>.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check mode: exit non-zero if artifacts are out of sync.",
    )
    args = parser.parse_args()

    source_path = Path(args.source).resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source not found: {source_path}")

    repo_root = Path.cwd().resolve()
    doc_root = repo_root / "docs" / "MaraudersMap" / args.doc_id
    sections_dir = doc_root / "sections"
    index_path = doc_root / "index.json"
    ai_map_path = doc_root / "ai-map.md"

    skill_text = _read_text(source_path)
    sections = _parse_sections(skill_text)
    if not sections:
        raise ValueError("No level-2 sections found in source SKILL.md.")

    desired_sections: dict[Path, str] = {}
    for section in sections:
        desired_sections[sections_dir / section.filename] = _render_section_file(
            source_path, section
        )

    desired_index = json.dumps(
        _build_index(source_path, sections), ensure_ascii=False, indent=2
    )
    desired_index += "\n"
    desired_ai_map = _render_ai_map(source_path, sections)

    stale_section_files = []
    if sections_dir.exists():
        for path in sorted(sections_dir.glob("*.md")):
            if path not in desired_sections:
                stale_section_files.append(path)

    changed_paths: list[Path] = []
    for path, desired in desired_sections.items():
        if _files_differ(path, desired):
            changed_paths.append(path)
            if not args.check:
                _write_text(path, desired)

    if _files_differ(index_path, desired_index):
        changed_paths.append(index_path)
        if not args.check:
            _write_text(index_path, desired_index)

    if _files_differ(ai_map_path, desired_ai_map):
        changed_paths.append(ai_map_path)
        if not args.check:
            _write_text(ai_map_path, desired_ai_map)

    if stale_section_files:
        changed_paths.extend(stale_section_files)
        if not args.check:
            for stale in stale_section_files:
                stale.unlink()

    if args.check:
        if changed_paths:
            print("Out-of-sync artifacts detected:")
            for path in changed_paths:
                print(f"- {path.relative_to(repo_root)}")
            return 1
        print("All SKILL artifacts are in sync.")
        return 0

    # Rebuild shards.json after writing sections/index/ai-map.
    build_ret = build_shards_with_args(["--doc-root", str(doc_root)])
    if build_ret != 0:
        return build_ret

    print(f"Synchronized SSOT artifacts from {source_path.relative_to(repo_root)}")
    print(f"Target doc root: {doc_root.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
