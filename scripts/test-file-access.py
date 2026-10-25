#!/usr/bin/env python3
"""HTTP regression tests using disposable files, never the site's database."""
import http.client
import pathlib
import re
import shlex
import shutil
import socket
import subprocess
import tempfile
import time
import unittest


class FileAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.project = pathlib.Path(cls.temp.name)
        cls.root = cls.project / "wp-site"
        (cls.project / "scripts").mkdir()
        shutil.copy(pathlib.Path(__file__).with_name("router.php"), cls.project / "scripts/router.php")
        files = {
            "index.php": "<?php echo 'wordpress-route:' . $_SERVER['REQUEST_URI'];",
            "wp-login.php": "<?php echo 'login';",
            "wp-admin/index.php": "<?php echo 'admin';",
            "wp-config.php": "<?php echo 'PRIVATE';",
            "wp-content/database/.ht.sqlite": "PRIVATE SQLite database",
            "wp-content/database/.ht.sqlite-wal": "PRIVATE WAL",
            "wp-content/database/backup.sqlite": "PRIVATE backup",
            "wp-content/database/export.json": "PRIVATE export",
            "wp-content/database/index.php": "<?php echo 'PRIVATE';",
            "wp-content/uploads/photo.jpg": "public image",
            "wp-content/uploads/site.sqlite": "PRIVATE database copy",
            "wp-content/uploads/site.sqlite-wal": "PRIVATE WAL copy",
            "wp-content/uploads/site.sql": "PRIVATE dump",
            "wp-content/uploads/debug.log": "PRIVATE log",
            "wp-content/uploads/source.PHP": "<?php /* PRIVATE source */",
            "wp-config.php.bak": "PRIVATE backup",
            ".env": "PRIVATE environment",
            "wp-includes/style.css": "public css",
            "wp-includes/app.js": "public js",
            "wp-includes/theme.json": '{"public":true}',
            "wp-content/db.php": "<?php require __DIR__ . '/plugins/sqlite-database-integration/constants.php';",
            "wp-content/plugins/sqlite-database-integration/constants.php": "<?php echo ABSPATH;",
            "wp-content/object-cache.php": "<?php echo 'PRIVATE drop-in';",
            "wp-content/db-error.php": "<?php echo 'PRIVATE drop-in';",
            "wp-includes/broken-library.php": "<?php missing_library_function();",
            "wp-includes/broken-syntax.php": "<?php function (",
            "wp-includes/warning-library.php": "<?php trigger_error('PRIVATE warning', E_USER_WARNING); echo 'safe';",
        }
        for name, content in files.items():
            file = cls.root / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content)
        (cls.project / "style.css").write_text("theme css")
        (cls.project / "css").mkdir()
        (cls.project / "css/theme.css").write_text("theme asset")
        (cls.project / "private.json").write_text("PRIVATE workspace")
        (cls.project / "css/leak.json").symlink_to(cls.project / "private.json")
        (cls.root / "wp-content/themes").mkdir()
        (cls.root / "wp-content/themes/gwt-wordpress").symlink_to(cls.project)
        (cls.root / "alias").symlink_to(cls.root / "wp-content/database")
        (cls.root / "escape").symlink_to(cls.project)
        (cls.root / "wp-content/uploads/alias.json").symlink_to(
            cls.root / "wp-content/uploads/site.sqlite")
        (cls.root / "linked-index").mkdir()
        (cls.root / "linked-index/index.php").symlink_to(cls.root / "wp-config.php")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        # Use the actual tracked startup options, not a separately hardened test
        # command. This catches regressions to PHP's default error display.
        startup = pathlib.Path(__file__).resolve().parent.parent / "start.sh"
        command = startup.read_text().replace("\\\n", " ")
        match = re.search(r"^exec php (.+?) -S ", command, re.MULTILINE)
        if match is None:
            raise RuntimeError("Cannot locate PHP server options in start.sh")
        cls.log = tempfile.TemporaryFile()
        cls.server = subprocess.Popen(
            ["php", "-d", "display_errors=1", "-d", "display_startup_errors=1",
             "-d", "log_errors=0", "-d", "error_log=", *shlex.split(match.group(1)),
             "-S", f"127.0.0.1:{cls.port}", "-t", str(cls.root),
             str(cls.project / "scripts/router.php")],
            stdout=subprocess.DEVNULL, stderr=cls.log,
        )
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", cls.port), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.05)
        else:
            cls.server.terminate()
            raise RuntimeError("PHP test server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait(timeout=5)
        cls.log.close()
        cls.temp.cleanup()

    def request(self, path, method="GET"):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(method, path)
        response = conn.getresponse()
        status, body = response.status, response.read()
        conn.close()
        return status, body

    def test_private_files_are_denied(self):
        paths = [
            "/wp-content/database/", "/wp-content/database/.ht.sqlite",
            "/wp-content/database/.ht.sqlite-wal",
            "/wp-content/database/.ht.sqlite-shm",
            "/wp-content/database/.ht.sqlite-journal",
            "/wp-content/database/backup.sqlite", "/wp-content/database/export.json",
            "/wp-content/database/index.php", "/wp-content/%64atabase/%2eht.sqlite",
            "/wp-content%2fdatabase%2f.ht.sqlite", "/wp-content/database/.ht.sqlite?download=1",
            "/wp-content/database/%252eht.sqlite", "/wp-content\\database\\.ht.sqlite",
            "/wp-config.php", "/wp-config.php/path", "/wp-config.php.bak",
            "/.env", "/%2eenv", "/.git/config",
            "/wp-content/uploads/site.sqlite", "/wp-content/uploads/site.sqlite-wal",
            "/wp-content/uploads/site.sql", "/wp-content/uploads/debug.log",
            "/wp-content/uploads/source.PHP", "/wp-content/uploads/alias.json",
            "/linked-index/",
            "/alias/export.json", "/escape/private.json",
            "/wp-content/themes/gwt-wordpress/private.json",
            "/wp-content/themes/gwt-wordpress/scripts/router.php",
            "/wp-content/themes/gwt-wordpress/css/leak.json",
            "/wp-content/themes/gwt-wordpress/wp-site/wp-content/database/.ht.sqlite",
            "/wp-content/themes/gwt-wordpress/../gwt-wordpress/private.json",
            "/wp-content/themes/gwt-wordpress/%2e%2e/gwt-wordpress/private.json",
            "/wp-content//database//.ht.sqlite",
            "/wp-content/db.php", "/wp-content/%64b.php?download=1",
            "/wp-content//db.php", "//wp-content/db.php", "/wp-content/db.php/path",
            "/wp-content/object-cache.php", "/wp-content/db-error.php",
        ]
        for path in paths:
            for method in ("GET", "HEAD"):
                with self.subTest(path=path, method=method):
                    status, body = self.request(path, method)
                    self.assertIn(status, (400, 403, 404))
                    self.assertNotIn(b"PRIVATE", body)

    def test_unbootstrapped_php_errors_are_logged_not_displayed(self):
        for path, expected_status, expected_body in [
            ("/wp-content/plugins/sqlite-database-integration/constants.php", 500, b""),
            ("/wp-includes/broken-library.php", 500, b""),
            ("/wp-includes/broken-syntax.php", 500, b""),
            ("/wp-includes/warning-library.php", 200, b"safe"),
        ]:
            for method in ("GET", "HEAD"):
                with self.subTest(path=path, method=method):
                    status, body = self.request(path, method)
                    self.assertEqual(status, expected_status)
                    self.assertEqual(body, expected_body if method == "GET" else b"")
        # Logging remains enabled for diagnosis without exposing it over HTTP.
        self.log.seek(0)
        log = self.log.read()
        for diagnostic in (b"Undefined constant", b"missing_library_function",
                           b"PHP Parse error", b"PRIVATE warning"):
            self.assertIn(diagnostic, log)

    def test_range_request_cannot_download_database(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", "/wp-content/database/.ht.sqlite", headers={"Range": "bytes=0-99"})
        response = conn.getresponse()
        self.assertEqual(response.status, 404)
        self.assertNotIn(b"PRIVATE", response.read())
        conn.close()

    def test_wordpress_and_public_assets_remain_available(self):
        for path, expected in [
            ("/", b"wordpress-route:/"),
            ("/sample-post/", b"wordpress-route:/sample-post/"),
            ("/wp-json/", b"wordpress-route:/wp-json/"),
            ("/wp-login.php", b"login"), ("/wp-admin/", b"admin"),
            ("/wp-includes/style.css", b"public css"),
            ("/wp-includes/app.js?ver=1", b"public js"),
            ("/wp-includes/theme.json", b'{"public":true}'),
            ("/wp-content/uploads/photo.jpg", b"public image"),
            ("/wp-content/themes/gwt-wordpress/style.css", b"theme css"),
            ("/wp-content/themes/gwt-wordpress/css/theme.css", b"theme asset"),
        ]:
            with self.subTest(path=path):
                status, body = self.request(path)
                self.assertEqual(status, 200)
                self.assertEqual(body, expected)


if __name__ == "__main__":
    unittest.main()
