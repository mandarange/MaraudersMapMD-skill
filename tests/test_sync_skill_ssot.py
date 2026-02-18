import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "sync_skill_ssot.py"


class TestSyncSkillSsot(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.repo = Path(self.tmpdir)
        (self.repo / "docs" / "MaraudersMap" / "SKILL" / "sections").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: demo",
                    "description: demo",
                    "---",
                    "",
                    "## When to Use",
                    "",
                    "- line one",
                    "",
                    "## Procedure",
                    "",
                    "Do this.",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        # stale section should be removed by sync
        (self.repo / "docs" / "MaraudersMap" / "SKILL" / "sections" / "99-stale.md").write_text(
            "stale\n", encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )

    def test_sync_writes_expected_artifacts(self):
        result = self._run("--source", "SKILL.md", "--doc-id", "SKILL")
        self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)

        doc_root = self.repo / "docs" / "MaraudersMap" / "SKILL"
        self.assertTrue((doc_root / "sections" / "01-when-to-use.md").exists())
        self.assertTrue((doc_root / "sections" / "02-procedure.md").exists())
        self.assertFalse((doc_root / "sections" / "99-stale.md").exists())
        self.assertTrue((doc_root / "index.json").exists())
        self.assertTrue((doc_root / "ai-map.md").exists())
        self.assertTrue((doc_root / "shards.json").exists())

    def test_check_detects_out_of_sync_files(self):
        # initial sync
        sync_result = self._run("--source", "SKILL.md", "--doc-id", "SKILL")
        self.assertEqual(sync_result.returncode, 0, msg=sync_result.stderr + sync_result.stdout)

        # mutate source and expect check to fail
        with (self.repo / "SKILL.md").open("a", encoding="utf-8") as f:
            f.write("## Checklist\n\n- added\n")

        check_result = self._run("--source", "SKILL.md", "--doc-id", "SKILL", "--check")
        self.assertEqual(check_result.returncode, 1)
        self.assertIn("Out-of-sync artifacts detected", check_result.stdout)


if __name__ == "__main__":
    unittest.main()
