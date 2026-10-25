<?php
/**
 * Plugin Name: GWT Login Security
 * Description: Persistent authentication throttling for browser and XML-RPC logins.
 */
defined('ABSPATH') || exit;

function gwt_login_buckets(string $username): array {
    // Never trust a client-supplied forwarding header for rate-limit identity.
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    return [
        'gwt_login_user_' . hash('sha256', strtolower(trim($username))) => 5,
        'gwt_login_ip_' . hash('sha256', $ip) => 50,
    ];
}

function gwt_login_locked(string $username): bool {
    foreach (gwt_login_buckets($username) as $key => $limit) {
        $bucket = get_transient($key);
        if (is_array($bucket) && $bucket['until'] > time() && $bucket['count'] >= $limit) {
            return true;
        }
    }
    return false;
}

function gwt_login_limit_error(): WP_Error {
    return new WP_Error('gwt_login_throttled', __('Too many login attempts. Try again in 15 minutes.'));
}

add_filter('authenticate', static function ($user, $username) {
    return gwt_login_locked((string) $username) ? gwt_login_limit_error() : $user;
}, 1, 2);

// Run after core's authenticate filters so a valid password cannot bypass a
// lock. Unknown users receive the same limits. REST application-password auth
// uses determine_current_user instead and is outside this login throttle.
add_filter('authenticate', static function ($user, $username) {
    if (gwt_login_locked((string) $username)) {
        return gwt_login_limit_error();
    }
    if (is_wp_error($user) && $username !== '') {
        foreach (gwt_login_buckets((string) $username) as $key => $limit) {
            $bucket = get_transient($key);
            if (!is_array($bucket) || $bucket['until'] <= time()) {
                $bucket = ['count' => 0, 'until' => time() + 15 * MINUTE_IN_SECONDS];
            }
            ++$bucket['count'];
            set_transient($key, $bucket, max(1, $bucket['until'] - time()));
        }
    }
    return $user;
}, 100, 2);
