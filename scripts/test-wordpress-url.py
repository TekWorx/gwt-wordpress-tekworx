#!/usr/bin/env python3
"""Canonical URL regression tests. No emails are sent and no options are saved."""
import base64
import json
import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
HELPER = ROOT / "scripts/wordpress-site-url.php"
INSTALLER = ROOT / "scripts/configure-wordpress-url.php"


class WordPressUrlTests(unittest.TestCase):
    def run_config(self, environment=None, server=None, wordpress=False):
        env = os.environ.copy()
        for key in ("WORDPRESS_SITE_URL", "APP_ENV"):
            env.pop(key, None)
        env["APP_ENV"] = "development"
        for key, value in (environment or {}).items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        headers = {
            "HTTP_HOST": "attacker.invalid",
            "HTTP_X_FORWARDED_HOST": "attacker.invalid",
            "HTTP_X_FORWARDED_PROTO": "http",
            "HTTP_X_FORWARDED_SSL": "off",
            "HTTP_X_FORWARDED_PORT": "80",
            "HTTP_FORWARDED": "host=attacker.invalid;proto=http",
            "REQUEST_URI": "/",
            "SERVER_PORT": "80",
        }
        headers.update(server or {})
        encoded = base64.b64encode(json.dumps(headers).encode()).decode()
        bootstrap = ROOT / "wp-site/wp-load.php" if wordpress else HELPER
        code = (
            f"$_SERVER = json_decode(base64_decode('{encoded}'), true);"
            "define('WP_USE_THEMES', false);"
            f"require '{bootstrap}';"
            "$result = ['home' => WP_HOME, 'site' => WP_SITEURL,"
            "'host' => $_SERVER['HTTP_HOST'], 'https' => $_SERVER['HTTPS'],"
            "'forwarded' => isset($_SERVER['HTTP_X_FORWARDED_PROTO'])"
            " || isset($_SERVER['HTTP_X_FORWARDED_HOST']) || isset($_SERVER['HTTP_FORWARDED'])];"
        )
        if wordpress:
            code += (
                "$result['home_url'] = home_url('/');"
                "$result['site_url'] = site_url('/');"
                "$result['reset_url'] = network_site_url("
                "'wp-login.php?action=rp&key=test-token&login=test-user', 'login');"
            )
        code += "echo json_encode($result);"
        return subprocess.run(
            ["php", "-r", code], env=env, text=True, capture_output=True, timeout=30
        )

    def test_production_url_is_pinned_despite_forged_headers(self):
        for headers in (
            {},
            {"HTTP_HOST": "attacker.invalid:443", "HTTPS": "off"},
            {"HTTP_HOST": "trusted.example@attacker.invalid", "HTTP_X_FORWARDED_PROTO": "https"},
            {"HTTP_HOST": "attacker.invalid, trusted.example", "HTTP_FORWARDED": "proto=https"},
        ):
            with self.subTest(headers=headers):
                result = self.run_config(
                    {"APP_ENV": "production", "WORDPRESS_SITE_URL": "https://trusted.example/"},
                    headers,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                values = json.loads(result.stdout)
                self.assertEqual(values["home"], "https://trusted.example")
                self.assertEqual(values["site"], "https://trusted.example")
                self.assertEqual(values["host"], "trusted.example")
                self.assertEqual(values["https"], "on")
                self.assertFalse(values["forwarded"])

    def test_preview_uses_configured_url_not_host(self):
        result = self.run_config({"WORDPRESS_SITE_URL": "https://preview.example.test"})
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertEqual(values["home"], "https://preview.example.test")
        self.assertEqual(values["https"], "on")

    def test_local_http_ignores_forged_https_headers(self):
        result = self.run_config(server={
            "HTTPS": "on", "HTTP_X_FORWARDED_PROTO": "https",
            "HTTP_X_FORWARDED_SSL": "on", "HTTP_X_FORWARDED_PORT": "443",
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertEqual(values["home"], "http://localhost:5000")
        self.assertEqual(values["https"], "off")
        self.assertEqual(values["host"], "localhost:5000")

    def test_production_fails_closed_for_missing_or_invalid_url(self):
        for url in (
            None, "", "http://trusted.example", "javascript:alert(1)",
            "https://user:password@trusted.example", "https://trusted.example/?host=evil",
            "https://trusted.example/#evil", "https://trusted.example\n",
            "https://trusted.example\\@evil.invalid",
        ):
            with self.subTest(url=url):
                env = {"APP_ENV": "production"}
                if url is not None:
                    env["WORDPRESS_SITE_URL"] = url
                result = self.run_config(env)
                self.assertNotEqual(result.returncode, 0)

    def test_missing_or_unknown_environment_fails_closed(self):
        for environment in (None, "", "staging", "developmnt"):
            with self.subTest(environment=environment):
                result = self.run_config({"APP_ENV": environment})
                self.assertNotEqual(result.returncode, 0)

    def test_wordpress_home_site_and_password_reset_url_are_pinned(self):
        result = self.run_config(
            {"APP_ENV": "production", "WORDPRESS_SITE_URL": "https://trusted.example"},
            wordpress=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertEqual(values["home_url"], "https://trusted.example/")
        self.assertEqual(values["site_url"], "https://trusted.example/")
        self.assertTrue(values["reset_url"].startswith("https://trusted.example/wp-login.php?"))
        self.assertNotIn("attacker.invalid", result.stdout)

    def test_installer_is_idempotent_and_preserves_unrelated_settings(self):
        # Synthetic fixture only: do not copy a real config or its credentials.
        source = INSTALLER.read_text()
        legacy = source.split("$legacy = <<<'PHP'\n", 1)[1].split("\nPHP;", 1)[0]
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)), tempfile.TemporaryDirectory() as temp:
                config = pathlib.Path(temp) / "wp-config.php"
                fixture = "<?php\n// unrelated settings remain untouched\n" + legacy + "\n// end\n"
                config.write_bytes(fixture.replace("\n", newline).encode())
                first = subprocess.run(["php", str(INSTALLER), str(config)], capture_output=True)
                self.assertEqual(first.returncode, 0, first.stderr)
                installed = config.read_bytes()
                second = subprocess.run(["php", str(INSTALLER), str(config)], capture_output=True)
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertEqual(config.read_bytes(), installed)
                expected = fixture.replace(
                    legacy, "require_once __DIR__ . '/../scripts/wordpress-site-url.php';"
                ).replace("\n", newline).encode()
                self.assertEqual(installed, expected)
                config.write_text("<?php\n// unfamiliar configuration\n")
                original = config.read_bytes()
                rejected = subprocess.run(["php", str(INSTALLER), str(config)], capture_output=True)
                self.assertNotEqual(rejected.returncode, 0)
                self.assertEqual(config.read_bytes(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
