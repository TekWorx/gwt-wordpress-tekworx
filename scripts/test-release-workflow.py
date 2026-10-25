#!/usr/bin/env python3
"""Exercise the actual upload shell block with mocked GitHub requests."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parent.parent


class UploadWorkflowTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("jq"):
            self.fail("jq is required to test the workflow's real validation.")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "bin").mkdir()
        assets = self.root / "generated-artifacts"
        assets.mkdir()
        (assets / "gwt-wordpress-27.0.6.zip").write_bytes(b"disposable package fixture")
        (assets / "SHA256SUMS.txt").write_text("disposable checksum fixture\n")
        workflow = (ROOT / ".github/workflows/package-release.yml").read_text()
        step = workflow.split("      - name: Upload to the maintainer-created draft\n", 1)[1]
        self.script = textwrap.dedent(step.split("        run: |\n", 1)[1])
        self.draft = {
            "draft": True, "tag_name": "v27.0.6", "assets": [],
            "author": {"type": "User", "login": "TekWorx"},
        }
        self.env = dict(os.environ)
        self.env.update(
            PATH=str(self.root / "bin") + os.pathsep + os.environ["PATH"],
            GH_TOKEN="disposable-test-value", RELEASE_TAG="v27.0.6",
            RELEASE_ID="123", GITHUB_ACTOR="TekWorx",
            GITHUB_REPOSITORY="TekWorx/fixture", FIXTURE_LOG=str(self.root / "requests"),
            FIXTURE_BAD_DIGEST="0",
        )
        self.mock("gh", """
            import json, os, sys
            assert sys.argv[1:] == ["api", "repos/TekWorx/fixture/releases/123"]
            print(os.environ["FIXTURE_DRAFT"])
        """)
        self.mock("curl", """
            import hashlib, json, os, pathlib, sys
            args = sys.argv[1:]
            path = pathlib.Path(args[args.index("--data-binary") + 1][1:])
            assert args[-1] == ("https://uploads.github.com/repos/TekWorx/fixture/"
                                "releases/123/assets?name=" + path.name)
            with open(os.environ["FIXTURE_LOG"], "a") as log:
                log.write(path.name + "\\n")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if os.environ["FIXTURE_BAD_DIGEST"] == "1":
                digest = "wrong"
            print(json.dumps({"state": "uploaded", "digest": "sha256:" + digest}))
        """)

    def mock(self, name, body):
        path = self.root / "bin" / name
        path.write_text("#!" + sys.executable + "\n" + textwrap.dedent(body))
        path.chmod(0o755)

    def run_upload(self):
        self.env["FIXTURE_DRAFT"] = json.dumps(self.draft)
        result = subprocess.run(
            ["bash", "-c", self.script], cwd=self.root, env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        path = self.root / "requests"
        return result.returncode, path.read_text().splitlines() if path.exists() else []

    def assert_rejected(self):
        code, requests = self.run_upload()
        self.assertNotEqual(code, 0)
        self.assertEqual(requests, [])

    def test_owner_draft_uploads_both_assets(self):
        code, requests = self.run_upload()
        self.assertEqual(code, 0)
        self.assertEqual(requests, ["gwt-wordpress-27.0.6.zip", "SHA256SUMS.txt"])

    def test_bot_created_draft_is_rejected(self):
        self.draft["author"] = {"type": "Bot", "login": "github-actions[bot]"}
        self.assert_rejected()

    def test_other_users_draft_is_rejected(self):
        self.draft["author"]["login"] = "another-maintainer"
        self.assert_rejected()

    def test_published_release_is_rejected(self):
        self.draft["draft"] = False
        self.assert_rejected()

    def test_different_version_is_rejected(self):
        self.draft["tag_name"] = "v27.0.5"
        self.assert_rejected()

    def test_existing_assets_are_rejected(self):
        self.draft["assets"] = [{"name": "existing.zip"}]
        self.assert_rejected()

    def test_invalid_release_id_is_rejected(self):
        self.env["RELEASE_ID"] = "123; echo unexpected"
        self.assert_rejected()

    def test_bad_upload_checksum_stops_the_job(self):
        self.env["FIXTURE_BAD_DIGEST"] = "1"
        code, requests = self.run_upload()
        self.assertNotEqual(code, 0)
        self.assertEqual(requests, ["gwt-wordpress-27.0.6.zip"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
