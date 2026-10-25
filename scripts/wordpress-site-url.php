<?php
/**
 * Load before wp-settings.php. Site identity comes from deployment configuration,
 * never request headers, including when TLS terminates at a reverse proxy.
 */
// Only an explicit development environment permits a local HTTP fallback.
$production = getenv('APP_ENV') !== 'development';
$siteUrl = getenv('WORDPRESS_SITE_URL');
if ($siteUrl === false || $siteUrl === '') {
    if ($production) {
        throw new RuntimeException('WORDPRESS_SITE_URL must be configured for production.');
    }
    $siteUrl = 'http://localhost:5000';
}

$parts = parse_url($siteUrl);
if ($parts === false
    || !filter_var($siteUrl, FILTER_VALIDATE_URL)
    || preg_match('/[\x00-\x20\x7f\\\\]/', $siteUrl)
    || !in_array($parts['scheme'] ?? '', ['http', 'https'], true)
    || empty($parts['host'])
    || isset($parts['user']) || isset($parts['pass'])
    || isset($parts['query']) || isset($parts['fragment'])
    || ($production && $parts['scheme'] !== 'https')
) {
    throw new RuntimeException('WORDPRESS_SITE_URL must be a valid HTTP(S) URL without credentials, query, or fragment; production requires HTTPS.');
}
$siteUrl = rtrim($siteUrl, '/');
foreach (['WP_HOME', 'WP_SITEURL'] as $constant) {
    if (defined($constant) && constant($constant) !== $siteUrl) {
        throw new RuntimeException('Conflicting WordPress canonical URL configuration.');
    }
    if (!defined($constant)) {
        define($constant, $siteUrl);
    }
}

// Keep core redirects, secure cookies, and plugin URL generation consistent.
// No proxy-header trust is needed: the configured public URL fixes the scheme.
$_SERVER['HTTP_HOST'] = $parts['host'] . (isset($parts['port']) ? ':' . $parts['port'] : '');
$_SERVER['SERVER_NAME'] = $parts['host'];
$_SERVER['HTTPS'] = $parts['scheme'] === 'https' ? 'on' : 'off';
$_SERVER['REQUEST_SCHEME'] = $parts['scheme'];
$_SERVER['SERVER_PORT'] = (string) ($parts['port'] ?? ($parts['scheme'] === 'https' ? 443 : 80));
foreach (array_keys($_SERVER) as $header) {
    if ($header === 'HTTP_FORWARDED' || str_starts_with($header, 'HTTP_X_FORWARDED_')) {
        unset($_SERVER[$header]);
    }
}
unset($production, $siteUrl, $parts, $constant, $header);
