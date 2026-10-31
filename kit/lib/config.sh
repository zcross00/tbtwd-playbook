# Sourced by the kit's shell scripts: `cfg KEY DEFAULT` prints a setting from
# the project's .playbook.toml, or DEFAULT when it can't be read.
_kit="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cfg() {
  local v
  v=$(bash "$_kit/python.sh" "$_kit/lib/playbook_config.py" "$1" 2>/dev/null) || v=""
  v=${v%$'\r'}
  printf '%s' "${v:-$2}"
}
