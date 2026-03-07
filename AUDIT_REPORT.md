# GWT WordPress Theme — Technical Audit Report

**Theme:** GWT-WordPress 26.0.0 (Government Web Template)  
**Repository:** https://github.com/TekWorx/gwt-wordpress-tekworx  
**Audit Date:** March 2026  
**PHP Target:** 8.0+  
**WordPress Target:** 6.x (latest stable)

---

## A. Executive Summary

The GWT WordPress theme is a feature-rich government website template built on the ZURB Foundation 6 framework, designed for Philippine government agencies. It includes extensive accessibility features, customizable branding, and a modular architecture. However, the codebase has significant issues that must be addressed before it can be considered production-ready on modern hosting environments.

**Classification: Usable with Fixes**

The theme works on older PHP versions (7.x) and older WordPress, but produces numerous PHP 8.x warnings/errors and has systemic security issues (missing output escaping throughout). The core architecture is sound — modular `inc/` structure, proper use of WordPress hooks — but the implementation has accumulated technical debt.

**Top 3 Critical Issues:**
1. **Stored XSS vulnerabilities** — Theme options are saved without sanitization and echoed without escaping throughout `inc/function-options.php` and the slider plugin.
2. **PHP 8.x fatal errors and warnings** — `sizeof()` on non-array, undefined array keys, uninitialized variables throughout `govph_displayoptions()` and GOVPH class methods.
3. **Duplicate jQuery loading** — Theme bundles jQuery 3.6.0 under a custom handle alongside WordPress core jQuery, causing conflicts and redundant downloads.

---

## B. Critical Issues

### B1. Stored XSS via Theme Options (HIGH)
- **File:** `inc/function-options.php`
- **Issue:** `register_setting('govph_options','govph_options')` (line 214) has no sanitization callback. All theme options are saved raw to the database and echoed without escaping.
- **Impact:** An administrator (or any user with access to theme options) can inject arbitrary HTML/JS that persists and renders on every page load.
- **Affected output locations:**
  - `govph_displayoptions('govph_logo')` — lines 887-897: agency name, tagline, logo URL echoed raw into `<img src>`, `alt` attributes, and `<div>` content.
  - `govph_displayoptions('govph_header_setting')` — line 901: header image URL echoed into CSS `background-image:url()` without sanitization.
  - Admin form fields: lines 338, 370, 379, 387, 406, 429, 439, 499, 509, 519, 530, 541, 606, 617, 695, 722, 738, 771, 781, 791, 801, 810, 818, 827, 839 — all echo `$this->options[...]` directly into `value=""` attributes without `esc_attr()`.
- **Fix:** Add sanitization callback to `register_setting()`. Apply `esc_attr()` to all form field values. Apply `esc_html()`, `esc_attr()`, `esc_url()` to all frontend output.

### B2. Stored XSS via Slider (HIGH)
- **File:** `inc/vendors/envato-flex-slider/envato-flex-slider.php`
- **Issue:** Line 45 builds slider HTML with raw `$slide_link` (from post meta) and `$caption` (from `get_the_title()`) without escaping.
- **Fix:**
```php
$slider .= '<li class="orbit-slide is-active"><a href="' . esc_url($slide_link) . '">' . $img . '</a><figcaption class="orbit-caption">' . esc_html($caption) . '</figcaption></li>';
```

### B3. Slider Admin Meta Box Missing Escaping (MEDIUM)
- **File:** `inc/vendors/envato-flex-slider/slider-img-type.php`
- **Issue:** Line 64 echoes `$slider_link` into an input value without `esc_attr()`.
- **Fix:** `value="<?php echo esc_attr($slider_link); ?>"`.

### B4. PHP 8.x `sizeof()` on Non-Array (CRITICAL)
- **File:** `inc/function-options.php`, line 65
- **Issue:** `sizeof($this->options)` will throw a `TypeError` if `get_option()` returns `false` (boolean) instead of an array.
- **Fix:**
```php
if (is_array($this->options) && count($this->options) > 0) {
```

