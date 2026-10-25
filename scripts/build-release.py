#!/usr/bin/env python3
"""Build a curated WordPress theme ZIP without site or workspace data."""
import argparse
from pathlib import Path
import re
import zipfile


ROOT = Path(__file__).resolve().parent.parent
SLUG = "gwt-wordpress"
ROOT_FILES = (
    "404.php", "archive.php", "comments.php", "favicon.ico", "footer.php",
    "functions.php", "header.php", "image.php", "index.php", "page.php",
    "rtl.css", "screenshot.png", "search.php", "searchform.php",
    "sidebar-left.php", "sidebar-panel-bottom.php", "sidebar-panel-top.php",
    "sidebar-right.php", "single.php", "style.css", "theme.css",
    "README.md", "CHANGELOG.md", "INSTALL.md", "SECURITY.md", "CONTRIBUTING.md",
)
ASSET_DIRS = (
    "accessibility", "css", "fonts", "foundation", "genericons", "images",
    "inc", "js", "languages", "template-parts",
)
PRIVATE_SUFFIXES = {
    ".sql", ".sqlite", ".sqlite3", ".db", ".bak", ".backup", ".pem", ".key",
}
PUBLIC_SUFFIXES = {
    ".php", ".css", ".js", ".mjs", ".json", ".map", ".html", ".htm",
    ".txt", ".md", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif",
    ".svg", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".po", ".mo", ".pot", ".scss", ".sass", ".less",
}


def check_member(root, path, forbidden_text=()):
    """Fail closed on links, private filenames, or unexpected text attribution."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if part.startswith(".") or current.is_symlink():
            raise ValueError("Hidden files and symbolic links are not release inputs.")
    if not path.is_file():
        raise ValueError("A required theme release input is missing.")
    if path.suffix.lower() in PRIVATE_SUFFIXES or path.name.lower().startswith("wp-config"):
        raise ValueError("Private configuration or database file in release inputs.")
    if path.suffix.lower() not in PUBLIC_SUFFIXES and path.name.upper() not in {
        "LICENSE", "COPYING", "NOTICE", "AUTHORS",
    }:
        raise ValueError("Unexpected file type in release inputs.")
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Oversized release input requires explicit review.")
    data = path.read_bytes()
    if any(term.encode("utf-8").lower() in data.lower() for term in forbidden_text if term):
        raise ValueError("Forbidden public wording in release inputs.")
    if re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", data):
        raise ValueError("Private key material in release inputs.")
    return relative


def collect_files(root=ROOT, forbidden_text=()):
    files = [root / name for name in ROOT_FILES]
    for directory in ASSET_DIRS:
        folder = root / directory
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError("A required asset directory is missing or linked.")
        for path in folder.rglob("*"):
            if path.is_symlink():
                raise ValueError("Symbolic links are not release inputs.")
            if path.is_file():
                files.append(path)
    for path in files:
        check_member(root, path, forbidden_text)
    return sorted(files)


def theme_version(root=ROOT):
    style = (root / "style.css").read_text()
    match = re.search(r"^\s*\*?\s*Version:\s*(\d+\.\d+\.\d+)\s*$", style, re.M)
    if not match:
        raise ValueError("Theme version must be a three-part numeric version.")
    return match.group(1)


def build(output, root=ROOT, forbidden_text=()):
    files = collect_files(root, forbidden_text)
    version = theme_version(root)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Validate all inputs before opening or replacing a package.
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(root)
            member = zipfile.ZipInfo(f"{SLUG}/{relative.as_posix()}")
            member.external_attr = 0o100644 << 16
            archive.writestr(member, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    return {"version": version, "files": len(files), "bytes": output.stat().st_size}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--forbid-text", action="append", default=[],
                        help="Reject a reviewed term in any package file; repeat as needed.")
    args = parser.parse_args()
    destination = args.output or ROOT / "generated-artifacts" / f"{SLUG}-{theme_version()}.zip"
    try:
        result = build(destination, forbidden_text=args.forbid_text)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Release build failed: {error}\n")
    print(f"Built {destination.name}: {result['files']} files, {result['bytes']} bytes.")
