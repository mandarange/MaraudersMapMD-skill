# pyright: basic
# pyright: reportArgumentType=false
# pyright: reportCallIssue=false
# pyright: reportOptionalSubscript=false
# pyright: reportIndexIssue=false

import unittest
import json
import os
import sys
import tempfile
import shutil


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shards_to_json import (
    build_shards_json,
    main_with_args,
    _make_section_id,
    _sha256,
    _first_heading,
    _token_count,
    _tokenize,
    _slug_from_filename,
)
from shards_search import (
    build_section_map,
    search_by_keyword,
    search_by_regex,
    search_by_bm25,
)


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "sample-doc")


class TestDeterministicIds(unittest.TestCase):
    def test_make_section_id_format(self):
        self.assertEqual(_make_section_id("SKILL", "intro"), "SKILL:intro")

    def test_make_section_id_different_docs(self):
        id1 = _make_section_id("DOC_A", "section1")
        id2 = _make_section_id("DOC_B", "section1")
        self.assertNotEqual(id1, id2)

    def test_build_shards_has_composite_ids(self):
        shards = build_shards_json(FIXTURES_DIR)
        for section in shards["sections"]:
            self.assertIn(":", section["id"])
            self.assertEqual(section["id"], f"sample-doc:{section['legacy_id']}")


class TestShardingBoundaries(unittest.TestCase):
    def test_sections_count(self):
        shards = build_shards_json(FIXTURES_DIR)
        self.assertEqual(len(shards["sections"]), 2)

    def test_section_titles(self):
        shards = build_shards_json(FIXTURES_DIR)
        titles = [s["title"] for s in shards["sections"]]
        self.assertIn("Introduction", titles)
        self.assertIn("Details", titles)

    def test_keywords_in_index(self):
        shards = build_shards_json(FIXTURES_DIR)
        kw_index = shards["index"]["keywords"]
        self.assertIn("parsing", kw_index)
        self.assertIn("configuration", kw_index)

    def test_term_index_populated(self):
        shards = build_shards_json(FIXTURES_DIR)
        term_index = shards["index"]["term_index"]
        self.assertGreater(len(term_index), 0)

    def test_bm25_metadata(self):
        shards = build_shards_json(FIXTURES_DIR)
        bm25 = shards["meta"]["bm25"]
        self.assertEqual(bm25["doc_count"], 2)
        self.assertGreater(bm25["avgdl"], 0)

    def test_empty_sections_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sections_dir = os.path.join(tmpdir, "sections")
            os.makedirs(sections_dir)
            shards = build_shards_json(tmpdir)
            self.assertEqual(len(shards["sections"]), 0)

    def test_missing_sections_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError):
                build_shards_json(tmpdir)


class TestContentHash(unittest.TestCase):
    def test_sha256_deterministic(self):
        h1 = _sha256("hello world")
        h2 = _sha256("hello world")
        self.assertEqual(h1, h2)

    def test_sha256_changes(self):
        h1 = _sha256("hello")
        h2 = _sha256("world")
        self.assertNotEqual(h1, h2)

    def test_section_content_hash_populated(self):
        shards = build_shards_json(FIXTURES_DIR)
        for section in shards["sections"]:
            self.assertIsNotNone(section["content_hash"])
            self.assertEqual(len(section["content_hash"]), 64)


class TestSchemaVersion(unittest.TestCase):
    def test_schema_version_is_2(self):
        shards = build_shards_json(FIXTURES_DIR)
        self.assertEqual(shards["meta"]["schema_version"], 2)

    def test_id_format_field(self):
        shards = build_shards_json(FIXTURES_DIR)
        self.assertEqual(shards["meta"]["id_format"], "docId:slug")


class TestIncrementalRebuild(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.doc_root = os.path.join(self.tmpdir, "test-doc")
        shutil.copytree(FIXTURES_DIR, self.doc_root)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_basic_build(self):
        ret = main_with_args(["--doc-root", self.doc_root])
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.doc_root, "shards.json")))

    def test_manifest_created_on_build(self):
        main_with_args(["--doc-root", self.doc_root])
        manifest_path = os.path.join(self.doc_root, ".manifest.json")
        self.assertTrue(os.path.isfile(manifest_path))
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(manifest["schema_version"], 2)

    def test_changed_no_changes(self):
        main_with_args(["--doc-root", self.doc_root])
        ret = main_with_args(["--doc-root", self.doc_root, "--changed"])
        self.assertEqual(ret, 0)

    def test_changed_detects_modification(self):
        main_with_args(["--doc-root", self.doc_root])
        section_path = os.path.join(self.doc_root, "sections", "01-intro.md")
        with open(section_path, "a", encoding="utf-8") as f:
            f.write("\nNew content added for testing.\n")
        ret = main_with_args(["--doc-root", self.doc_root, "--changed"])
        self.assertEqual(ret, 0)

    def test_dry_run_no_write(self):
        ret = main_with_args(["--doc-root", self.doc_root, "--dry-run"])
        self.assertEqual(ret, 0)
        self.assertFalse(os.path.isfile(os.path.join(self.doc_root, "shards.json")))

    def test_force_rebuild(self):
        main_with_args(["--doc-root", self.doc_root])
        ret = main_with_args(["--doc-root", self.doc_root, "--changed", "--force"])
        self.assertEqual(ret, 0)

    def test_report_flag(self):
        ret = main_with_args(["--doc-root", self.doc_root, "--report"])
        self.assertEqual(ret, 0)


class TestSearchIntegration(unittest.TestCase):
    def setUp(self):
        self.shards = build_shards_json(FIXTURES_DIR)
        self.section_map = build_section_map(self.shards)

    def test_keyword_search(self):
        results = search_by_keyword(self.shards, self.section_map, "parsing")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["legacy_id"], "intro")

    def test_regex_search(self):
        results = search_by_regex(self.shards, r"BM25")
        self.assertGreater(len(results), 0)

    def test_bm25_search(self):
        results = search_by_bm25(self.shards, self.section_map, "configuration options")
        self.assertGreater(len(results), 0)

    def test_section_map_composite_and_legacy(self):
        self.assertIn("sample-doc:intro", self.section_map)
        self.assertIn("intro", self.section_map)


class TestHelperFunctions(unittest.TestCase):
    def test_first_heading(self):
        self.assertEqual(_first_heading("# Hello\nworld"), "Hello")
        self.assertEqual(_first_heading("no heading"), "")

    def test_token_count(self):
        self.assertEqual(_token_count("one two three"), 3)
        self.assertEqual(_token_count(""), 0)

    def test_tokenize(self):
        tokens = _tokenize("Hello World 123")
        self.assertEqual(tokens, ["hello", "world", "123"])

    def test_slug_from_filename(self):
        self.assertEqual(_slug_from_filename("01-intro.md"), "intro")
        self.assertEqual(_slug_from_filename("overview.md"), "overview")
