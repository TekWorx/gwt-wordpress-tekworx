<?php
/**
 * gwt_wp functions and definitions
 *
 * @package gwt_wp
 */

/**
 * Template Initialize
 */
require get_template_directory() . '/inc/function-initialize.php';

/**
 * Register widgetized area
 */
require get_template_directory() . '/inc/function-widget.php';

/**
 * Breadcrumbs
 */
require get_template_directory() . '/inc/function-breadcrumbs.php';

/**
 * Govph Excerpt
 */
require get_template_directory() . '/inc/function-excerpt.php';

/**
 * Enqueue scripts and styles
 */
require get_template_directory() . '/inc/function-enqueue_scripts.php';

/**
 * Disable comment functions
 */
require get_template_directory() . '/inc/function-disable_comments.php';

/**
 * GovPH default widgets
 */
require get_template_directory() . '/inc/govph-widget.php';

/**
 * Default sidebar contents
 */
require get_template_directory() . '/inc/sidebar.php';

/**
 * Custom template tags for this theme.
 */
require get_template_directory() . '/inc/template-tags.php';

/**
 * Custom functions that act independently of the theme templates.
 */
require get_template_directory() . '/inc/extras.php';

/**
 * Customizer additions.
 */
// require get_template_directory() . '/inc/customizer.php';

/**
 * Load Jetpack compatibility file.
 */
// require get_template_directory() . '/inc/jetpack.php';

/**
 * Theme Options Page.
 */
require get_template_directory() . '/inc/function-options.php';

/**
 * Custom Post Types
 */
// require get_template_directory() . '/inc/custom-post-types.php';

/**
 * Custom template tags for this theme.
 */
require get_template_directory() . '/inc/template-tags.php';

/**
 * Customizer additions.
 */
require get_template_directory() . '/inc/customizer.php';

/**
 * Envato Flexslider
 */
require get_template_directory() . '/inc/vendors/envato-flex-slider/envato-flex-slider.php';

/**
 * Disable rest api for users additions.
 */
require get_template_directory() . '/inc/function-disable_api.php';

/**
 * GWT only works in WordPress 4.4 or later.
 */
if ( version_compare( $GLOBALS['wp_version'], '4.4-alpha', '<' ) ) {
        require get_template_directory() . '/inc/back-compat.php';
}



function govph_fix_widget_theme_urls( $text ) {
    if ( is_admin() || ( defined( 'REST_REQUEST' ) && REST_REQUEST ) ) {
        return $text;
    }
    $current_uri = get_template_directory_uri();
    $text = preg_replace(
        '#https?://[^/\s"\']+/wp-content/themes/gwt-wordpress/#',
        $current_uri . '/',
        $text
    );
    return $text;
}
add_filter( 'widget_text', 'govph_fix_widget_theme_urls', 5 );
add_filter( 'widget_text_content', 'govph_fix_widget_theme_urls', 5 );

/**
 * Enable classic widgets or disabled gutenberg style for widgets.
 */
require get_template_directory() . '/inc/function-enable-classic-widgets.php';

/**
 * Enable classic posts or disabled gutenberg style for posts.
 */
require get_template_directory() . '/inc/function-enable-classic-posts.php';

?>