### B5. PHP 8.x Undefined Array Key Warnings (HIGH)
- **File:** `inc/function-options.php`
- **Issue:** Throughout `govph_displayoptions()` (lines 905, 914, 928-939, 1030, 1036, 1044, 1052, 1055, 1060, 1063, 1068), array keys are accessed on `$option` without `isset()` checks. When the option doesn't exist, PHP 8.0+ emits "Undefined array key" warnings.
- **Also in GOVPH class methods:** Lines 296, 305, 315, 324, 325, 368, 377, 418, 451, 460, 469, 478, 549-581, 642-645, 660-662, 676-678, 712, 728 — all access `$this->options[...]` with loose comparison without null-safe checks.
- **Fix:** Use `$option['key'] ?? ''` or `isset($option['key'])` checks throughout.

### B6. Undefined Variable `$next_id` (MEDIUM)
- **File:** `inc/template-tags.php`, line 152
- **Issue:** `$next_id` is only defined inside a `foreach` loop (line 146). If the loop doesn't execute or the condition isn't met, `$next_id` is undefined.
- **Fix:** Initialize `$next_id = null;` before the loop.

### B7. Undefined Variables in `govph_displayoptions()` (HIGH)
- **File:** `inc/function-options.php`
- **Lines:** 906-907 (`$backgroundHeaderImageSizeSetting`), 1163 (`$menuSetting`), 1167-1168 (`$menuFontSetting`), 1173 (`$menuFontHoverSetting`), 1177 (`$menuFontSetting`)
- **Issue:** These variables are used with `.=` (concatenation-assignment) without being initialized first.
- **Fix:** Initialize each variable to `''` before use.

---

## C. Compatibility Findings

### C1. WordPress API Compatibility

| Area | Status | Details |
|------|--------|---------|
| `title-tag` support | Missing | Commented out in `inc/function-initialize.php` (line 36). Theme uses deprecated `wp_title()` in `header.php` (line 20) and a `wp_title` filter in `inc/extras.php`. |
| `wp_title()` | Deprecated | Used directly in `header.php` line 20: `<?php wp_title( '\|', true, 'right' ); ?>`. Should use `add_theme_support('title-tag')` instead. |
| `query_posts()` | Deprecated pattern | Used in `inc/vendors/envato-flex-slider/envato-flex-slider.php` line 21. Should use `WP_Query`. |
| `the_tags()` | Misused | `header.php` line 28: `<style <?php the_tags(); ?>>` — `the_tags()` outputs post tags, not style attributes. This produces invalid HTML. |
| Block Editor | Partial | Theme provides options to disable Gutenberg for widgets and posts (classic editor toggle), but no `theme.json`, no block styles, no block patterns. |
| REST API | Blocked | `inc/function-disable_api.php` blocks all REST API for logged-out users. This breaks Gutenberg for unauthenticated contexts and may interfere with plugins. |
| `apply_filters` misuse | Yes | `inc/function-initialize.php` line 91: `apply_filters('the_content','make_clickable')` — this doesn't do what's intended. Should be `add_filter('the_content', 'make_clickable')`. |

### C2. PHP 8.x Compatibility

| Issue | Severity | Location |
|-------|----------|----------|
| `sizeof()` on non-array | Fatal | `inc/function-options.php:65` |
| Undefined array key access | Warning | `inc/function-options.php` (50+ locations) |
| Undefined variable `$next_id` | Warning | `inc/template-tags.php:152` |
| Undefined variables via `.=` | Warning | `inc/function-options.php:906,1163,1167,1173,1177` |
| Loose `==` comparisons with `0` | Logic bug | `inc/function-options.php:549-581` (border width/radius comparisons) |
| `$_REQUEST` vs `$_POST` mismatch | Warning | `inc/vendors/envato-flex-slider/slider-img-type.php:92-93` |
| `$option['govph_breadcrumbs_enable']` without check | Warning | `inc/function-breadcrumbs.php:9` |

