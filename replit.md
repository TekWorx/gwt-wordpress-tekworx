# GWT WordPress Theme - Development Setup

## Project Overview
This is the **Government Web Template (GWT) for WordPress** v27.0.0 — a custom WordPress theme built for Philippine government websites. It is based on the ZURB Foundation framework and follows the Unified Web Content Policy of the Philippines.

Maintained by TekWorx. Forked from iGovPhil/gwt-wordpress v26.0.0.
See `AUDIT_REPORT.md` for the full technical audit and `CHANGELOG.md` for release notes.

## Project Structure
- `/` — WordPress theme files (PHP templates, CSS, JS, images)
- `/wp-site/` — Full WordPress installation (not tracked in git)
  - `/wp-site/wp-content/themes/gwt-wordpress` — Symlink to theme root
  - `/wp-site/wp-content/plugins/sqlite-database-integration` — SQLite DB plugin
  - `/wp-site/wp-content/database/` — SQLite database files
  - `/wp-site/wp-config.php` — WordPress configuration with HTTPS proxy detection

## Architecture
- **CMS**: WordPress (latest)
- **Language**: PHP 8.2
- **Database**: SQLite (via WordPress SQLite Integration plugin)
- **Web Server**: PHP built-in development server on port 5000
- **Theme**: GWT-Wordpress 27.0.0

## Running the Application
The app starts with `bash /home/runner/workspace/start.sh` which launches a PHP web server at `0.0.0.0:5000` serving the WordPress installation in `/wp-site/`.

## Admin Access
- **URL**: `/wp-admin`
- **Username**: `admin`
- **Password**: `admin123`

## Key Configuration
- `wp-site/wp-config.php` — WordPress config with dynamic URL detection, HTTPS proxy detection, and error suppression
- `inc/function-options.php` — Theme options class with sanitization callback, output escaping, PHP 8.x compatibility
- `inc/function-enqueue_scripts.php` — Asset loading (single jQuery, footer scripts, versioned assets)
- `inc/function-initialize.php` — Theme setup with title-tag support enabled
- `functions.php` — Theme setup with widget URL fix filter

## v27.0.0 Changes (from v26.0.0)
- **Security**: Output escaping added throughout; sanitization callback on register_setting
- **PHP 8.x**: sizeof() guard, null coalescing for array keys, strict comparisons, undefined variable fixes
- **Performance**: Duplicate jQuery eliminated, scripts moved to footer, version strings use theme version
- **Accessibility**: Search form label added, ARIA roles on toggle buttons, text resizer expanded
- **WordPress Compat**: title-tag support enabled, deprecated wp_title replaced, the_tags() misuse removed

## Notes
- WordPress is installed in `wp-site/` (not tracked in git)
- The theme is symlinked from the workspace root into WordPress themes directory
- SQLite is used instead of MySQL for local development
- PHP warnings are suppressed in wp-config.php (`error_reporting(0)`) as a safety net
- Widget URLs are dynamically rewritten via `govph_fix_widget_theme_urls` filter for HTTPS compatibility
