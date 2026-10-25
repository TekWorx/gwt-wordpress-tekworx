#!/usr/bin/env python3
"""Credential regression tests against a disposable WordPress/SQLite installation."""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import unittest


class CredentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.source = Path(__file__).resolve().parent.parent
        cls.site = cls.root / "wp-site"
        cls.site.mkdir()
        (cls.root / "scripts").mkdir()
        for name in ["prepare-security.php", "wordpress-config.php", "wordpress-login-security.php",
                     "wordpress-site-url.php"]:
            shutil.copy(cls.source / "scripts" / name, cls.root / "scripts" / name)
        # Include directories and plugin code are read-only links; all config, options, accounts,
        # transients, and SQLite data belong to this disposable installation.
        for source in (cls.source / "wp-site").glob("*.php"):
            if source.name not in ["wp-config.php", "wp-config-sample.php"]:
                # wp-load.php resolves configuration relative to its own __DIR__.
                # It must be a copy, not a link back to the live installation.
                shutil.copy(source, cls.site / source.name)
        for name in ["wp-admin", "wp-includes"]:
            (cls.site / name).symlink_to(cls.source / "wp-site" / name, target_is_directory=True)
        content = cls.site / "wp-content"
        (content / "plugins").mkdir(parents=True)
        (content / "themes").mkdir()
        (content / "database").mkdir()
        shutil.copy(cls.source / "wp-site/wp-content/db.php", content / "db.php")
        (content / "plugins/sqlite-database-integration").symlink_to(
            cls.source / "wp-site/wp-content/plugins/sqlite-database-integration",
            target_is_directory=True,
        )
        shutil.copy(cls.source / "scripts/wordpress-config.php", cls.site / "wp-config.php")
        cls.env = dict(os.environ)
        cls.env["SESSION_SECRET"] = secrets.token_hex(48)
        cls.env.pop("WP_ADMIN_PASSWORD", None)
        cls.old_password = secrets.token_urlsafe(30)
        cls.password = secrets.token_urlsafe(30)
        cls.env["FIXTURE_PASSWORD"] = cls.old_password
        cls.php("""
            define('WP_INSTALLING', true);
            require getenv('FIXTURE_SITE') . '/wp-load.php';
            require_once ABSPATH . 'wp-admin/includes/upgrade.php';
            wp_install('Credential tests', 'admin', 'fixture@example.invalid', false,
                '', getenv('FIXTURE_PASSWORD'));
            $user = get_user_by('login', 'admin');
            WP_Session_Tokens::get_instance($user->ID)->create(time() + 3600);
            WP_Application_Passwords::create_new_application_password($user->ID,
                ['name' => 'fixture']);
            echo 'initialized';
        """, bootstrap=False)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def php(cls, code, bootstrap=True, env=None):
        environment = dict(cls.env if env is None else env)
        environment["FIXTURE_SITE"] = str(cls.site)
        prefix = "require getenv('FIXTURE_SITE') . '/wp-load.php';" if bootstrap else ""
        result = subprocess.run(
            ["php", "-r", prefix + code], env=environment, text=True, capture_output=True
        )
        if result.returncode:
            # Never include process output: an upstream error could contain data.
            raise AssertionError("Disposable WordPress PHP operation failed")
        return result.stdout.strip()

    @classmethod
    def prepare(cls, env=None):
        result = subprocess.run(
            ["php", str(cls.root / "scripts/prepare-security.php")],
            env=cls.env if env is None else env, text=True, capture_output=True,
        )
        return result.returncode

    def test_complete_security_lifecycle(self):
        before = json.loads(self.php("""
            $u = get_user_by('login', 'admin');
            echo json_encode([$u->ID, $u->user_pass, wp_count_posts()->publish]);
        """))
        self.assertEqual(self.prepare(), 0)
        state = json.loads(self.php("""
            $u = get_user_by('login', 'site-manager');
            echo json_encode([
                (bool)get_user_by('login', 'admin'), $u->ID, $u->user_pass,
                wp_count_posts()->publish,
                wp_check_password(getenv('FIXTURE_PASSWORD'), $u->user_pass, $u->ID),
                get_user_meta($u->ID, 'session_tokens', true),
                WP_Application_Passwords::get_user_application_passwords($u->ID)
            ]);
        """))
        self.assertFalse(state[0])
        self.assertEqual(before[0], state[1])
        self.assertNotEqual(before[1], state[2])
        self.assertEqual(before[2], state[3])
        self.assertFalse(state[4])
        self.assertFalse(state[5])
        self.assertEqual(state[6], [])
        self.php("""
            $id = wp_create_user('new-fixture-manager', getenv('FIXTURE_PASSWORD'),
                'new-fixture@example.invalid');
            $u = new WP_User($id);
            $u->set_role('administrator');
            WP_Session_Tokens::get_instance($id)->create(time() + 3600);
            WP_Application_Passwords::create_new_application_password($id,
                ['name' => 'new-admin-fixture']);
        """)
        new_admin_state = self.php("""
            $u = get_user_by('login', 'new-fixture-manager');
            echo json_encode([$u->user_pass, get_user_meta($u->ID, 'session_tokens', true),
                WP_Application_Passwords::get_user_application_passwords($u->ID)]);
        """)
        self.assertEqual(self.prepare(), 0)
        self.assertEqual(state[2], self.php("echo get_user_by('login', 'site-manager')->user_pass;"))
        self.assertEqual(new_admin_state, self.php("""
            $u = get_user_by('login', 'new-fixture-manager');
            echo json_encode([$u->user_pass, get_user_meta($u->ID, 'session_tokens', true),
                WP_Application_Passwords::get_user_application_passwords($u->ID)]);
        """))

        self.env["WP_ADMIN_PASSWORD"] = self.password
        self.assertEqual(self.prepare(), 0)
        self.assertEqual("yes", self.php("""
            $u = get_user_by('login', 'site-manager');
            echo wp_check_password(getenv('WP_ADMIN_PASSWORD'), $u->user_pass, $u->ID)
                ? 'yes' : 'no';
        """))
        configured_hash = self.php("echo get_user_by('login', 'site-manager')->user_pass;")
        self.assertEqual(self.prepare(), 0)
        self.assertEqual(configured_hash, self.php("echo get_user_by('login', 'site-manager')->user_pass;"))

        # Removing the secret is a revocation operation, not a no-op.
        self.php("""
            $u = get_user_by('login', 'site-manager');
            WP_Session_Tokens::get_instance($u->ID)->create(time() + 3600);
            WP_Application_Passwords::create_new_application_password($u->ID,
                ['name' => 'revocation-fixture']);
        """)
        removed_env = dict(self.env)
        removed_env.pop("WP_ADMIN_PASSWORD")
        removed_env["REVOKED_FIXTURE_PASSWORD"] = self.password
        self.assertEqual(self.prepare(removed_env), 0)
        revoked = json.loads(self.php("""
            $u = get_user_by('login', 'site-manager');
            echo json_encode([
                $u->user_pass,
                is_wp_error(wp_authenticate('site-manager', getenv('REVOKED_FIXTURE_PASSWORD'))),
                get_user_meta($u->ID, 'session_tokens', true),
                WP_Application_Passwords::get_user_application_passwords($u->ID),
                (bool)get_user_meta($u->ID, '_gwt_admin_secret_configured', true)
            ]);
        """, env=removed_env))
        self.assertNotEqual(configured_hash, revoked[0])
        self.assertTrue(revoked[1])
        self.assertFalse(revoked[2])
        self.assertEqual(revoked[3], [])
        self.assertFalse(revoked[4])
        self.assertEqual(self.prepare(removed_env), 0)
        self.assertEqual(revoked[0], self.php(
            "echo get_user_by('login', 'site-manager')->user_pass;", env=removed_env))
        self.assertEqual(self.prepare(), 0)
        self.php("""
            foreach (gwt_login_buckets('site-manager') as $key => $limit) {
                delete_transient($key);
            }
        """)

        self.assertEqual("yes", self.php("""
            $keys = array_map('constant', ['AUTH_KEY','SECURE_AUTH_KEY','LOGGED_IN_KEY',
                'NONCE_KEY','AUTH_SALT','SECURE_AUTH_SALT','LOGGED_IN_SALT','NONCE_SALT']);
            echo count(array_unique($keys)) === 8 && strlen(AUTH_KEY) === 128
                && DB_PASSWORD === '' && DB_ENGINE === 'sqlite' ? 'yes' : 'no';
        """))
        old_key_hash = self.php("echo hash('sha256', AUTH_KEY);")
        rotated_env = dict(self.env, SESSION_SECRET=secrets.token_hex(48))
        self.assertNotEqual(old_key_hash, self.php("echo hash('sha256', AUTH_KEY);", env=rotated_env))

        # Fail closed and do not replace the installed configuration.
        config = (self.site / "wp-config.php").read_bytes()
        for overrides in [{"SESSION_SECRET": ""}, {"WP_ADMIN_PASSWORD": "short"}]:
            self.assertNotEqual(self.prepare(dict(self.env, **overrides)), 0)
            self.assertEqual(config, (self.site / "wp-config.php").read_bytes())

        # Login success, legacy username rejection, persistent account lock.
        self.assertEqual("ok", self.php("""
            $u = wp_authenticate('site-manager', getenv('WP_ADMIN_PASSWORD'));
            echo $u instanceof WP_User ? 'ok' : 'failed';
        """))
        self.assertEqual("rejected", self.php("""
            echo is_wp_error(wp_authenticate('admin', getenv('FIXTURE_PASSWORD')))
                ? 'rejected' : 'accepted';
        """))
        for _ in range(5):
            self.assertEqual("rejected", self.php("""
                echo is_wp_error(wp_authenticate('site-manager', 'wrong-fixture-password'))
                    ? 'rejected' : 'accepted';
            """))
        self.assertEqual("gwt_login_throttled", self.php("""
            echo wp_authenticate('site-manager', getenv('WP_ADMIN_PASSWORD'))->get_error_code();
        """))
        self.assertEqual("ok", self.php("""
            foreach (gwt_login_buckets('site-manager') as $key => $limit) {
                set_transient($key, ['count' => 100, 'until' => time() - 1], 30);
            }
            $u = wp_authenticate('site-manager', getenv('WP_ADMIN_PASSWORD'));
            echo $u instanceof WP_User ? 'ok' : 'failed';
        """))
        self.assertEqual("gwt_login_throttled", self.php("""
            foreach (gwt_login_buckets('other-fixture') as $key => $limit) {
                if ($limit === 50) {
                    set_transient($key, ['count' => 50, 'until' => time()+900], 900);
                }
            }
            $_SERVER['HTTP_X_FORWARDED_FOR'] = '198.51.100.12';
            echo wp_authenticate('site-manager', getenv('WP_ADMIN_PASSWORD'))->get_error_code();
        """))
        # Printed results never contain salts, passwords or password hashes.


if __name__ == "__main__":
    unittest.main()
