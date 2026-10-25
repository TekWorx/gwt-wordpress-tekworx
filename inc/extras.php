<?php
/**
 * Custom functions that act independently of the theme templates
 *
 * Eventually, some of the functionality here could be replaced by core features
 *
 * @package GWT
 * @since Government Website Template 2.0
 */

/**
 * Get our wp_nav_menu() fallback, wp_page_menu(), to show a home link.
 */
function gwt_wp_page_menu_args( $args ) {
        $args['show_home'] = true;
        return $args;
}
add_filter( 'wp_page_menu_args', 'gwt_wp_page_menu_args' );

/**
 * Adds custom classes to the array of body classes.
 */
function gwt_wp_body_classes( $classes ) {
        // Adds a class of group-blog to blogs with more than 1 published author
        if ( is_multi_author() ) {
                $classes[] = 'group-blog';
        }

        return $classes;
}
add_filter( 'body_class', 'gwt_wp_body_classes' );

/**
 * Filter in a link to a content ID attribute for the next/previous image links on image attachment pages
 */
function gwt_wp_enhanced_image_navigation( $url, $id ) {
        if ( ! is_attachment() && ! wp_attachment_is_image( $id ) )
                return $url;

        $image = get_post( $id );
        if ( ! empty( $image->post_parent ) && $image->post_parent != $id )
                $url .= '#main';

        return $url;
}
add_filter( 'attachment_link', 'gwt_wp_enhanced_image_navigation', 10, 2 );

/**
 * Filters document title parts for a proper <title> tag via title-tag support.
 */
function gwt_wp_document_title_parts( $title_parts ) {
        $site_description = get_bloginfo( 'description', 'display' );
        if ( $site_description && ( is_home() || is_front_page() ) ) {
                $title_parts['tagline'] = $site_description;
        }

        return $title_parts;
}
add_filter( 'document_title_parts', 'gwt_wp_document_title_parts' );