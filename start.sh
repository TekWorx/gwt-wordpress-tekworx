#!/bin/bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
php "$project_root/scripts/wordpress-site-url.php"
php "$project_root/scripts/prepare-security.php"
php "$project_root/scripts/configure-wordpress-url.php"
cd "$project_root/wp-site"
# The built-in server ignores .htaccess. Always use the tracked access guard,
# in both the preview workflow and deployment (which share this entry point).
# Apply before any request script is parsed, even when WordPress never loads.
# Keep diagnostics in server logs, never in anonymous HTTP responses.
exec php -d display_errors=0 -d display_startup_errors=0 -d log_errors=1 \
    -S 0.0.0.0:5000 -t "$project_root/wp-site" "$project_root/scripts/router.php"
