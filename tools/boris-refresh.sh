#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
  echo "usage: $0 BORIS_REPOSITORY BORIS_REF BORIS_OUTPUT" >&2
  echo "example: $0 ../boris afterparty zig-out/bin/boris" >&2
  exit 2
fi

boris_repo=$1
boris_ref=$2
boris_output=$3
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
worktree_root=$(mktemp -d "${TMPDIR:-/tmp}/boris-afterparty.XXXXXX")

cleanup() {
  git -C "$boris_repo" worktree remove --force "$worktree_root" >/dev/null 2>&1 || true
  rmdir "$worktree_root" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

git -C "$boris_repo" rev-parse --show-toplevel >/dev/null
if ! git -C "$boris_repo" show-ref --verify --quiet "refs/heads/$boris_ref" && \
   ! git -C "$boris_repo" show-ref --verify --quiet "refs/remotes/origin/$boris_ref"; then
  echo "Boris ref not found: $boris_ref" >&2
  exit 1
fi

boris_commit=$(git -C "$boris_repo" rev-parse "$boris_ref")
git -C "$boris_repo" worktree add --detach "$worktree_root" "$boris_commit" >/dev/null

if ! command -v zig >/dev/null 2>&1; then
  echo "zig is required to build Boris from the afterparty source" >&2
  exit 1
fi

(
  cd "$worktree_root"
  zig build -Doptimize=ReleaseSafe
)

built_binary="$worktree_root/$boris_output"
if [ ! -x "$built_binary" ]; then
  echo "Boris build completed, but output was not executable: $boris_output" >&2
  exit 1
fi

install -m 755 "$built_binary" "$repo_root/bin/boris"
sha256=$(shasum -a 256 "$repo_root/bin/boris" | awk '{print $1}')
cat <<EOF
Built Boris commit: $boris_commit
Installed: $repo_root/bin/boris
SHA-256: $sha256

Update tooling/boris-toolchain.json with the repository, commit, platform, and checksum,
then run ./build.sh and ./bin/boris check --input content before committing.
EOF
