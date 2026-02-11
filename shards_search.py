#!/usr/bin/env python3
import argparse
import json
import math
import re
import sqlite3
import sys


def load_shards(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_section_map(shards):
    section_map = {}
    for section in shards.get("sections", []):
        section_map[section.get("id")] = section
        if "legacy_id" in section:
            section_map[section["legacy_id"]] = section
    return section_map


def search_by_keyword(shards, section_map, keyword):
    matches = []
    index = shards.get("index", {}).get("keywords", {})
    for slug in index.get(keyword, []):
        section = section_map.get(slug)
        if section:
            matches.append(section)
    return matches


def search_by_regex(shards, pattern, flags=0):
    regex = re.compile(pattern, flags)
    results = []
    for section in shards.get("sections", []):
        if regex.search(section.get("content", "")):
            results.append(section)
    return results


def search_by_bm25(shards, section_map, query):
    term_index = shards.get("index", {}).get("term_index", {})
    bm25_meta = shards.get("meta", {}).get("bm25", {})
    k1 = bm25_meta.get("k1", 1.5)
    b = bm25_meta.get("b", 0.75)
    doc_count = bm25_meta.get("doc_count", len(section_map))
    avgdl = bm25_meta.get("avgdl", 0) or 1

    query_terms = [term.lower() for term in re.findall(r"[A-Za-z0-9]+", query)]
    scores = {}

    for term in query_terms:
        postings = term_index.get(term, [])
        df = len(postings)
        if df == 0:
            continue
        idf = math.log(1 + (doc_count - df + 0.5) / (df + 0.5))
        for slug, tf in postings:
            section = section_map.get(slug)
            if not section:
                continue
            dl = section.get("token_count", 0) or 1
            denom = tf + k1 * (1 - b + b * (dl / avgdl))
            score = idf * (tf * (k1 + 1) / denom)
            scores[slug] = scores.get(slug, 0) + score

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [section_map[slug] for slug, _score in ranked]


def _warn(message):
    print(f"Warning: {message}", file=sys.stderr)


def _check_db_schema(db_path, expected_version="2"):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()
        version = row[0] if row else None
    except sqlite3.OperationalError:
        version = None
    finally:
        conn.close()

    if version != expected_version:
        _warn(
            f"DB schema_version={version} (expected {expected_version}); results may be unreliable"
        )


def search_db_keyword(db_path, keyword, doc_filter=None, limit=5):
    """Search by exact keyword match in the keywords JSON array stored in sections table."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM sections WHERE EXISTS (SELECT 1 FROM json_each(keywords) WHERE json_each.value = ?)"
    params = [keyword]
    if doc_filter:
        query += " AND doc_id = ?"
        params.append(doc_filter)
    query += " LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_db_bm25(db_path, query_text, doc_filter=None, limit=5):
    """FTS5 full-text search with BM25 ranking. bm25() returns NEGATIVE scores (lower=better)."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    fts_query = """
        SELECT s.*, bm25(sections_fts, 10.0, 1.0, 5.0) AS rank
        FROM sections_fts
        JOIN sections s ON s.rowid = sections_fts.rowid
        WHERE sections_fts MATCH ?
    """
    params = [query_text]
    if doc_filter:
        fts_query += " AND s.doc_id = ?"
        params.append(doc_filter)
    fts_query += " ORDER BY rank LIMIT ?"
    params.append(limit)
    rows = conn.execute(fts_query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_db_regex(db_path, pattern, doc_filter=None, limit=5, flags=0):
    """Regex search across section content in DB."""
    import re as re_mod

    regex = re_mod.compile(pattern, flags)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM sections"
    params = []
    if doc_filter:
        query += " WHERE doc_id = ?"
        params.append(doc_filter)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    results = [dict(r) for r in rows if regex.search(r["content"] or "")]
    return results[:limit]


def _print_text(results, show_content=False):
    for r in results:
        section_id = r.get("id", "?")
        title = r.get("title", "")
        print(f"[{section_id}] {title}")
        if show_content:
            content = r.get("content", "")
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"  {preview}")


def _print_json(results, show_content=False):
    import json

    output = []
    for r in results:
        entry = {"id": r.get("id"), "title": r.get("title")}
        if show_content:
            entry["content"] = r.get("content", "")
        if "rank" in r:
            entry["score"] = r["rank"]
        output.append(entry)
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Search shards.json for fast lookup (or use --db for SQLite/FTS5)."
    )
    parser.add_argument("--shards", help="Path to shards.json.")
    parser.add_argument("--db", help="Path to SQLite DB (read-only).")
    parser.add_argument("--keyword", help="Exact keyword from shards index.")
    parser.add_argument(
        "--regex", help="Regex pattern to search within section content."
    )
    parser.add_argument("--query", help="Free-text query for BM25 ranking.")
    parser.add_argument("--doc", help="Filter results by doc id (DB backend only).")
    parser.add_argument("--top", type=int, default=5, help="Max results to print.")
    parser.add_argument(
        "--full", action="store_true", help="Include content in output."
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    args = parser.parse_args()

    if bool(args.shards) == bool(args.db):
        raise SystemExit("Provide exactly one of --shards or --db.")

    if args.db:
        _check_db_schema(args.db)

        if args.keyword:
            results = search_db_keyword(
                args.db, args.keyword, doc_filter=args.doc, limit=args.top
            )
        elif args.regex:
            results = search_db_regex(
                args.db,
                args.regex,
                doc_filter=args.doc,
                limit=args.top,
                flags=re.IGNORECASE,
            )
        elif args.query:
            results = search_db_bm25(
                args.db, args.query, doc_filter=args.doc, limit=args.top
            )
        else:
            raise SystemExit("Provide --keyword, --regex, or --query.")
    else:
        shards = load_shards(args.shards)
        section_map = build_section_map(shards)

        if args.keyword:
            results = search_by_keyword(shards, section_map, args.keyword)
        elif args.regex:
            results = search_by_regex(shards, args.regex, flags=re.IGNORECASE)
        elif args.query:
            results = search_by_bm25(shards, section_map, args.query)
        else:
            raise SystemExit("Provide --keyword, --regex, or --query.")

    results = results[: args.top]
    if args.format == "json":
        _print_json(results, show_content=args.full)
    else:
        _print_text(results, show_content=args.full)


if __name__ == "__main__":
    main()
