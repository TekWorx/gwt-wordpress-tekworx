# Building and verifying GWT

Preserve original GWT credits and the license notices shipped with bundled
libraries. Do not add site databases, uploads, account records, secrets, or local
hosting configuration to the source repository.

## Build an installation ZIP

With Python 3 available, run:

```sh
python3 scripts/build-release.py
```

The output is `generated-artifacts/gwt-wordpress-<version>.zip`. It contains one
`gwt-wordpress` theme directory and only reviewed theme files and documentation.
The source repository also contains optional host setup and test scripts; those
scripts are not installed by the theme ZIP.

The builder uses explicit file and directory allowlists, rejects symbolic links
and private or unknown file types, and produces reproducible output. Extra text
checks can be supplied with the repeatable `--forbid-text` option.

## Package checks

```sh
python3 scripts/test-release.py
```

Archive-content and reproducibility checks run without WordPress. The HTTP
integration check is explicitly skipped when its local test prerequisites are
missing; a skip is **not** evidence that installation was verified.

For full integration verification, maintain a separate local WordPress
installation at `wp-site/`, with PHP 8.2, SQLite support, the WordPress SQLite
Database Integration plugin, and its `wp-content/db.php` drop-in. This directory
is ignored by version control. Never use a production database as a fixture.
The tests create their own temporary database and accounts, copy core entry
points, and use core/plugin code as read-only test inputs.

Other local checks are:

```sh
python3 scripts/test-wordpress-url.py
python3 scripts/test-file-access.py
python3 scripts/test-credentials.py
php scripts/test-widget-urls.php
```

These additional checks require the local WordPress test installation and
appropriate development configuration. They do not replace testing on staging
with the target host's PHP version, plugins, and content.

## Working with the public baseline

The public source begins at the reviewed v27.0.5 baseline. Older release archives
are withdrawn. If your clone predates that baseline, make a fresh clone rather
than merging or force-pushing the old history back into the repository.

Review every release diff and installation ZIP. Do not describe automated checks
as a guarantee that the theme or a complete WordPress website is vulnerability-free.

## Draft release packaging

After reviewing the source and completing full integration checks, create a
version tag and an empty draft release under your own GitHub account, through
the website or an authenticated user connection. Supply the intended tag
explicitly when creating or updating the draft. Record its numeric release ID.
Creating the draft as a user keeps that user displayed as the release author.

Run the **Package release** workflow with the reviewed tag and draft release ID,
using the same GitHub account that created the draft. The workflow builds the
curated ZIP and checksum from the tagged source, checks that the destination is
an empty, matching, user-created draft owned by the dispatcher, and uploads both
files while verifying their server-reported checksums. It never creates or
publishes a release. For a failed partial upload, review and remove its draft
assets before retrying; published assets must not be overwritten.

Check the uploader safeguards locally with
`python3 scripts/test-release-workflow.py`. These tests use mocked requests and
do not contact GitHub or require credentials.

The runner's package tests explicitly skip the local WordPress integration check
when the test installation is absent. Complete that check separately before
tagging. Compare the uploaded checksum with the reviewed package before publishing.
Do not move a tag or replace assets after a release has been published.
