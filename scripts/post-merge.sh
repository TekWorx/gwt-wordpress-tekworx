#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

bash -n start.sh
php scripts/configure-wordpress-url.php

# Validate theme code only, not the local WordPress installation or tooling.
while IFS= read -r -d '' file; do
    php -l "$file"
done < <(find . -type d \( -name '.*' ! -name '.' -o -name wp-site -o -name attached_assets \) -prune -o -type f -name '*.php' -print0)

echo "Post-merge checks passed. WordPress URL configuration is current; the database was not modified."
