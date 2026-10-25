# Security scope and reporting

## Theme protections

Recent theme changes include safer output handling, sanitized theme settings,
and HTTP/HTTPS-only links in the Transparency Seal and Freedom of Information
widgets. Consult [CHANGELOG.md](CHANGELOG.md) for individual changes.

These changes reduce specific risks. They are not a guarantee that a website is
free of vulnerabilities. WordPress core, plugins, hosting, configuration, and
administrator practices are separate parts of the security boundary.

## Host responsibilities

On every installation:

- Keep WordPress, PHP, plugins, and the theme on supported, reviewed versions.
- Use HTTPS and a trusted canonical URL configured by the site administrator.
- Use unique administrator credentials and appropriate login protections.
- Keep signing keys and secrets outside the public repository.
- Prevent HTTP access to configuration, backups, database files, and private
  project files; do not rely solely on hidden filenames.
- Maintain private backups and test restores.

The repository's optional server setup scripts protect the bundled development
installation when that startup process is used. They are **not installed by the
theme ZIP**, and do not secure a separately hosted site automatically. Do not
copy those configuration files into an unrelated installation without review.

From v27.0.6, the optional built-in-server setup also disables PHP error display
before WordPress bootstrap and blocks direct requests to core drop-in files.
Diagnostics remain in server logs. See [the file-access guide](https://github.com/TekWorx/gwt-wordpress-tekworx/blob/gwt-wordpress-26.0.0/scripts/FILE-ACCESS.md)
in the source repository for setup and verification. The theme ZIP does not
contain that guide or apply these server settings. On Apache, Nginx, or another
host, configure equivalent error-display and file-access protections separately.

## Historical source archives

The v27.0.0–v27.0.4 distribution releases have been withdrawn. Use v27.0.5 or
later and download the curated theme ZIP for WordPress installation.

Do not deploy historical full-site archives or reuse credentials, signing keys,
or databases from another installation. Previously published secrets must be
treated as compromised even after files are removed from the current branch.
History cleanup cannot recall existing clones or downloads.

## Report a vulnerability

Use the repository's **Security → Report a vulnerability** option when available.
If it is unavailable, open an issue asking for a private reporting channel,
without including exploit details, personal data, credentials, or database files.
Do not post sensitive evidence in a public issue.

## Release verification

The release builder uses explicit theme-file and asset-directory allowlists.
Packaging checks also activate and render the extracted theme in a disposable
WordPress installation. Those checks are useful regression protection, not a
complete code audit or independent security certification.