### C3. Browser/JavaScript Compatibility
- Foundation 6 and jQuery 3.6.0 are modern enough for current browsers.
- `js/theme.js` uses `jQuery` global and Foundation IIFE correctly.
- `createCookie()` sets `HttpOnly` flag which is ineffective from JavaScript (HttpOnly cookies can only be set server-side).
- Global variable `template_directory` is set via inline `<script>` in `header.php` line 203 without `var`/`let`/`const`.

### C4. Responsive/Mobile
- Foundation 6 grid provides responsive layout.
- Off-canvas mobile menu is implemented.
- Banner slider has mobile visibility options.
- Image sizing adapts based on sidebar configuration in `template-parts/content.php`.

---

## D. Security Findings

### D1. Output Escaping (HIGH - Systemic)

**Frontend output (visible to all visitors):**

| File | Line(s) | Issue |
|------|---------|-------|
| `inc/function-options.php` | 882-884 | CSS values echoed without sanitization |
| `inc/function-options.php` | 887-897 | Agency name, tagline, logo URL echoed raw |
| `inc/function-options.php` | 900-902 | Header color/image echoed into CSS |
| `inc/function-options.php` | 912-918 | Slider CSS values echoed raw |
| `inc/function-options.php` | 921-926 | Anchor colors echoed raw |
| `inc/function-options.php` | 1144-1193 | Multiple CSS values echoed raw |
| `inc/vendors/envato-flex-slider/envato-flex-slider.php` | 45 | Slider link and caption echoed raw |
| `header.php` | 203 | `template_directory` URL echoed without `esc_url()` |
| `header.php` | 214-232 | Accessibility link URLs echoed without `esc_url()` |
| `inc/banner.php` | 53, 61, 68, 75, 125 | CSS class variables echoed without `esc_attr()` |
| `inc/function-breadcrumbs.php` | 12-13, 48-49, 58-63 | Breadcrumb separator, titles, and URLs echoed raw |

**Admin panel (visible to admins):**

| File | Line(s) | Issue |
|------|---------|-------|
| `inc/function-options.php` | 338, 370, 379, 387, 406, 429, 439, 499, 509, 519, 530, 541, 606, 617, 695, 722, 738, 771, 781, 791, 801, 810, 818, 827, 839 | Form field values echoed without `esc_attr()` |
| `inc/vendors/envato-flex-slider/slider-img-type.php` | 64 | Meta box input value echoed without `esc_attr()` |

### D2. Input Sanitization (HIGH)
- `register_setting('govph_options','govph_options')` in `inc/function-options.php` line 214 has **no sanitization callback**. All values are saved as-is to the database.
- **Fix:** Add a sanitization callback that uses `sanitize_text_field()` for text values and `sanitize_hex_color()` for color values.

### D3. Nonce Verification (LOW)
- Slider meta box in `inc/vendors/envato-flex-slider/slider-img-type.php` correctly verifies nonces (line 80).
- Theme options page uses `settings_fields('govph_options')` which handles nonces via the Settings API.
- No AJAX endpoints found in the theme.

### D4. Capability Checks (LOW)
- Theme options page uses `'administrator'` capability in `add_theme_page()` (line 73). Should use `'manage_options'` capability instead for WordPress best practices.
- Slider meta box correctly checks `current_user_can('edit_post', $post_id)` (line 88).

---

## E. Performance Findings

### E1. Duplicate jQuery (HIGH)
- **File:** `inc/function-enqueue_scripts.php`
- **Issue:** Theme enqueues its own jQuery 3.6.0 as `gwt_wp-jquery` (line 17) but `gwt_wp-theme-js` depends on the core `jquery` handle (line 20). This causes WordPress to load both its bundled jQuery AND the theme's jQuery.
- **Fix:** Either deregister WordPress jQuery and register the theme's version under the `jquery` handle, or use WordPress's bundled jQuery:
```php
wp_deregister_script('jquery');
wp_register_script('jquery', get_template_directory_uri() . '/foundation/js/vendor/jquery-3.6.0.min.js', array(), '3.6.0', true);
```

