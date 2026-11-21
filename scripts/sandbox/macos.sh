#!/bin/bash
# This script sandboxes one bot process on macOS. Use it as the command prefix of `hkbench --sandbox`:
#
#   hkbench score ... --sandbox "scripts/sandbox/macos.sh --deny-read /path/to/deck.json --" --bot "python3 /bot/my_bot.py"
#
# It runs the bot under /usr/bin/sandbox-exec with a new profile for each launch:
#   * no network (sockets, including Unix ones);
#   * no fork, so the bot cannot start a descendant, a daemon or a setsid survivor (exec still works);
#   * writes only inside a new empty directory under a shared mode-0700 parent; HOME, TMPDIR, TMP and TEMP
#     point at it and the bot starts in it (unless --keep-cwd), and it is removed when the bot ends or is stopped;
#   * the parent's other directories (other bots' scratch) cannot be read, listed or even stat-ed;
#   * every --deny-read PATH (a file or a directory) cannot be read: give it the private deck;
#   * no POSIX shared memory and no registering of Mach services.
# Everything else on disk stays readable, so the deck must be named with --deny-read and must not sit
# in a place the bot is meant to read. sandbox-exec is deprecated by Apple but still works.
#
# Options (before the --):
#   --deny-read PATH   make PATH unreadable (repeat)
#   --allow-write PATH make PATH writable as well (repeat; for a cache the bot needs)
#   --keep-cwd         start the bot in the directory this wrapper was started in, not in the scratch
#                      (without it, give the bot's script by absolute path: a relative one is not found)
#   --allow-fork       leave fork allowed (only if a bot cannot start without it)
#   --allow-shm        leave POSIX shared memory and Mach registration allowed
# stdin, stdout and stderr go to the bot untouched, and the environment is passed through apart from HOME and the temp variables.

set -u

deny_read=()
allow_write=()
keep_cwd=0
allow_fork=0
allow_shm=0
while [ $# -gt 0 ]; do
  case "$1" in
    --deny-read) deny_read+=("$2"); shift 2 ;;
    --allow-write) allow_write+=("$2"); shift 2 ;;
    --keep-cwd) keep_cwd=1; shift ;;
    --allow-fork) allow_fork=1; shift ;;
    --allow-shm) allow_shm=1; shift ;;
    --) shift; break ;;
    *) echo "macos.sh: unknown option $1 (the bot's command goes after --)" >&2; exit 2 ;;
  esac
done
[ $# -gt 0 ] || { echo "macos.sh: no command after --" >&2; exit 2; }
SANDBOX_EXEC=/usr/bin/sandbox-exec
[ -x "$SANDBOX_EXEC" ] || { echo "macos.sh: $SANDBOX_EXEC not found" >&2; exit 2; }

# The real path of a file or directory that may not be a plain absolute path.
real() {
  local p="$1" d
  if [ -d "$p" ]; then (cd -P "$p" && pwd); return; fi
  d=$(cd -P "$(dirname "$p")" 2>/dev/null && pwd) || return 1
  echo "$d/$(basename "$p")"
}
quote() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

# One parent for every launch, mode 0700 and ours.
base=${HKSANDBOX_PARENT:-${TMPDIR:-/tmp}}
mkdir -p "$base" 2>/dev/null
parent="$(real "$base")/hkbench-sandbox-$(id -u)"
if [ -L "$parent" ]; then echo "macos.sh: $parent is a link" >&2; exit 2; fi
mkdir -m 700 "$parent" 2>/dev/null || true
if [ ! -d "$parent" ] || [ "$(stat -f %u "$parent")" != "$(id -u)" ]; then
  echo "macos.sh: cannot use $parent" >&2; exit 2
fi
chmod 700 "$parent"
parent=$(real "$parent")

# Remove what a launch that was killed outright left behind: its directory is named for its process.
for old in "$parent"/*; do
  [ -e "$old" ] || continue
  pid=${old##*/}; pid=${pid%%-*}
  case "$pid" in ''|*[!0-9]*) continue ;; esac
  kill -0 "$pid" 2>/dev/null || rm -rf "$old" "$old.sb"
done

scratch=$(mktemp -d "$parent/$$-XXXXXXXX") || exit 2
scratch=$(real "$scratch")
profile="$scratch.sb"

{
  echo '(version 1)'
  echo '(allow default)'
  echo '(deny network*)'
  [ "$allow_fork" = 1 ] || echo '(deny process-fork)'
  [ "$allow_shm" = 1 ] || { echo '(deny ipc-posix-shm*)'; echo '(deny mach-register)'; }
  echo '(deny file-write*)'
  echo "(allow file-write* (subpath \"$(quote "$scratch")\"))"
  echo '(allow file-write* (literal "/dev/null") (literal "/dev/tty") (literal "/dev/dtracehelper") (regex #"^/dev/fd/[0-9]+$"))'
  for w in ${allow_write[@]+"${allow_write[@]}"}; do
    echo "(allow file-write* (subpath \"$(quote "$(real "$w")")\"))"
  done
  # Other launches' directories are closed, and so is the parent's listing; only this one is open.
  echo "(deny file-read* (subpath \"$(quote "$parent")\"))"
  echo "(allow file-read-metadata (literal \"$(quote "$parent")\"))"
  echo "(allow file-read* (subpath \"$(quote "$scratch")\"))"
  for r in ${deny_read[@]+"${deny_read[@]}"}; do
    rp=$(real "$r") || { echo "macos.sh: --deny-read $r: cannot resolve" >&2; rm -rf "$scratch" "$profile"; exit 2; }
    echo "(deny file-read* (subpath \"$(quote "$rp")\"))"
  done
} > "$profile"

child=""
cleanup() { rm -rf "$scratch" "$profile"; }
on_signal() {
  trap '' TERM INT HUP
  [ -n "$child" ] && kill -TERM "$child" 2>/dev/null
  [ -n "$child" ] && wait "$child" 2>/dev/null
  cleanup
  exit 143
}
trap on_signal TERM INT HUP
trap cleanup EXIT

export HOME="$scratch" TMPDIR="$scratch" TMP="$scratch" TEMP="$scratch"
[ "$keep_cwd" = 1 ] || cd "$scratch" || exit 2

# Run it as a child (not exec) so the scratch can be removed afterwards and on a signal. stdin is passed
# on explicitly: a background command would otherwise get /dev/null.
"$SANDBOX_EXEC" -f "$profile" "$@" <&0 &
child=$!
wait "$child"
status=$?
child=""
exit $status
