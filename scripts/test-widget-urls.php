<?php
/**
 * Regression checks using the local WordPress installation's real URL escaping.
 * Run: php scripts/test-widget-urls.php
 * Does not save widget options or change site content.
 */
define( 'WP_USE_THEMES', false );
$_SERVER['HTTP_HOST'] = 'localhost';
$_SERVER['REQUEST_URI'] = '/';
require dirname( __DIR__ ) . '/wp-site/wp-load.php';
require_once dirname( __DIR__ ) . '/inc/govph-widget.php';

function check_widget_url( $condition, $message ) {
    if ( ! $condition ) {
        fwrite( STDERR, "FAIL: $message\n" );
        exit( 1 );
    }
}

$widgets = array(
    'govph_widget_transparency' => 'http://domain.gov.ph/transparency',
    'govph_widget_foi'          => 'https://www.foi.gov.ph/',
);
$unsafe_urls = array(
    'javascript:alert(1)',
    'JaVaScRiPt:alert(1)',
    'java&#x73;cript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'vbscript:msgbox(1)',
    'ftp://example.com/file',
);
$safe_urls = array(
    'https://example.gov.ph/transparency',
    'http://example.gov.ph/foi',
    'https://example.gov.ph/?page=1&section=2',
    '/transparency/',
);

foreach ( $widgets as $class => $default_url ) {
    $widget = new $class();
    check_widget_url( $widget->update( array(), array() )['url'] === $default_url, "$class preserves its default URL" );
    check_widget_url( $widget->update( array( 'url' => '' ), array() )['url'] === $default_url, "$class preserves its empty-input default" );
    foreach ( $unsafe_urls as $url ) {
        check_widget_url( $widget->update( array( 'url' => $url ), array() )['url'] === '', "$class rejects unsafe schemes on save" );
        // Render the original value to cover malicious URLs already in storage.
        ob_start();
        $widget->widget( array( 'before_widget' => '<section>', 'after_widget' => '</section>' ), array( 'url' => $url ) );
        $html = ob_get_clean();
        check_widget_url( strpos( $html, 'href=""' ) !== false, "$class neutralizes stored unsafe schemes on output" );
    }
    foreach ( $safe_urls as $url ) {
        check_widget_url( $widget->update( array( 'url' => $url ), array() )['url'] === $url, "$class preserves valid URLs on save" );
        ob_start();
        $widget->widget( array( 'before_widget' => '<section>', 'after_widget' => '</section>' ), array( 'url' => $url ) );
        $html = ob_get_clean();
        check_widget_url( strpos( $html, 'href="' . esc_url( $url, array( 'http', 'https' ) ) . '"' ) !== false, "$class renders valid URLs with output escaping" );
    }
    $payload = 'https://example.gov.ph/" onclick="alert(1)';
    ob_start();
    $widget->widget( array( 'before_widget' => '', 'after_widget' => '' ), array( 'url' => $payload ) );
    $html = ob_get_clean();
    check_widget_url( strpos( $html, '" onclick="' ) === false, "$class prevents attribute injection" );
    ob_start();
    $widget->form( array( 'url' => $payload ) );
    $html = ob_get_clean();
    check_widget_url( strpos( $html, '" onclick="' ) === false, "$class escapes stored values in the admin form" );
    echo "PASS: $class save, stored URL output, valid links, defaults, and attribute injection\n";
}
