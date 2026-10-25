# Trusted WordPress base URL

`wordpress-site-url.php` defines `WP_HOME` and `WP_SITEURL` before WordPress
loads. It uses no request headers to select a domain or protocol.

- **Published app:** Set `APP_ENV=production` and the environment variable `WORDPRESS_SITE_URL`
  to the site's full canonical HTTPS URL. Startup requests fail closed if it is
  missing or invalid; there is no fallback to a visitor's Host header.
- **Preview:** Set `APP_ENV=development` and `WORDPRESS_SITE_URL` to the trusted
  HTTPS preview URL in the local runner configuration, not in source code.
- **Local CLI:** With `APP_ENV=development` and no configured URL, uses
  `http://localhost:5000`. An absent or unrecognized environment is treated as
  production and requires a valid HTTPS URL.

HTTPS state and host-related server variables are normalized to that trusted
URL. Forwarded headers are discarded rather than trusted, so no proxy IP
allowlist is needed. This also keeps secure cookies and redirects correct behind
a TLS-terminating proxy.

Startup and post-merge setup run `configure-wordpress-url.php`. This replaces
only the known legacy URL block in the untracked `wp-site/wp-config.php`, and is
safe to rerun. It refuses unfamiliar config layouts rather than overwriting
credentials or database settings. The database is not modified.

For an independently hosted WordPress installation, pin `WP_HOME`/`WP_SITEURL`
in its server-side `wp-config.php` to that installation's canonical URL. The
theme itself does not set or override an external installation's site identity.

Run regression checks with `python3 scripts/test-wordpress-url.py`.
