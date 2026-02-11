#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
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


def _make_section_id(doc_id, slug):
    """Return deterministic composite ID: 'docId:slug'."""
    return f"{doc_id}:{slug}"


def _collect_sections(sections_dir, index_map, doc_id):
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
            "id": _make_section_id(doc_id, slug),
            "legacy_id": slug,
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
        slug = section["legacy_id"]
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
        slug = section["legacy_id"]
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
    doc_id = os.path.basename(doc_root)

    if not os.path.isdir(sections_dir):
        raise FileNotFoundError(f"Missing sections directory: {sections_dir}")

    index_data = {}
    if os.path.isfile(index_path):
        index_data = json.loads(_read_text(index_path))

    index_map = _build_index_map(index_data)
    sections = _collect_sections(sections_dir, index_map, doc_id)

    term_index = _build_term_index(sections)
    doc_count = len(sections)
    avgdl = 0
    if doc_count:
        avgdl = sum(section["token_count"] for section in sections) / doc_count

    shards = {
        "meta": {
            "doc_id": doc_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_sections": sections_dir,
            "source_index": index_path if os.path.isfile(index_path) else None,
            "source_ai_map": ai_map_path if os.path.isfile(ai_map_path) else None,
            "tool": "shards_to_json.py",
            "schema_version": 2,
            "id_format": "docId:slug",
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


def _atomic_write_json(path, data):
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    fd, temp_path = tempfile.mkstemp(
        dir=os.path.dirname(path) or ".",
        prefix=".shards-",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temp_path, path)
    except BaseException:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _load_manifest(doc_root):
    manifest_path = os.path.join(doc_root, ".manifest.json")
    if not os.path.isfile(manifest_path):
        return None
    try:
        manifest = json.loads(_read_text(manifest_path))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(manifest, dict):
        return None
    if manifest.get("schema_version") != 2:
        return None
    if not isinstance(manifest.get("sections"), dict):
        manifest["sections"] = {}
    return manifest


def _save_manifest(doc_root, sections, index_hash):
    manifest_sections = {}
    for section in sections:
        section_id = section.get("id")
        content_hash = section.get("content_hash")
        path = section.get("path")
        if not section_id or not content_hash:
            continue
        file_path = None
        if path:
            try:
                file_path = os.path.relpath(path, doc_root)
            except ValueError:
                file_path = path
        manifest_sections[section_id] = {
            "content_hash": content_hash,
            "file": file_path,
        }

    data = {
        "schema_version": 2,
        "sections": manifest_sections,
        "index_hash": index_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = os.path.join(doc_root, ".manifest.json")
    _atomic_write_json(manifest_path, data)


def _detect_changes(sections, manifest):
    prev_sections = {}
    if isinstance(manifest, dict):
        prev_sections = manifest.get("sections") or {}

    current = {s.get("id"): s.get("content_hash") for s in sections if s.get("id")}
    prev = {
        k: (v.get("content_hash") if isinstance(v, dict) else None)
        for k, v in prev_sections.items()
        if k
    }

    added = []
    changed = []
    unchanged = []
    for section_id, content_hash in current.items():
        if section_id not in prev:
            added.append(section_id)
            continue
        if prev.get(section_id) != content_hash:
            changed.append(section_id)
        else:
            unchanged.append(section_id)

    removed = [section_id for section_id in prev.keys() if section_id not in current]

    added.sort()
    changed.sort()
    removed.sort()
    unchanged.sort()
    return {
        "added": added,
        "changed": changed,
        "removed": removed,
        "unchanged": unchanged,
    }


def main_with_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate shards.json from MaraudersMapMD section packs."
    )
    parser.add_argument(
        "--doc-root", help="Path to docs/MaraudersMap/<docId>.", required=True
    )
    parser.add_argument(
        "--output",
        help="Output path for shards.json (defaults to doc-root/shards.json).",
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Skip rebuild when section content hashes match .manifest.json.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="With --changed, force a rebuild even if no changes detected.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing any files.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print a change summary after rebuild.",
    )
    args = parser.parse_args(argv)

    doc_root = os.path.abspath(args.doc_root)
    output_path = args.output or os.path.join(doc_root, "shards.json")

    doc_id = os.path.basename(doc_root)
    manifest_path = os.path.join(doc_root, ".manifest.json")
    index_path = os.path.join(doc_root, "index.json")

    manifest = None
    change_info = None
    index_changed = False
    current_index_hash = None
    scanned_sections = None

    should_scan = args.changed or args.report or args.dry_run
    if should_scan:
        sections_dir = os.path.join(doc_root, "sections")
        if not os.path.isdir(sections_dir):
            raise FileNotFoundError(f"Missing sections directory: {sections_dir}")

        index_data = {}
        if os.path.isfile(index_path):
            try:
                index_data = json.loads(_read_text(index_path))
            except json.JSONDecodeError:
                index_data = {}

        index_map = _build_index_map(index_data)
        scanned_sections = _collect_sections(sections_dir, index_map, doc_id)
        print(f"[{doc_id}] {len(scanned_sections)} sections scanned", file=sys.stderr)

        manifest = _load_manifest(doc_root)
        change_info = _detect_changes(scanned_sections, manifest)

        if os.path.isfile(index_path):
            current_index_hash = _sha256(_read_text(index_path))
        prev_index_hash = manifest.get("index_hash") if manifest else None
        index_changed = prev_index_hash != current_index_hash

    def _print_change_details():
        if not change_info:
            return
        added = change_info["added"]
        changed = change_info["changed"]
        removed = change_info["removed"]
        parts = [
            f"added={len(added)}",
            f"changed={len(changed)}",
            f"removed={len(removed)}",
        ]
        if index_changed:
            parts.append("index=changed")
        print(f"[{doc_id}] Changes detected: " + ", ".join(parts), file=sys.stderr)
        if added:
            print(f"[{doc_id}] Added: " + ", ".join(added), file=sys.stderr)
        if changed:
            print(f"[{doc_id}] Changed: " + ", ".join(changed), file=sys.stderr)
        if removed:
            print(f"[{doc_id}] Removed: " + ", ".join(removed), file=sys.stderr)

    if args.changed:
        has_section_changes = bool(
            change_info
            and (
                change_info["added"] or change_info["changed"] or change_info["removed"]
            )
        )
        has_changes = has_section_changes or index_changed
        if not has_changes and not args.force:
            print(f"[{doc_id}] No changes detected.", file=sys.stderr)
            if args.report:
                output_size = (
                    os.path.getsize(output_path)
                    if os.path.isfile(output_path)
                    else None
                )
                size_str = (
                    f"{output_size} bytes" if output_size is not None else "(missing)"
                )
                print(
                    f"[{doc_id}] Report: sections={len(scanned_sections) if scanned_sections is not None else 0}, added=0, changed=0, removed=0, output_size={size_str}",
                    file=sys.stderr,
                )
            return 0

        if args.force and not has_changes:
            print(
                f"[{doc_id}] No changes detected, but --force set; rebuilding.",
                file=sys.stderr,
            )
        else:
            _print_change_details()

    if args.dry_run:
        if args.changed and change_info is not None:
            added = len(change_info["added"])
            changed = len(change_info["changed"])
            removed = len(change_info["removed"])
            print(
                f"[{doc_id}] Dry run: would rebuild (added={added}, changed={changed}, removed={removed}{', index=changed' if index_changed else ''}).",
                file=sys.stderr,
            )
        shards = build_shards_json(doc_root)
        content = json.dumps(shards, ensure_ascii=False, indent=2) + "\n"
        output_size = len(content.encode("utf-8"))
        if args.report:
            added_count = len(change_info["added"]) if change_info else 0
            changed_count = len(change_info["changed"]) if change_info else 0
            removed_count = len(change_info["removed"]) if change_info else 0
            print(
                f"[{doc_id}] Report (dry run): sections={len(shards.get('sections', []))}, added={added_count}, changed={changed_count}, removed={removed_count}, output_size={output_size} bytes",
                file=sys.stderr,
            )
        print(f"Dry run: would write shards JSON: {output_path}")
        print(f"Dry run: would write manifest: {manifest_path}")
        return 0

    shards = build_shards_json(doc_root)
    _atomic_write_json(output_path, shards)
    print(f"Wrote shards JSON: {output_path}")

    if current_index_hash is None and os.path.isfile(index_path):
        current_index_hash = _sha256(_read_text(index_path))
    _save_manifest(doc_root, shards.get("sections", []), current_index_hash)

    if args.report:
        if change_info is None:
            manifest_before = _load_manifest(doc_root)
            change_info = _detect_changes(shards.get("sections", []), manifest_before)
        output_size = (
            os.path.getsize(output_path) if os.path.isfile(output_path) else None
        )
        size_str = f"{output_size} bytes" if output_size is not None else "(missing)"
        print(
            f"[{doc_id}] Report: sections={len(shards.get('sections', []))}, added={len(change_info['added'])}, changed={len(change_info['changed'])}, removed={len(change_info['removed'])}, output_size={size_str}",
            file=sys.stderr,
        )
    return 0


def main():
    sys.exit(main_with_args())


if __name__ == "__main__":
    main()