### E2. Render-Blocking Scripts (MEDIUM)
- Both jQuery and Foundation JS are loaded in the `<head>` (5th parameter is `false` in `wp_enqueue_script`). These should be moved to the footer.
- **Fix:** Change to `true` for the `$in_footer` parameter.

### E3. Large Inline CSS Block (MEDIUM)
- `header.php` lines 28-201 contain a massive `<style>` block with PHP calls to `govph_displayoptions()`. This cannot be cached as an external file and increases document size on every page load.
- **Recommendation:** Generate this CSS via `wp_add_inline_style()` attached to the theme's main stylesheet handle.

### E4. External Script Dependencies (LOW)
- `footer.php` loads external scripts from `gwhs.i.gov.ph` (government footer and Philippine Standard Time) via inline `<script>` tags (lines 58-82). If this external server is slow or down, it can delay page rendering.

### E5. Stale Version Strings (LOW)
- All enqueued assets use hardcoded version `'20160530'`. This prevents proper cache busting when files are updated.
- **Fix:** Use the theme version or file modification time.

### E6. `query_posts()` Usage (MEDIUM)
- `inc/vendors/envato-flex-slider/envato-flex-slider.php` line 21 uses `query_posts()` which modifies the main query and is inefficient.
- **Fix:** Replace with `new WP_Query()`:
```php
$efs_query = new WP_Query('post_type=slider-image');
```

---

## F. Accessibility Findings

### F1. Missing Form Labels (HIGH)
- **File:** `searchform.php`
- **Issue:** Search input has no `<label>` element. Uses `title` and `placeholder` attributes, which are not sufficient for WCAG 2.0 compliance (Success Criterion 3.3.2).
- **Fix:**
```php
<label for="s" class="show-for-sr"><?php echo esc_html_x('Search for:', 'label', 'gwt_wp'); ?></label>
<input type="search" id="s" class="search-field" ... />
```

### F2. Text Resizer Limited to `<p>` Tags (MEDIUM)
- **File:** `js/theme.js`, lines 284-318
- **Issue:** Font size adjustment only targets `<p>` elements. Headings, lists, table cells, and other content types are not affected.
- **Fix:** Target a broader selector: `$('.entry-content *')` or use CSS custom properties.

### F3. Accessibility Toggle Buttons Missing Proper ARIA (MEDIUM)
- **File:** `header.php`, lines 331, 367
- **Issue:** Accessibility and magnifier buttons use `<button>` with nested dropdown menus but don't use `role="switch"` or `aria-expanded` attributes.
- **File:** `js/theme.js`, lines 146, 160
- **Issue:** `aria-checked` is used on links (`<a>`) without a `role="switch"` or `role="checkbox"`, which confuses screen readers.

### F4. Keyboard Focus Management (MEDIUM)
- **File:** `js/theme.js`, lines 321-331
- **Issue:** Mobile side-nav opens/closes by width manipulation but does not trap focus inside the open menu. Keyboard users can tab through the hidden page content.

### F5. Hardcoded Government Portal URL (LOW)
- **File:** `header.php`, line 295 and 306
- **Issue:** `http://www.gov.ph` and `https://www.gov.ph` are hardcoded. Should use `https://` consistently.

### F6. Skip Link Target Dependency (LOW)
- Skip links in `header.php` depend on theme option configuration (`govph_acc_link_main_content`). If not configured, the skip-to-content link defaults to `#main-content`, which may not exist on all pages.

---

## G. Maintainability Findings

### G1. Monolithic `function-options.php` (HIGH)
- At 1195 lines, `inc/function-options.php` handles the GOVPH class, admin UI, settings registration, AND the frontend `govph_displayoptions()` function. This should be split into:
  - `inc/class-govph-options.php` — the GOVPH class and admin settings
  - `inc/govph-display.php` — the `govph_displayoptions()` function

