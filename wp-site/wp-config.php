<?php
/**
 * WordPress Configuration for GWT WordPress Theme
 * Using SQLite database via the sqlite-database-integration plugin.
 */

define( 'DB_NAME', 'wordpress' );
define( 'DB_USER', 'wordpress' );
define( 'DB_PASSWORD', 'wordpress' );
define( 'DB_HOST', 'localhost' );
define( 'DB_CHARSET', 'utf8mb4' );
define( 'DB_COLLATE', '' );

define('AUTH_KEY',         'x4 Mm|m)t[wxx#~;R>qvCI%M4U:j8p2GNMXh}*%at|I3-ic1mC>|K+7x>%4[Z!PQ');
define('SECURE_AUTH_KEY',  'r4-~>d<1+p_O(Xlr;paUT2|E|sZmy+BBZQeQ[sGRApq-qT~,}V0(c^+R!><w#O[L');
define('LOGGED_IN_KEY',    '4siV;|z]U?9n4(|6-1+5*(+;`2_o>b-@Fa+y]]|0Jwb=ztv9M~J?O&67+{wYZO;a');
define('NONCE_KEY',        'OzyVV+Rxx|w:axtioGUM|V+f8KNASb_}bY{!FZVqQ,Mk`4EbnCusa4+8}1h3|&0W');
define('AUTH_SALT',        'l0f{|l/ ;x{_Nu=JGHu^<zW(c-/j3p2vYluW5|8BngluP0Jwev.WEn8]oCuC;jPd');
define('SECURE_AUTH_SALT', '<;^x,3+vTT%BVVB_;KG5l>Ho-SxvOT!O8C p`jt&I%-?z8,0qxzQI|`?v[Em+Plt');
define('LOGGED_IN_SALT',   'ub1mmjL,|B_nx,3_?$#l#3fWbdz_6u|,wYZVDJ9NT8& 97v25ZhC0=<) |7W|yB$');
define('NONCE_SALT',       'bUN,|>GqB(+.j.|.B+D|KGv-u@9]G[Rs/<J,d0 C=vb}w~6krDfe/G2.ss-yo)N^');

$table_prefix = 'wp_';

define( 'WP_DEBUG', false );
define( 'WP_DEBUG_LOG', false );
define( 'WP_DEBUG_DISPLAY', false );
error_reporting( 0 );
@ini_set( 'display_errors', 0 );

if (
    ( isset( $_SERVER['HTTP_X_FORWARDED_PROTO'] ) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https' ) ||
    ( isset( $_SERVER['HTTP_X_FORWARDED_SSL'] )   && $_SERVER['HTTP_X_FORWARDED_SSL']   === 'on' )    ||
    ( isset( $_SERVER['HTTP_X_FORWARDED_PORT'] )   && $_SERVER['HTTP_X_FORWARDED_PORT']  == '443' )    ||
    ( isset( $_SERVER['SERVER_PORT'] )             && $_SERVER['SERVER_PORT']             == '443' )
) {
    $_SERVER['HTTPS'] = 'on';
}
$protocol = ( ! empty( $_SERVER['HTTPS'] ) && $_SERVER['HTTPS'] !== 'off' ) ? 'https' : 'http';
$host     = ! empty( $_SERVER['HTTP_HOST'] ) ? $_SERVER['HTTP_HOST'] : 'localhost:5000';
$site_url = $protocol . '://' . $host;

define( 'WP_HOME', $site_url );
define( 'WP_SITEURL', $site_url );

if ( ! defined( 'ABSPATH' ) ) {
    define( 'ABSPATH', __DIR__ . '/' );
}

require_once ABSPATH . 'wp-settings.php';
