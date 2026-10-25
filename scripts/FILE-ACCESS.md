# Built-in server file-access guard

Start the application with `bash start.sh`. Both the preview workflow and the
deployment use this entry point. Do not replace it with a bare `php -S` command:
the built-in server ignores Apache `.htaccess` rules.

`router.php` blocks database directories (including SQLite sidecars and backups),
dotfiles, WordPress configuration, and non-public file types before PHP's static
file handling. It also restricts the workspace-linked theme to public assets, so
the symlink cannot be used to download other project files. Other symlinks are
denied. WordPress PHP endpoints, login, admin, pretty permalinks and public
CSS/JavaScript/image/font/media assets remain available.

Direct requests to WordPress drop-ins such as `wp-content/db.php` and
`object-cache.php` receive a generic 404. Core can still include these files
normally. Generated drop-ins and vendor libraries do not need local edits.

`start.sh` disables PHP `display_errors` and `display_startup_errors` at server
startup and enables `log_errors`. This covers runtime warnings, uncaught errors,
and parse failures even in directly requested PHP libraries that never bootstrap
WordPress. Diagnostics remain in server logs, not visitor responses. Other PHP
endpoints remain available for plugin compatibility; this is not a blanket PHP
entry-point allowlist.

The database is deliberately left in place: this fix does not copy, migrate,
reset or otherwise modify site data or the untracked WordPress configuration.
The protection lives in tracked files and takes effect when the shared startup
command is restarted. Existing published instances do not change until this
change is merged and deployed through the normal release process.

Run the HTTP regression tests with:

```sh
python3 scripts/test-file-access.py
```

The tests start an isolated PHP server with disposable fixtures. They never
read or write the site's database. They cover anonymous GET, HEAD and Range
requests, encoded paths, symlink aliases, database sidecars, private files,
public assets, login/admin and WordPress routing.
