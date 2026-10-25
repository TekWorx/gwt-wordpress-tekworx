# Installation and updates

## What this package contains

GWT is a theme for an existing WordPress website. It does not include WordPress
core, plugins, accounts, passwords, database files, or site content.
Original GWT credits and bundled dependency license notices remain applicable.

The current local verification environment is WordPress 6.9.1 with PHP 8.2.
That is a tested environment, not a claim that every other version is supported.
Use a currently maintained WordPress release and PHP version supported by your
host. Test on staging before changing a production government website.

## Install

1. Back up the existing website's files and database.
2. Download the **theme-only ZIP** attached to a reviewed project release.
   GitHub's automatically generated source archives are not a substitute for the
   curated installation package, especially for historical versions.
3. In WordPress, open **Appearance → Themes → Add New Theme → Upload Theme**.
4. Upload the ZIP, install it, and activate the GWT theme.
5. Configure menus, widgets, the site identity, and theme options.
6. Check the homepage, search, navigation, forms, widgets, and mobile layout.

For a manual installation, extract the ZIP into `wp-content/themes/`. It should
create `wp-content/themes/gwt-wordpress/style.css`, not a second nested theme
folder. Activate the theme in WordPress afterward.

Use your own site's public URL. Do not copy another site's `wp-config.php`,
database, uploads, credentials, or hosting configuration.

## Update

Back up first and test the new package on staging. Keep the existing
`gwt-wordpress` folder name; changing it can affect menu and widget assignments.
Use WordPress's theme replacement flow or your normal controlled deployment.
Do not replace the site's database or `wp-config.php` when updating a theme.

Keep customizations in a child theme where possible. Retain a private backup of
the previously installed theme so you can restore its files if necessary.

## Hosting security

Read [SECURITY.md](SECURITY.md). Installing the theme does not configure server
access rules, administrator credentials, HTTPS, WordPress signing keys, backups,
or login throttling.
