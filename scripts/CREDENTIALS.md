# Credential hardening

Both preview and deployment run `start.sh`. Before opening the listener it
installs the tracked, secret-free configuration and mandatory login security
plugin, renames the default administrator (preserving its ID and content), and
rotates exposed administrator passwords. Other original administrators retain
their usernames, but their initially exposed passwords are also revoked.
The initial affected account IDs are recorded once; administrators created
normally afterward retain their chosen passwords across restarts. This runs
against each instance's own database; no development database is copied into a
published instance.

## Secure administrator access

Set `WP_ADMIN_PASSWORD` to a unique password-manager-generated password of at
least 20 characters in the hosting environment's secret manager, then restart. The renamed account is
`site-manager`. With no password secret it is deliberately inaccessible until
configured, rather than retaining the known weak login. Subsequent starts do not
change passwords or revoke sessions unless the configured password changes.
Removing `WP_ADMIN_PASSWORD` and restarting revokes the previously configured
password, sessions, and application passwords; the account is inaccessible until
a new secret is supplied.
Existing administrators can also use WordPress's normal password reset mechanism
if their account has a working email address. No credential is printed or written
to a project file. Ensure the secret is configured for each target environment.

`SESSION_SECRET` must contain at least 32 random characters. Eight independently
labelled HMAC-SHA512 outputs replace the old WordPress keys and salts.
Rotating this master secret revokes cookies and nonces. SQLite has no database
password to rotate: the old unused MySQL placeholders are removed.

Authentication allows five failed attempts per account and fifty per direct
source address in a fixed fifteen-minute window, persisted in the database.
Correct passwords cannot bypass an active lock; successful requests do not
extend the window. Browser and XML-RPC authentication share these limits.
REST API Basic Authentication with application passwords uses a separate
WordPress authentication path and is not covered by this login throttle.
Forwarded IP headers are intentionally not trusted. Behind a shared proxy,
the address limit may be shared by visitors; account limits still apply.

Run `python3 scripts/test-credentials.py` for the disposable-installation
credential lifecycle tests, and `python3 scripts/test-file-access.py` for HTTP
file-disclosure regressions. Tests never copy or query the existing site database.

## Previously exposed Git history

Removing files from the current tree does **not** erase older commits, clones,
forks, or checkpoints. Treat the old salts, password hashes and credentials as
compromised permanently. The startup rotation makes them unusable on the updated
instance, but only when the code reaches that instance through the normal release
process. This task does not deploy or modify a published instance.

A task-branch merge cannot purge ancestor commits. History cleanup must be
coordinated separately by the repository owner because it changes commit IDs,
requires force-pushing protected branches/tags, and requires collaborators to
discard old clones. After arranging a private backup and a maintenance window,
use a disposable mirror clone with `git-filter-repo` installed:

```sh
git clone --mirror <repository-url> sanitized.git
cd sanitized.git
# Set this to the former setup document that contained credentials.
LEGACY_SETUP_DOC=path/to/former-setup-document.md
git filter-repo --invert-paths --path wp-site/ --path "$LEGACY_SETUP_DOC"
# Inspect all refs and verify the sensitive paths are absent.
git log --all -- wp-site/ "$LEGACY_SETUP_DOC"
# Only after owner approval, restore the remote if filter-repo removed it,
# then force-push the sanitized branches and tags.
```

This removes the historical WordPress tree (including the exposed SQLite
database) and the credential-bearing documentation. Restore only the sanitized
current documentation after cleanup. Do not merge an old branch back afterward.
The remote host may also retain unreachable objects or cached copies; arrange
their removal under its retention policy. Do not run history rewriting in an
active task checkout or assume it cleans other clones.
