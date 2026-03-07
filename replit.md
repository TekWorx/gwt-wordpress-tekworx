# GWT WordPress Theme - Replit Setup

## Project Overview
This is the **Government Web Template (GWT) for WordPress** — a custom WordPress theme (version 26.0.0) built for Philippine government websites. It is based on the ZURB Foundation framework and follows the Unified Web Content Policy of the Philippines.

## Project Structure
- `/` — WordPress theme files (PHP templates, CSS, JS, images)
- `/wp-site/` — Full WordPress installation (not tracked in git)
  - `/wp-site/wp-content/themes/gwt-wordpress` — Symlink to theme root
  - `/wp-site/wp-content/plugins/sqlite-database-integration` — SQLite DB plugin
  - `/wp-site/wp-content/database/` — SQLite database files
  - `/wp-site/wp-config.php` — WordPress configuration

## Architecture
- **CMS**: WordPress (latest)
- **Language**: PHP 8.2
- **Database**: SQLite (via WordPress SQLite Integration plugin)
- **Web Server**: PHP built-in development server on port 5000
- **Theme**: GWT-Wordpress 26.0.0

## Running the Application
The app starts with `bash /home/runner/workspace/start.sh` which launches a PHP web server at `0.0.0.0:5000` serving the WordPress installation in `/wp-site/`.

## Admin Access
- **URL**: `/wp-admin`
- **Username**: `admin`
- **Password**: `admin123`

## Key Configuration
- `wp-site/wp-config.php` — WordPress config with dynamic URL detection and error suppression
- `inc/function-options.php` — Theme options (fixed to handle uninitialized options gracefully)
- `functions.php` — Theme setup (X-Frame-OPTIONS header removed to allow Replit preview)

## Notes
- WordPress is installed in `wp-site/` (not tracked in git)
- The theme is symlinked from the workspace root into WordPress themes directory
- SQLite is used instead of MySQL since MySQL is not available in Replit
- PHP warnings are suppressed in wp-config.php (`error_reporting(0)`)
