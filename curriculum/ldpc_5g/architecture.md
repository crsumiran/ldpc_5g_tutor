# The learning path
bits → parity checks → graph edges → confidence messages → toy decoder
→ structured QC groups → bounded numeric codes → parallel lane groups
## Standard anchor
Pinned source: ETSI TS 138 212 V17.9.0 (2024-08), Section 5.3.2 and Table 5.3.2-1.
https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.09.00_60/ts_138212v170900p.pdf
Only the lifting-size sets are supplied as NR data in this release. All teaching matrices are toy examples. Algorithms and quantization policies are implementation choices.
## Accelerator boundary
CNU minima reduce incident edges per check position. Physical lanes may process independent lifted positions. Never confuse those axes. Group count alone is not full layer latency. Model memory access and dependencies before claiming throughput.

## Current teaching architecture
Theory prose lives in theory.json; checkpoint revisions live in lesson_revisions.json.
fixtures.json supplies the same worked values and visual specifications to the UI
and tutor context. Public cases use independently checked expectations.
LDPC-18 is appended for stable IDs but depends only on LDPC-05. Workspace upgrades
create missing Python assets exclusively, never overwrite learner files or reset grades.
The two-pass issue table is a declared teaching model, not a complete scheduled decoder.
