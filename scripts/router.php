<?php
/**
 * Access guard for PHP's built-in server, which does not enforce .htaccess.
 * Keep this outside the document root and always pass it to `php -S`.
 */

$deny = static function (): void {
    http_response_code(404);
    header('Content-Type: text/plain; charset=UTF-8');
    header('Cache-Control: no-store');
    echo "Not Found\n";
};

$root = realpath(__DIR__ . '/../wp-site');
$themeRoot = realpath(__DIR__ . '/..');
$path = rawurldecode(explode('?', $_SERVER['REQUEST_URI'] ?? '/', 2)[0]);

// Decode exactly once, reject ambiguous encodings and path separators, and
// check every segment before letting the server perform static-file handling.
if ($root === false || $path === '' || $path[0] !== '/'
    || preg_match('/[%\\\\\x00-\x1f\x7f]/', $path)
) {
    $deny();
    return true;
}

$segments = explode('/', $path);
foreach ($segments as $segment) {
    if (($segment !== '' && $segment[0] === '.')
        || preg_match('/^(?:wp-config(?:-sample)?\.php|database)$/i', $segment)
    ) {
        $deny();
        return true;
    }
}

// WordPress drop-ins are loaded by core, never public request entry points.
// Enforce this here rather than editing generated/vendor-managed PHP files.
if (preg_match('~^/+wp-content/+(?:advanced-cache|db|db-error|install|maintenance|object-cache|php-error|fatal-error-handler|sunrise)\.php(?:/|$)~i', $path)) {
    $deny();
    return true;
}

// Allow only public asset types. In particular, database files, WAL/journal
// sidecars, dumps, logs, backups, config files and shell scripts are not assets.
$publicExtensions = [
    'css', 'js', 'mjs', 'json', 'html', 'htm',
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif', 'svg', 'ico',
    'woff', 'woff2', 'ttf', 'otf', 'eot',
    'pdf', 'mp3', 'mp4', 'm4a', 'ogg', 'ogv', 'wav', 'webm', 'vtt',
];
$extension = strtolower(pathinfo($path, PATHINFO_EXTENSION));
if ($extension !== '' && $extension !== 'php' && !in_array($extension, $publicExtensions, true)) {
    $deny();
    return true;
}
if (preg_match('~(?:^|/)(?:composer|package)(?:-lock)?\.json$~i', $path)) {
    $deny();
    return true;
}

$target = realpath($root . $path);
$inside = static function (string $file, string $directory): bool {
    return $file === $directory || str_starts_with($file, $directory . DIRECTORY_SEPARATOR);
};

// The local theme is a symlink to the workspace. Only its public asset
// folders and root CSS/images may be fetched, not arbitrary workspace files.
$themePrefix = '/wp-content/themes/gwt-wordpress/';
if (str_starts_with($path, $themePrefix)) {
    $relative = substr($path, strlen($themePrefix));
    $assetFolder = preg_match('~^(?:css|js|images|fonts|genericons|foundation|accessibility)/~', $relative);
    $rootAsset = !str_contains($relative, '/') && in_array($extension, ['css', 'png', 'ico'], true);
    if ($target === false || !is_file($target) || !$inside($target, $themeRoot)
        || !($assetFolder || $rootAsset) || !in_array($extension, $publicExtensions, true)
    ) {
        $deny();
        return true;
    }
    // A symlink in a public asset folder must not point back into WordPress
    // or another non-public workspace directory.
    $expected = $themeRoot . '/' . $relative;
    if ($target !== $expected) {
        $deny();
        return true;
    }
    return false;
}

if ($target !== false) {
    // Apart from the explicitly supported theme link above, do not follow
    // symlinks: a harmless-looking asset alias could expose a private file.
    $normalizedPath = '/' . implode('/', array_filter($segments, static fn ($part) => $part !== ''));
    $relativeTarget = substr($target, strlen($root));
    if (!$inside($target, $root)
        || $target !== rtrim($root . $normalizedPath, '/')
        || preg_match('~(?:^|/)(?:\.[^/]*|database|wp-config(?:-sample)?\.php)(?:/|$)~i', $relativeTarget)
    ) {
        $deny();
        return true;
    }
    if (is_file($target)) {
        if (pathinfo($target, PATHINFO_EXTENSION) === 'php' || in_array($extension, $publicExtensions, true)) {
            return false;
        }
        $deny();
        return true;
    }
    if (is_dir($target) && is_file($target . '/index.php')
        && realpath($target . '/index.php') === $target . '/index.php'
    ) {
        return false;
    }
    $deny();
    return true;
}

// Preserve WordPress pretty permalinks and REST routes.
$_SERVER['SCRIPT_NAME'] = '/index.php';
$_SERVER['SCRIPT_FILENAME'] = $root . '/index.php';
require $root . '/index.php';
return true;
