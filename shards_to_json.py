#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone


AI_HINT_PATTERN = re.compile(r"^\s*>\s*\[(AI RULE|AI DECISION|AI TODO|AI CONTEXT)\]")
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def _read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _first_heading(text):
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def _token_count(text):
    return len(re.findall(r"\S+", text))


def _tokenize(text):
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def _extract_ai_hints(text):
    hints = []
    for line in text.splitlines():
        match = AI_HINT_PATTERN.match(line)
        if match:
            hints.append(match.group(1))
    return hints


def _build_index_map(index_data):
    entries = index_data.get("entries", [])
    by_slug = {}
    for entry in entries:
        slug = entry.get("slug")
        if slug:
            by_slug[slug] = entry
    return by_slug


def _slug_from_filename(filename):
    base = os.path.splitext(filename)[0]
    if "-" in base:
        return base.split("-", 1)[1]
    return base


def _collect_sections(sections_dir, index_map):
    sections = []
    for filename in sorted(os.listdir(sections_dir)):
        if not filename.endswith(".md"):
            continue
        path = os.path.join(sections_dir, filename)
        content = _read_text(path)
        slug = _slug_from_filename(filename)
        index_entry = index_map.get(slug, {})
        title = _first_heading(content) or index_entry.get("section") or slug
        section = {
            "id": slug,
            "title": title,
            "path": path,
            "content": content,
            "token_count": _token_count(content),
            "content_hash": _sha256(content),
            "keywords": index_entry.get("keywords", []),
            "links": index_entry.get("links", []),
            "ai_hints": index_entry.get("aiHints", []) or _extract_ai_hints(content),
            "summary": index_entry.get("summary", ""),
            "line_range": index_entry.get("lineRange", []),
            "index_tokens": index_entry.get("tokens"),
        }
        sections.append(section)
    return sections


def _build_inverted_index(sections):
    keywords = {}
    links = {}
    ai_hints = {}
    for section in sections:
        slug = section["id"]
        for keyword in section.get("keywords", []):
            keywords.setdefault(keyword, []).append(slug)
        for link in section.get("links", []):
            links.setdefault(link, []).append(slug)
        for hint in section.get("ai_hints", []):
            ai_hints.setdefault(hint, []).append(slug)
    return {"keywords": keywords, "links": links, "ai_hints": ai_hints}


def _build_term_index(sections):
    term_index = {}
    for section in sections:
        slug = section["id"]
        tokens = _tokenize(section.get("content", ""))
        term_freq = {}
        for token in tokens:
            term_freq[token] = term_freq.get(token, 0) + 1
        for term, tf in term_freq.items():
            term_index.setdefault(term, []).append([slug, tf])
    return term_index


def build_shards_json(doc_root):
    sections_dir = os.path.join(doc_root, "sections")
    index_path = os.path.join(doc_root, "index.json")
    ai_map_path = os.path.join(doc_root, "ai-map.md")

    if not os.path.isdir(sections_dir):
        raise FileNotFoundError(f"Missing sections directory: {sections_dir}")

    index_data = {}
    if os.path.isfile(index_path):
        index_data = json.loads(_read_text(index_path))

    index_map = _build_index_map(index_data)
    sections = _collect_sections(sections_dir, index_map)

    term_index = _build_term_index(sections)
    doc_count = len(sections)
    avgdl = 0
    if doc_count:
        avgdl = sum(section["token_count"] for section in sections) / doc_count

    shards = {
        "meta": {
            "doc_id": os.path.basename(doc_root),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_sections": sections_dir,
            "source_index": index_path if os.path.isfile(index_path) else None,
            "source_ai_map": ai_map_path if os.path.isfile(ai_map_path) else None,
            "tool": "shards_to_json.py",
            "schema_version": 1,
            "bm25": {
                "k1": 1.5,
                "b": 0.75,
                "doc_count": doc_count,
                "avgdl": avgdl,
            },
        },
        "sections": sections,
        "index": {
            **_build_inverted_index(sections),
            "term_index": term_index,
        },
    }
    return shards


def main():
    parser = argparse.ArgumentParser(description="Generate shards.json from MaraudersMapMD section packs.")
    parser.add_argument("--doc-root", help="Path to docs/MaraudersMap/<docId>.", required=True)
    parser.add_argument("--output", help="Output path for shards.json (defaults to doc-root/shards.json).")
    args = parser.parse_args()

    doc_root = os.path.abspath(args.doc_root)
    output_path = args.output or os.path.join(doc_root, "shards.json")

    shards = build_shards_json(doc_root)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(shards, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote shards JSON: {output_path}")


if __name__ == "__main__":
    main()
