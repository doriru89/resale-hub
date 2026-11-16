#!/usr/bin/env sh
# Install the resale skill without the plugin system.
#
#   ./install.sh                  # skill -> ~/.claude/skills/resale (every project)
#   ./install.sh /path/to/project # skill -> that project's .claude/skills/resale
#
# The plugin install (see README) also adds the record-guard hook and the browser.
set -eu
here="$(cd "$(dirname "$0")" && pwd)"
if [ $# -ge 1 ]; then dest="$1/.claude/skills/resale"; else dest="$HOME/.claude/skills/resale"; fi
mkdir -p "$dest"
cp -R "$here/skills/resale/." "$dest/"
mkdir -p "${RESALE_BASE:-$HOME/resale}"
[ -f "${RESALE_BASE:-$HOME/resale}/config.yaml" ] || cp "$here/examples/config.yaml" "${RESALE_BASE:-$HOME/resale}/config.yaml"
echo "skill       -> $dest"
echo "data folder -> ${RESALE_BASE:-$HOME/resale}  (edit config.yaml there)"
command -v uv >/dev/null 2>&1 || echo "note: install uv (https://docs.astral.sh/uv/) to run the store"
