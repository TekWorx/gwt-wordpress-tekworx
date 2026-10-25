<?php
/**
 * Fail-closed, idempotent security provisioning, before the HTTP listener opens.
 * Secrets are consumed only by application code; never print their values.
 */
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
$root = dirname(__DIR__);
try {
    $master = getenv('SESSION_SECRET');
    if (!is_string($master) || strlen($master) < 32) {
        throw new RuntimeException('Set SESSION_SECRET to a random value of at least 32 characters in Secrets.');
    }
    unset($master);
    $password = getenv('WP_ADMIN_PASSWORD');
    if ($password !== false && (strlen($password) < 20 || strlen($password) > 4096)) {
        throw new RuntimeException('WP_ADMIN_PASSWORD must be a unique password of 20–4096 characters.');
    }
    // Refuse to silently replace a MySQL installation's configuration.
    $dropin = $root . '/wp-site/wp-content/db.php';
    if (!is_file($dropin) || !str_contains(file_get_contents($dropin), 'sqlite-database-integration')
        || !is_file($root . '/wp-site/wp-content/plugins/sqlite-database-integration/wp-includes/sqlite/db.php')) {
        throw new RuntimeException('The expected SQLite integration is required; configuration was not changed.');
    }
    $install = static function (string $source, string $destination): void {
        if (is_file($destination) && hash_file('sha256', $source) === hash_file('sha256', $destination)) {
            return;
        }
        $temporary = tempnam(dirname($destination), '.security-');
        if ($temporary === false || !chmod($temporary, 0600) || !copy($source, $temporary)
            || !rename($temporary, $destination)) {
            throw new RuntimeException('Cannot install WordPress security configuration.');
        }
    };
    $install(__DIR__ . '/wordpress-config.php', $root . '/wp-site/wp-config.php');
    $plugins = $root . '/wp-site/wp-content/mu-plugins';
    if (!is_dir($plugins) && !mkdir($plugins, 0755, true)) {
        throw new RuntimeException('Cannot create the security plugin directory.');
    }
    $install(__DIR__ . '/wordpress-login-security.php', $plugins . '/gwt-login-security.php');

    require $root . '/wp-site/wp-load.php';
    if (!defined('DB_ENGINE') || DB_ENGINE !== 'sqlite') {
        throw new RuntimeException('SQLite integration did not load.');
    }
    require_once ABSPATH . 'wp-admin/includes/user.php';
    global $wpdb;
    $legacy = get_user_by('login', 'admin');
    if ($legacy) {
        $replacement = 'site-manager';
        if (get_user_by('login', $replacement)) {
            throw new RuntimeException('Cannot rename the default administrator: site-manager already exists.');
        }
        $result = $wpdb->update($wpdb->users, [
            'user_login' => $replacement,
            'user_nicename' => $replacement,
        ], ['ID' => $legacy->ID]);
        if ($result !== 1) {
            throw new RuntimeException('Cannot rename the default administrator.');
        }
        clean_user_cache($legacy->ID);
        update_user_meta($legacy->ID, '_gwt_managed_admin', 1);
    }
    $administrators = get_users(['role' => 'administrator']);
    // Snapshot the affected accounts once. Administrators created normally
    // after remediation must not lose their chosen password on a later restart.
    $exposedIds = get_option('_gwt_exposed_admin_ids', null);
    if (!is_array($exposedIds)) {
        $exposedIds = array_map(static fn ($user) => (int) $user->ID, $administrators);
        update_option('_gwt_exposed_admin_ids', $exposedIds, false);
        if (get_option('_gwt_exposed_admin_ids', null) !== $exposedIds) {
            throw new RuntimeException('Cannot record the initial credential rotation scope.');
        }
    }
    foreach ($administrators as $admin) {
        $managed = (bool) get_user_meta($admin->ID, '_gwt_managed_admin', true);
        $rotated = (bool) get_user_meta($admin->ID, '_gwt_credentials_rotated', true);
        $desired = $managed && $password !== false ? $password : null;
        $secretConfigured = (bool) get_user_meta($admin->ID, '_gwt_admin_secret_configured', true);
        $secretRemoved = $managed && $secretConfigured && $desired === null;
        $initialRotation = !$rotated && in_array((int) $admin->ID, $exposedIds, true);
        if ($initialRotation || ($legacy && $legacy->ID === $admin->ID)
            || $secretRemoved
            || ($desired !== null && !wp_check_password($desired, $admin->user_pass, $admin->ID))) {
            $nextPassword = $desired ?? bin2hex(random_bytes(48));
            wp_set_password($nextPassword, $admin->ID);
            $updated = get_userdata($admin->ID);
            if (!$updated || !wp_check_password($nextPassword, $updated->user_pass, $admin->ID)) {
                throw new RuntimeException('Cannot rotate administrator credentials.');
            }
            unset($nextPassword);
            // Revoke sessions and alternate credentials exposed with the DB.
            WP_Session_Tokens::get_instance($admin->ID)->destroy_all();
            WP_Application_Passwords::delete_all_application_passwords($admin->ID);
            update_user_meta($admin->ID, '_gwt_credentials_rotated', 1);
        }
        if ($managed && $secretConfigured !== ($desired !== null)) {
            update_user_meta($admin->ID, '_gwt_admin_secret_configured', $desired !== null ? 1 : 0);
        }
    }
    if ($wpdb->last_error !== '') {
        throw new RuntimeException('Database reported an error during security provisioning.');
    }
    unset($password, $desired);
    echo "WordPress security configuration and administrator hardening applied.\n";
    if (getenv('WP_ADMIN_PASSWORD') === false) {
        echo "Default administrator access is disabled. Set WP_ADMIN_PASSWORD in Secrets and restart to enable site-manager access.\n";
    }
} catch (Throwable $error) {
    // Do not include exception details from database or secret-processing code.
    fwrite(STDERR, "WordPress security setup failed. Check SQLite integration and required Secrets; HTTP server was not started.\n");
    exit(1);
}
