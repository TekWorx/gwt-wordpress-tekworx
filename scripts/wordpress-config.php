<?php
/**
 * Installed by prepare-security.php. No credentials belong in this file.
 * This installation uses SQLite, not a password-authenticated MySQL server.
 */
$master = getenv('SESSION_SECRET');
if (!is_string($master) || strlen($master) < 32) {
    throw new RuntimeException('SESSION_SECRET must contain at least 32 characters.');
}
foreach (['AUTH_KEY', 'SECURE_AUTH_KEY', 'LOGGED_IN_KEY', 'NONCE_KEY',
          'AUTH_SALT', 'SECURE_AUTH_SALT', 'LOGGED_IN_SALT', 'NONCE_SALT'] as $name) {
    // Domain separation gives each key an independent value. Changing the
    // master invalidates cookies and nonces; the label rotates the leaked keys.
    define($name, hash_hmac('sha512', 'gwt-wordpress-security-v1:' . $name, $master));
}
unset($master, $name);

define('DB_NAME', 'wordpress');
define('DB_USER', '');
define('DB_PASSWORD', '');
define('DB_HOST', '');
define('DB_CHARSET', 'utf8mb4');
define('DB_COLLATE', '');
$table_prefix = 'wp_';
define('WP_DEBUG', false);
define('WP_DEBUG_LOG', false);
define('WP_DEBUG_DISPLAY', false);
@ini_set('display_errors', '0');

require_once __DIR__ . '/../scripts/wordpress-site-url.php';
if (!defined('ABSPATH')) {
    define('ABSPATH', __DIR__ . '/');
}
require_once ABSPATH . 'wp-settings.php';