### G2. `govph_displayoptions()` Anti-Pattern (HIGH)
- This function uses a massive `switch` statement with 40+ cases. Some cases `echo` output, others `return` values, and some do both. This inconsistency makes the function unpredictable and hard to maintain.
- **Recommendation:** Split into dedicated functions: `govph_get_option()` for returning values, `govph_echo_option()` for echoing. Always return values and let the caller decide whether to echo.

### G3. Duplicated Code (MEDIUM)
- `inc/function-options.php` lines 990-1027: Three nearly identical column-width calculation blocks for panel-top, panel-bottom, and agency-footer positions. Should be extracted into a shared helper function.
- `functions.php` includes `inc/template-tags.php` twice (lines 51 and 81).
- Media uploader JavaScript in `inc/function-options.php` (lines 118-206): Three identical blocks for different upload buttons. Should be generalized.

### G4. Walker Classes Defined Inside `gwt_wp_setup()` (LOW)
- `Off_Canvass_Menu` and `Topbar_Nav_Menu` walker classes are defined inside the `gwt_wp_setup()` function in `inc/function-initialize.php`. They should be in their own files for maintainability and autoloading.

### G5. Translation Readiness (LOW)
- Text domain `'gwt_wp'` is used consistently.
- Some strings are not translatable: "You are here:" in `inc/function-breadcrumbs.php`, "Republic of the Philippines" in `inc/function-options.php` line 892, "GOVPH" in `header.php`.
- Admin labels like "Search Disabled", "Enable Image Logo" in `inc/function-options.php` are not wrapped in `__()`.

### G6. Child Theme Friendliness (LOW)
- Most functions are wrapped in `function_exists()` checks (good).
- `govph_displayoptions()` is not pluggable — child themes cannot override individual cases without replacing the entire function.

---

## H. File-by-File Recommendations

### `functions.php`
- **Line 81:** Duplicate `require get_template_directory() . '/inc/template-tags.php';` — remove.
- **Lines 105-108 (removed):** `block_frames()` X-Frame-Options function was correctly removed for twd compatibility. In production, consider re-adding with a filter to allow whitelisted origins.

### `header.php`
- **Line 20:** Replace `wp_title()` with `add_theme_support('title-tag')`.
- **Line 25:** Add `esc_url()`: `href="<?php echo esc_url(get_template_directory_uri()); ?>/favicon.ico"`.
- **Line 28:** Remove `<?php the_tags(); ?>` from `<style>` tag — produces invalid HTML.
- **Line 203:** Add `esc_url()`: `var template_directory = '<?php echo esc_url(get_template_directory_uri()); ?>';`.
- **Lines 214-232:** Add `esc_url()` to all accessibility link hrefs.
- **Line 295:** Change `http://www.gov.ph` to `https://www.gov.ph`.

### `footer.php`
- **Line 87:** "Back to top" link should have `aria-label="Back to top"`.

### `inc/function-options.php`
- **Line 65:** Guard `sizeof()` with `is_array()` check.
- **Line 73:** Change `'administrator'` to `'manage_options'`.
- **Line 91:** Change `apply_filters()` to `add_filter()` in `function-initialize.php`.
- **Line 214:** Add sanitization callback to `register_setting()`.
- **Lines 296-839:** Add `?? ''` null coalescing to all `$this->options[...]` accesses.
- **Lines 870-1194:** Add `isset()` / `?? ''` to all `$option[...]` accesses in `govph_displayoptions()`.
- **Lines 882-1193:** Add proper escaping (`esc_attr()`, `esc_html()`, `esc_url()`) to all output.
- **Lines 906, 1163, 1167, 1173, 1177:** Initialize variables before `.=` concatenation.

### `inc/function-enqueue_scripts.php`
- Fix jQuery handle conflict.
- Move scripts to footer where possible.
- Update version strings.

