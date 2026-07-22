# Boris toolchain routine

The site build depends on a compiled Boris binary. The binary must be treated as a release artifact from the Boris `afterparty` branch, not rebuilt opportunistically during a site change.

## Monthly intake

1. Identify the Boris repository and exact `afterparty` commit.
2. Build the platform binary from that commit:

   ```sh
   ./tools/boris-refresh.sh /path/to/boris afterparty zig-out/bin/boris
   ```

3. Record the repository, commit, target platform, and SHA-256 in `tooling/boris-toolchain.json`.
4. Run the graph check and site build:

   ```sh
   ./bin/boris check --input content
   ./build.sh
   git diff --check
   ```

5. Inspect the generated diff before merging the Boris update.

The refresh script uses a detached worktree, so it does not alter the Boris developer branch. It only replaces this repository's `bin/boris` after a successful build and executable-output check.

## Cloudflare requirement

The checked-in binary is currently macOS arm64. Before asking Cloudflare Pages to run `./build.sh`, add a Linux x86_64 Boris build and record its checksum. Until then, build `dist/` in CI or locally and deploy the static output rather than asking Cloudflare to execute the macOS binary.
