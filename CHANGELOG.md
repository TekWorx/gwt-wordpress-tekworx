# Changelog

All notable changes to the GWT WordPress Theme (TekWorx fork) will be documented in this file.

## [27.0.1] - 2026-03-08

### Fixed
- Fixed "critical error" on Theme Options page (Appearance > Theme Options) caused by non-static method `govph_options_page()` being called with static syntax `array('GOVPH', 'govph_options_page')`. PHP 8.x throws a fatal error for this pattern. Method is now properly declared as `static`.

---

## [27.0.0] - 2026-03-07

First release under [TekWorx](https://github.com/TekWorx/gwt-wordpress-tekworx), forked from [iGovPhil/gwt-wordpress](https://github.com/iGovPhil/gwt-wordpress) v26.0.0. This release addresses critical security vulnerabilities, PHP 8.x compatibility issues, performance problems, accessibility gaps, and WordPress feature compatibility.

### Security
- Added `govph_sanitize_options()` sanitization callback to `register_setting()` — all theme options are now sanitized by type (checkbox, color, URL, text, select) before saving to the database.
- Added `esc_attr()` to all admin form field `value` attributes in `inc/function-options.php`.
- Added `esc_html()`, `esc_attr()`, and `esc_url()` to all frontend output in `govph_displayoptions()` — CSS values, image URLs, agency name/tagline text, accessibility link hrefs.
- Escaped slider output: `esc_url()` for slide links, `esc_html()` for captions, `intval()` for slide numbers in `inc/vendors/envato-flex-slider/envato-flex-slider.php`.
- Escaped slider admin meta box input value with `esc_attr()` in `inc/vendors/envato-flex-slider/slider-img-type.php`.
- Escaped breadcrumb output: separator, ancestor links, page titles in `inc/function-breadcrumbs.php`.
- Escaped banner CSS class variables in `inc/banner.php`.
- Escaped template tag output in `inc/template-tags.php`.
- Fixed `$_REQUEST` / `$_POST` inconsistency in slider save handler.

### PHP 8.x Compatibility
- Fixed `sizeof()` on potentially non-array value in `inc/function-options.php` constructor — now uses `is_array()` guard with `count()`.
- Added null coalescing (`??`) for all undefined array key accesses throughout `inc/function-options.php` (50+ locations) and `inc/function-breadcrumbs.php`.
- Fixed undefined variables: `$backgroundHeaderImageSizeSetting`, `$menuSetting`, `$menuFontSetting`, `$menuFontHoverSetting` (initialized before `.=` concatenation).
- Fixed undefined variable `$next_id` in `inc/template-tags.php` (initialized to `null` before foreach loop).
- Fixed undefined variable `$output` in `inc/function-breadcrumbs.php`.
- Replaced all loose comparisons (`==`/`!=`) with strict comparisons (`===`/`!==`) throughout theme files.
- Added `_default_options` array with complete set of default keys to prevent undefined key warnings.

### Performance
- Eliminated duplicate jQuery loading: deregistered WordPress bundled jQuery and registered theme's jQuery 3.6.0 under the standard `jquery` handle.
- Moved Foundation JS and jQuery to the footer (changed `$in_footer` parameter to `true`).
- Updated all hardcoded `'20160530'` version strings to use `wp_get_theme()->get('Version')` for proper cache busting.

### Accessibility
- Added `<label>` element (visually hidden) to search form in `searchform.php` for WCAG 2.0 Success Criterion 3.3.2.
- Added `role="switch"` and `aria-checked="false"` to high contrast toggle link in `header.php`.
- Expanded text resizer in `js/theme.js` from targeting only `<p>` elements to a broad range of content elements (`p, li, td, th, dd, dt, span, blockquote, label, input, textarea, select, a`).
- Updated `aria-checked` handling to use proper string `"true"`/`"false"` values for correct ARIA switch semantics.

### WordPress Compatibility
- Enabled `add_theme_support('title-tag')` in `inc/function-initialize.php` (was commented out).
- Removed deprecated `wp_title()` call from `header.php` `<title>` tag.
- Replaced `wp_title` filter with modern `document_title_parts` filter in `inc/extras.php`.
- Replaced deprecated `query_posts()` with `new WP_Query()` in `inc/vendors/envato-flex-slider/envato-flex-slider.php`.
- Removed erroneous `the_tags()` call from `<style>` element in `header.php` (was producing invalid HTML).

### Bug Fixes
- Fixed `apply_filters('the_content','make_clickable')` misuse in `inc/function-initialize.php` — changed to `add_filter()`.
- Removed duplicate `require` of `inc/template-tags.php` in `functions.php`.
- Added dynamic widget URL rewriting filter (`govph_fix_widget_theme_urls`) to prevent broken images when site URL changes or when served behind HTTPS proxy.
- Added robust HTTPS reverse proxy detection in WordPress configuration, checking `X-Forwarded-Proto`, `X-Forwarded-SSL`, `X-Forwarded-Port`, and `Server-Port` headers.

### Documentation
- Created comprehensive `AUDIT_REPORT.md` with full technical audit covering security, compatibility, performance, accessibility, maintainability, and a prioritized remediation roadmap.
- Created this `CHANGELOG.md` for release tracking.
- Updated `README.md` with TekWorx fork information and v27.0.0 changelog.

## [26.0.0] - 2022 (iGovPhil upstream)

See the original [iGovPhil/gwt-wordpress](https://github.com/iGovPhil/gwt-wordpress) repository for the v26.0.0 changelog.
