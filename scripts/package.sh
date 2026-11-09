#!/usr/bin/env bash
# Build the installable package: dist/yace-themes-<version>.tar.gz
# Needs `yace` on PATH (or $YACE): `yace --package-plugin` validates the
# manifest and every theme file, and prints the package's SHA-256.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
yace="${YACE:-yace}"
id="$(sed -n 's/^id = "\(.*\)"/\1/p' "$root/yace-plugin.toml")"
version="$(sed -n 's/^version = "\(.*\)"/\1/p' "$root/yace-plugin.toml")"
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/$id" "$root/dist"
cp -r "$root/yace-plugin.toml" "$root/themes" "$root/README.md" "$root/LICENSE-MIT" "$root/LICENSE-APACHE" "$stage/$id/"
"$yace" --package-plugin "$stage/$id" -o "$root/dist/yace-themes-$version.tar.gz"