### `inc/function-initialize.php`
- **Line 36:** Uncomment `add_theme_support('title-tag')`.
- **Line 91:** Fix `apply_filters` to `add_filter`.

### `inc/function-breadcrumbs.php`
- **Line 9:** Add `isset()` check before accessing `$option['govph_breadcrumbs_enable']`.
- **Lines 12, 17, 29:** Add `isset()` and `?? ''` for option access.
- **Lines 48-49, 58, 61, 63:** Add `esc_html()` to title output and `esc_url()` to permalink output.

### `inc/template-tags.php`
- **Line 143:** Initialize `$next_id = null;` before the foreach loop.

### `inc/vendors/envato-flex-slider/envato-flex-slider.php`
- **Line 21:** Replace `query_posts()` with `new WP_Query()`.
- **Line 45:** Add `esc_url()` for link and `esc_html()` for caption.

### `inc/vendors/envato-flex-slider/slider-img-type.php`
- **Line 64:** Add `esc_attr()` to input value.
- **Line 92-93:** Use consistent `$_POST` instead of mixing `$_REQUEST`/`$_POST`.

### `searchform.php`
- Add `<label>` element for search input.

### `inc/extras.php`
- **Lines 51-71:** The `gwt_wp_wp_title` filter is only needed if `title-tag` support is not enabled. It should be conditionally loaded.

---

## I. Prioritized Remediation Roadmap

### Critical Fixes (Must Do Now)

1. **Add sanitization callback** to `register_setting()` in `inc/function-options.php`.
2. **Add output escaping** (`esc_html`, `esc_attr`, `esc_url`) to all theme option output in `govph_displayoptions()` and admin form fields.
3. **Fix PHP 8.x `sizeof()` fatal error** in `inc/function-options.php` constructor.
4. **Fix undefined array key warnings** throughout `inc/function-options.php` by adding `?? ''` / `isset()` checks.
5. **Fix undefined variables** (`$backgroundHeaderImageSizeSetting`, `$menuSetting`, `$menuFontSetting`, `$menuFontHoverSetting`, `$next_id`, `$val`).
6. **Fix duplicate jQuery** loading in `inc/function-enqueue_scripts.php`.
7. **Escape slider output** in `inc/vendors/envato-flex-slider/envato-flex-slider.php`.
8. **Fix `the_tags()` misuse** in `header.php` line 28.

### Important Improvements (Should Do Next)

9. **Enable `title-tag` support** and remove `wp_title()` usage.
10. **Replace `query_posts()`** with `WP_Query` in slider plugin.
11. **Add `<label>` to search form** for accessibility compliance.
12. **Fix `apply_filters` misuse** in `inc/function-initialize.php` line 91.
13. **Move render-blocking JS** to footer.
14. **Remove duplicate `template-tags.php` include** in `functions.php`.
15. **Fix breadcrumb option access** to prevent PHP 8.x warnings.
16. **Add ARIA attributes** to accessibility toggle buttons.
17. **Change capability** from `'administrator'` to `'manage_options'` in theme options page.
18. **Use HTTPS** for gov.ph links.

### Nice-to-Have Optimizations (Future Enhancements)

19. **Split `function-options.php`** into separate class and display function files.
20. **Refactor `govph_displayoptions()`** into dedicated return-value functions.
21. **Add `theme.json`** for block editor compatibility.
22. **Add block patterns** for government content structures.
23. **Move inline CSS** from `header.php` to `wp_add_inline_style()`.
24. **Expand text resizer** to target all content elements, not just `<p>`.
25. **Add focus trap** to mobile side navigation.
26. **Extract Walker classes** to separate files.
27. **Make hardcoded strings translatable** (breadcrumbs, government labels).
28. **Update Foundation** to latest version and review CSS/JS compatibility.
29. **Add child theme override points** (make `govph_displayoptions` pluggable).
30. **Update version strings** in enqueued assets for proper cache busting.

---

*End of Audit Report*
