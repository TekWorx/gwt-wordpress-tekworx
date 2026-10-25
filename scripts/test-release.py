#!/usr/bin/env python3
"""Verify release contents and install the ZIP into a disposable WordPress site."""
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import zipfile


ROOT = Path(__file__).resolve().parent.parent


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module("release_builder", "build-release.py")


class ReleaseTests(unittest.TestCase):
    def test_package_is_curated_and_reproducible(self):
        with tempfile.TemporaryDirectory() as temp:
            first, second = [Path(temp) / name for name in ("first.zip", "second.zip")]
            builder.build(first)
            builder.build(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertIsNone(archive.testzip())
                names = archive.namelist()
                self.assertIn("gwt-wordpress/style.css", names)
                self.assertIn("gwt-wordpress/INSTALL.md", names)
                self.assertIn("gwt-wordpress/inc/function-initialize.php", names)
                for name in names:
                    parts = Path(name).parts
                    self.assertEqual(parts[0], "gwt-wordpress")
                    self.assertFalse(any(p.startswith(".") or p == ".." for p in parts))
                    self.assertNotIn(parts[1], ("wp-site", "scripts", "start.sh", "DEVELOPMENT.md"))

    def test_rejects_links_and_private_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            regular = root / "asset.txt"
            regular.write_text("fixture")
            link = root / "linked.txt"
            link.symlink_to(regular)
            with self.assertRaises(ValueError):
                builder.check_member(root, link)
            for filename in (".env", "backup.sqlite", "wp-config.php", "secret.key",
                             "database.sqlite-wal", "old.sql.gz", "debug.log", "unexpected.exe"):
                private = root / filename
                private.write_text("fixture")
                with self.subTest(filename=filename), self.assertRaises(ValueError):
                    builder.check_member(root, private)
            regular.write_text("Example forbidden wording")
            with self.assertRaises(ValueError):
                builder.check_member(root, regular, ("example FORBIDDEN wording",))

    @unittest.skipUnless(
        (ROOT / "wp-site/wp-load.php").is_file()
        and (ROOT / "wp-site/wp-content/db.php").is_file(),
        "HTTP integration requires a local WordPress/SQLite test installation; see CONTRIBUTING.md.",
    )
    def test_zip_activates_without_repository_runtime_helpers(self):
        fixture = load_module("release_fixture", "test-credentials.py").CredentialTests
        fixture.setUpClass()
        try:
            package = fixture.root / "theme.zip"
            builder.build(package)
            with zipfile.ZipFile(package) as archive:
                archive.extractall(fixture.site / "wp-content/themes")
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            origin = f"http://127.0.0.1:{port}"
            fixture.env["FIXTURE_SITE_URL"] = origin
            # A standard, independent host config, using only disposable test secrets.
            # No repository URL helper, login plugin, or startup provisioning is used.
            (fixture.site / "wp-config.php").write_text("""<?php
define('DB_NAME', 'unused');
define('DB_USER', 'unused');
define('DB_PASSWORD', '');
define('DB_HOST', 'localhost');
define('DB_CHARSET', 'utf8');
define('DB_COLLATE', '');
$table_prefix = 'wp_';
define('WP_HOME', getenv('FIXTURE_SITE_URL'));
define('WP_SITEURL', getenv('FIXTURE_SITE_URL'));
define('WP_DEBUG', false);
define('WP_DEBUG_DISPLAY', false);
foreach (['AUTH_KEY', 'SECURE_AUTH_KEY', 'LOGGED_IN_KEY', 'NONCE_KEY',
          'AUTH_SALT', 'SECURE_AUTH_SALT', 'LOGGED_IN_SALT', 'NONCE_SALT'] as $key) {
    define($key, hash_hmac('sha256', $key, getenv('SESSION_SECRET')));
}
if (!defined('ABSPATH')) {
    define('ABSPATH', __DIR__ . '/');
}
require_once ABSPATH . 'wp-settings.php';
""")
            shutil.rmtree(fixture.root / "scripts")
            activation = json.loads(fixture.php("""
                require_once ABSPATH . 'wp-admin/includes/theme.php';
                wp_clean_themes_cache();
                $theme = wp_get_theme('gwt-wordpress');
                switch_theme('gwt-wordpress');
                echo json_encode([
                    'exists' => $theme->exists(),
                    'errors' => (bool) $theme->errors(),
                    'active' => get_option('stylesheet'),
                    'version' => $theme->get('Version'),
                ]);
            """))
            self.assertTrue(activation["exists"])
            self.assertFalse(activation["errors"])
            self.assertEqual(activation["active"], "gwt-wordpress")
            self.assertEqual(activation["version"], builder.theme_version())
            # Exercise a real HTTP request, including core redirects and template
            # loading, rather than approximating web-server variables in CLI.
            server = subprocess.Popen(
                ["php", "-S", f"127.0.0.1:{port}", "-t", str(fixture.site)],
                env=fixture.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            try:
                for attempt in range(30):
                    try:
                        with urlopen(origin, timeout=3) as response:
                            self.assertEqual(response.status, 200)
                            html = response.read().decode("utf-8")
                        break
                    except HTTPError:
                        self.fail("The independently installed theme returned an HTTP error.")
                    except URLError:
                        if server.poll() is not None:
                            self.fail("Disposable web server exited before serving the theme.")
                        time.sleep(0.1)
                else:
                    self.fail("Disposable web server did not serve the installed theme.")
                self.assertIn("<html", html.lower())
                self.assertIn("/themes/gwt-wordpress/", html)
            finally:
                server.terminate()
                server.wait(timeout=5)
        finally:
            fixture.tearDownClass()


if __name__ == "__main__":
    unittest.main(verbosity=2)
