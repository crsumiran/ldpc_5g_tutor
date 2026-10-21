# Security Model

This file describes runtime separation inside the tutor. The GitHub repository is public and includes the cache reference RTL and testbenches marked hidden by the runtime. Anyone with repository access can read them, so they are not confidential grading assets. Do not rely on these files as secret tests.

1. Local import roots: only paths under `ALLOWED_IMPORT_ROOTS` (env, default `/home/ranga/opencode`).
2. ZIP: reject absolute paths, `..`, overwrites outside dest, files > 5 MiB, total uncompressed > 50 MiB.
3. Git: `git clone --depth 1 --single-branch --recurse-submodules=no`. Do not copy `.git` hooks into the snapshot. Strip `.git` after clone.
4. Symlinks in snapshots: refuse if target is outside the snapshot.
5. Analysis never runs project code, `setup.py`, or Makefile.
6. Secrets: skip files named `.env`, `.env.*`, `id_rsa`, `*.pem`, `credentials.json` from LLM excerpts.
7. Sandbox: `network_disabled=True`, `cap_drop=["ALL"]`, `read_only=True`, `no-new-privileges`, mem `512m`, cpus `1.0`, timeout 30s, tmpfs `/tmp` and `/work`.
8. Learner mounts: workspace only. Never `reference/`, never hidden tests as writable files. Hidden tests mount read-only at `/hidden` only inside the evaluator container.
9. LLM prompts get excerpts capped at 80k characters total, selected by `analysis/select.py`.

## Verilog Lab Addendum

10. Lab runs use only commands assembled from the authored course manifest; learner input is never treated as a shell command.
11. A run receives a temporary copy of the learner workspace. The original workspace is never mounted into the simulator.
12. Reference RTL is never mounted into a learner run. Hidden testbenches are mounted read-only only for `submit` runs.
13. Learner file reads and writes are limited to manifest-listed source and provided files. Traversal, symlinks, and files over 256 KiB are rejected.
14. Verilog output is capped at 128 KiB. VCD artifacts are limited to the allowlisted `wave.vcd` file and served only through the owning run.
15. Hidden results return counts only; hidden names, inputs, expected values, assertion text, and source are not returned to the learner or tutor.
16. The tutor interprets deterministic runner output but never executes Verilog and never decides whether a checkpoint passed.
