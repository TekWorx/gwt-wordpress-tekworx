<?php
/**
 * The template for displaying search forms in gwt_wp
 *
 * @package GWT
 * @since Government Website Template 2.0
 */
$gwt_search_id = wp_unique_id( 'search-field-' );
?>
<form role="search" method="get" class="search-form" action="<?php echo esc_url( home_url( '/' ) ); ?>">
    <label class="show-for-sr" for="<?php echo esc_attr( $gwt_search_id ); ?>"><?php echo esc_html_x( 'Search for:', 'label', 'gwt_wp' ); ?></label>
    <input type="search" class="search-field"
        id="<?php echo esc_attr( $gwt_search_id ); ?>"
        placeholder="<?php echo esc_attr_x( 'Search &hellip;', 'placeholder', 'gwt_wp' ); ?>"
        value="<?php echo esc_attr( get_search_query() ); ?>" name="s">
</form>