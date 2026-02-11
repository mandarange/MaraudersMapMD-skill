#!/usr/bin/env python3
import argparse, hashlib, json, os, re, sqlite3
from datetime import datetime, timezone

AI_HINT_PATTERN = re.compile(r"^\s*>\s*\[(AI RULE|AI DECISION|AI TODO|AI CONTEXT)\]")
TOKEN_COUNT_RE = re.compile(r"\S+")


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


def load_sections(doc_root):
    doc_root = os.path.abspath(doc_root)
    doc_id = os.path.basename(doc_root)
    shards_path = os.path.join(doc_root, "shards.json")
    if os.path.isfile(shards_path):
        data = json.loads(_read(shards_path))
        out = []
        for s in data.get("sections") or []:
            legacy_id = s.get("legacy_id") or s.get("legacyId")
            section_id = s.get("id")
            if not legacy_id and section_id and ":" in section_id:
                legacy_id = section_id.split(":", 1)[1]
            if not section_id and legacy_id:
                section_id = f"{doc_id}:{legacy_id}"
            content = s.get("content") or ""
            out.append(
                {
                    "id": section_id,
                    "legacy_id": legacy_id or "",
                    "title": s.get("title"),
                    "content": content,
                    "content_hash": s.get("content_hash")
                    or s.get("contentHash")
                    or _sha(content),
                    "token_count": s.get("token_count")
                    or s.get("tokenCount")
                    or _tok_count(content),
                    "keywords": s.get("keywords", []),
                    "links": s.get("links", []),
                    "ai_hints": s.get("ai_hints")
                    or s.get("aiHints")
                    or [
                        m.group(1)
                        for m in (
                            AI_HINT_PATTERN.match(l) for l in content.splitlines()
                        )
                        if m
                    ],
                    "summary": s.get("summary", ""),
                    "line_range": s.get("line_range") or s.get("lineRange") or [],
                    "file_path": s.get("path")
                    or s.get("file_path")
                    or s.get("filePath"),
                }
            )
        return out
    sections_dir = os.path.join(doc_root, "sections")
    if not os.path.isdir(sections_dir):
        raise FileNotFoundError(f"Missing sections directory: {sections_dir}")
    index_path = os.path.join(doc_root, "index.json")
    index_map = {}
    if os.path.isfile(index_path):
        entries = json.loads(_read(index_path)).get("entries") or []
        index_map = {e.get("slug"): e for e in entries if e.get("slug")}
    out = []
    for fn in sorted(os.listdir(sections_dir)):
        if not fn.endswith(".md"):
            continue
        path = os.path.join(sections_dir, fn)
        content = _read(path)
        base = os.path.splitext(fn)[0]
        slug = base.split("-", 1)[1] if "-" in base else base
        ie = index_map.get(slug, {})
        title = (
            next(
                (
                    l.lstrip("#").strip()
                    for l in content.splitlines()
                    if l.startswith("#")
                ),
                "",
            )
            or ie.get("section")
            or slug
        )
        ai_hints = ie.get("aiHints", []) or [
            m.group(1)
            for m in (AI_HINT_PATTERN.match(l) for l in content.splitlines())
            if m
        ]
        out.append(
            {
                "id": f"{doc_id}:{slug}",
                "legacy_id": slug,
                "title": title,
                "content": content,
                "content_hash": _sha(content),
                "token_count": _tok_count(content),
                "keywords": ie.get("keywords", []),
                "links": ie.get("links", []),
                "ai_hints": ai_hints,
                "summary": ie.get("summary", ""),
                "line_range": ie.get("lineRange", []),
                "file_path": path,
            }
        )
    return out


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
    return [
        os.path.join(map_root, n)
        for n in sorted(os.listdir(map_root))
        if os.path.isdir(os.path.join(map_root, n, "sections"))
    ]


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
