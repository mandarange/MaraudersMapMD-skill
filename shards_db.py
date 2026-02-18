#!/usr/bin/env python3
import argparse, hashlib, json, os, re, sqlite3
from datetime import datetime, timezone

AI_HINT_PATTERN = re.compile(r"^\s*>\s*\[(AI RULE|AI DECISION|AI TODO|AI CONTEXT)\]")
TOKEN_COUNT_RE = re.compile(r"\S+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
REWRITTEN_FILE_RE = re.compile(r"^(?P<base>.+)\.rewritten_v(?P<version>\d+)\.md$")
SLUG_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tok_count(text):
    return len(TOKEN_COUNT_RE.findall(text))


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _jarr(v):
    if v is None:
        v = []
    if not isinstance(v, list):
        v = [v]
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


def _slugify(text):
    tokens = [t.lower() for t in SLUG_TOKEN_RE.findall(text or "")]
    return "-".join(tokens) if tokens else "section"


def _find_latest_rewritten(doc_root, doc_id):
    best = None
    best_ver = -1
    for filename in os.listdir(doc_root):
        match = REWRITTEN_FILE_RE.match(filename)
        if not match:
            continue
        if match.group("base") != doc_id:
            continue
        version = int(match.group("version"))
        if version > best_ver:
            best_ver = version
            best = os.path.join(doc_root, filename)
    if not best:
        raise FileNotFoundError(
            f"Missing rewritten markdown: expected '{doc_id}.rewritten_vN.md' in {doc_root}"
        )
    return best


def _build_section_record(doc_id, legacy_id, title, content, file_path, line_range):
    return {
        "id": f"{doc_id}:{legacy_id}",
        "legacy_id": legacy_id,
        "title": title,
        "content": content,
        "content_hash": _sha(content),
        "token_count": _tok_count(content),
        "keywords": [],
        "links": [],
        "ai_hints": [
            m.group(1)
            for m in (AI_HINT_PATTERN.match(l) for l in content.splitlines())
            if m
        ],
        "summary": "",
        "line_range": line_range,
        "file_path": file_path,
    }


def _sections_from_markdown(doc_id, md_path, text):
    lines = text.splitlines()
    heading_positions = []
    heading_titles = []
    for idx, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if match:
            heading_positions.append(idx)
            heading_titles.append(match.group(2).strip())

    sections = []
    slug_counts = {}

    def next_slug(title):
        base_slug = _slugify(title)
        count = slug_counts.get(base_slug, 0) + 1
        slug_counts[base_slug] = count
        if count == 1:
            return base_slug
        return f"{base_slug}-{count}"

    if not heading_positions:
        return [
            _build_section_record(
                doc_id=doc_id,
                legacy_id="document",
                title="Document",
                content=text,
                file_path=md_path,
                line_range=[1, len(lines) if lines else 1],
            )
        ]

    first_heading = heading_positions[0]
    if first_heading > 0:
        preamble = "\n".join(lines[:first_heading]).strip()
        if preamble:
            sections.append(
                _build_section_record(
                    doc_id=doc_id,
                    legacy_id=next_slug("document-overview"),
                    title="Document Overview",
                    content=preamble,
                    file_path=md_path,
                    line_range=[1, first_heading],
                )
            )

    for idx, start in enumerate(heading_positions):
        end_exclusive = (
            heading_positions[idx + 1]
            if idx + 1 < len(heading_positions)
            else len(lines)
        )
        chunk_lines = lines[start:end_exclusive]
        chunk = "\n".join(chunk_lines).strip()
        title = heading_titles[idx]
        sections.append(
            _build_section_record(
                doc_id=doc_id,
                legacy_id=next_slug(title),
                title=title,
                content=chunk,
                file_path=md_path,
                line_range=[start + 1, end_exclusive],
            )
        )

    return sections


def load_sections(doc_root):
    doc_root = os.path.abspath(doc_root)
    doc_id = os.path.basename(doc_root)
    rewritten_path = _find_latest_rewritten(doc_root, doc_id)
    rewritten_content = _read(rewritten_path)
    return _sections_from_markdown(doc_id, rewritten_path, rewritten_content)


def db_path(map_root):
    return os.path.join(os.path.abspath(map_root), "shards.db")


def connect(db_file):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sections(id TEXT PRIMARY KEY, doc_id TEXT NOT NULL, legacy_id TEXT NOT NULL, title TEXT, content TEXT, content_hash TEXT, token_count INTEGER, keywords TEXT, links TEXT, ai_hints TEXT, summary TEXT, line_range TEXT, file_path TEXT, updated_at TEXT);
CREATE INDEX IF NOT EXISTS idx_sections_doc_id ON sections(doc_id);
CREATE INDEX IF NOT EXISTS idx_sections_content_hash ON sections(content_hash);
CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(title, content, keywords, tokenize='porter unicode61', content='sections', content_rowid='rowid');
CREATE TRIGGER IF NOT EXISTS sections_ai AFTER INSERT ON sections BEGIN INSERT INTO sections_fts(rowid, title, content, keywords) VALUES (new.rowid, new.title, new.content, new.keywords); END;
CREATE TRIGGER IF NOT EXISTS sections_ad AFTER DELETE ON sections BEGIN INSERT INTO sections_fts(sections_fts, rowid, title, content, keywords) VALUES('delete', old.rowid, old.title, old.content, old.keywords); END;
CREATE TRIGGER IF NOT EXISTS sections_au AFTER UPDATE ON sections BEGIN INSERT INTO sections_fts(sections_fts, rowid, title, content, keywords) VALUES('delete', old.rowid, old.title, old.content, old.keywords); INSERT INTO sections_fts(rowid, title, content, keywords) VALUES (new.rowid, new.title, new.content, new.keywords); END;
"""


def init_schema(conn):
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT OR IGNORE INTO meta(key, value) VALUES(?, ?)", ("schema_version", "2")
    )
    conn.execute(
        "INSERT OR IGNORE INTO meta(key, value) VALUES(?, ?)", ("created_at", _utc())
    )
    row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    if not row or row["value"] != "2":
        raise RuntimeError(
            f"Unsupported schema_version={row['value'] if row else None}; expected 2"
        )


def ingest_doc(conn, doc_root):
    doc_root = os.path.abspath(doc_root)
    doc_id = os.path.basename(doc_root)
    now = _utc()
    by_id = {}
    for s in load_sections(doc_root):
        sid = s.get("id")
        if sid:
            by_id[sid] = s
    existing = {
        r["id"]: r["content_hash"]
        for r in conn.execute(
            "SELECT id, content_hash FROM sections WHERE doc_id=?", (doc_id,)
        ).fetchall()
    }
    inserted = skipped = 0
    for sid, s in by_id.items():
        ch = s.get("content_hash")
        if existing.get(sid) == ch:
            skipped += 1
            continue
        conn.execute(
            "INSERT OR REPLACE INTO sections(id, doc_id, legacy_id, title, content, content_hash, token_count, keywords, links, ai_hints, summary, line_range, file_path, updated_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                sid,
                doc_id,
                s.get("legacy_id") or "",
                s.get("title"),
                s.get("content") or "",
                ch,
                int(s.get("token_count") or 0),
                _jarr(s.get("keywords")),
                _jarr(s.get("links")),
                _jarr(s.get("ai_hints")),
                s.get("summary") or "",
                _jarr(s.get("line_range")),
                s.get("file_path"),
                now,
            ),
        )
        inserted += 1
    incoming = sorted(by_id.keys())
    if incoming:
        ph = ",".join(["?"] * len(incoming))
        conn.execute(
            f"DELETE FROM sections WHERE doc_id=? AND id NOT IN ({ph})",
            [doc_id, *incoming],
        )
    else:
        conn.execute("DELETE FROM sections WHERE doc_id=?", (doc_id,))
    return doc_id, len(by_id), inserted, skipped


def discover_docs(map_root):
    map_root = os.path.abspath(map_root)
    docs = []
    for name in sorted(os.listdir(map_root)):
        doc_root = os.path.join(map_root, name)
        if not os.path.isdir(doc_root):
            continue
        try:
            _find_latest_rewritten(doc_root, name)
        except FileNotFoundError:
            continue
        docs.append(doc_root)
    return docs


def print_status(conn):
    q = "SELECT doc_id, COUNT(*) AS sections, COALESCE(SUM(token_count), 0) AS tokens, COALESCE(MAX(updated_at), '') AS last_updated FROM sections GROUP BY doc_id ORDER BY doc_id"
    rows = conn.execute(q).fetchall()
    print("| DocId | Sections | Tokens | Last Updated |")
    print("| --- | ---: | ---: | --- |")
    for r in rows:
        print(
            f"| {r['doc_id']} | {r['sections']} | {r['tokens']} | {r['last_updated']} |"
        )


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Repo-level unified SQLite+FTS5 shards index"
    )
    p.add_argument("--map-root", default="docs/MaraudersMap")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--init", action="store_true")
    g.add_argument("--ingest", metavar="DOC_DIR")
    g.add_argument("--ingest-all", action="store_true")
    g.add_argument("--status", action="store_true")
    g.add_argument("--drop-doc", metavar="DOC_ID")
    a = p.parse_args(argv)
    db_file = db_path(a.map_root)
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    conn = connect(db_file)
    try:
        with conn:
            init_schema(conn)
        if a.init:
            print(f"Initialized DB: {db_file}")
            return 0
        if a.drop_doc:
            with conn:
                conn.execute("DELETE FROM sections WHERE doc_id=?", (a.drop_doc,))
            print(f"Dropped doc: {a.drop_doc}")
            return 0
        if a.status:
            print_status(conn)
            return 0
        if a.ingest:
            with conn:
                doc_id, n, ins, skip = ingest_doc(conn, a.ingest)
            print(f"Ingested {doc_id}: {n} sections (upserted={ins}, skipped={skip})")
            return 0
        if a.ingest_all:
            total_docs = total_sections = 0
            for doc_root in discover_docs(a.map_root):
                with conn:
                    _, n, _, _ = ingest_doc(conn, doc_root)
                total_docs += 1
                total_sections += n
            print(f"Ingested all docs: {total_docs} docs, {total_sections} sections")
            return 0
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
