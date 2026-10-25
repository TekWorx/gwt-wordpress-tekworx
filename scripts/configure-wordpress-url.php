<?php
/**
 * Idempotently replace only the known legacy URL block in the untracked local
 * config. Never print its contents or touch credentials/database settings.
 */
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
$configPath = $argv[1] ?? dirname(__DIR__) . '/wp-site/wp-config.php';
$config = file_get_contents($configPath);
if ($config === false) {
    throw new RuntimeException('Cannot read WordPress configuration.');
}
$include = "require_once __DIR__ . '/../scripts/wordpress-site-url.php';";
$legacy = <<<'PHP'
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
PHP;
$newline = str_contains($config, "\r\n") ? "\r\n" : "\n";
$legacy = str_replace("\n", $newline, $legacy);
if (substr_count($config, $legacy) === 1 && !str_contains($config, $include)) {
    $updated = str_replace($legacy, $include, $config);
    if (file_put_contents($configPath, $updated, LOCK_EX) !== strlen($updated)) {
        throw new RuntimeException('Cannot update WordPress URL configuration.');
    }
    echo "Installed trusted WordPress URL configuration.\n";
} elseif (substr_count($config, $include) === 1 && !str_contains($config, $legacy)) {
    echo "Trusted WordPress URL configuration is already installed.\n";
} else {
    // Do not guess at, or broadly rewrite, an unfamiliar wp-config.php.
    throw new RuntimeException('Unrecognized WordPress URL configuration; manual review required.');
}
