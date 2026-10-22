# Glossary

| Term | Meaning | Chapter |
|---|---|---|
| **APP / L value** | running "a-posteriori" LLR per bit, updated every layer | 01 |
| **bar / cross (swap)** | the two states of a 2×2 switch: straight through, or exchanged | 03 |
| **Banyan network** | log2 N stages of 2×2 switches, built recursively; unique path; blocking; can do all rotations | 03, 06 |
| **barrel shifter / rotator** | log-depth shifter where stage k shifts by 2^k; shift bits drive the selects directly | 04 |
| **base graph (BG1, BG2)** | small matrix of shift values that describes the large H; 46×68 and 42×52 in 5G | 01 |
| **Benes network** | Banyan + mirrored Banyan, 2·log2 N − 1 stages; rearrangeably non-blocking (any permutation) | 03 |
| **block-serial** | decoder processes one base-matrix block (Z edges) per clock | 07 |
| **blocking** | some permutations are impossible because two routes need one internal link | 03 |
| **bypass network** | two rotators/shifters + merge, to rotate a vector shorter than the network | 05, 06 |
| **circulant I(P)** | Z×Z identity with columns rotated right by P | 01, 02 |
| **CNU** | check-node unit: computes min1, min2, idx, sign for one check | 01, 07 |
| **code rate** | information bits / transmitted bits | 00 |
| **control generation** | logic turning (shift, Z, frame mode) into switch selects | 03, 06 |
| **crossbar** | N output muxes of N:1; any permutation; N² cost | 03 |
| **d_c (row weight)** | number of blocks in a base-matrix row = edges per check | 01, 07 |
| **delta-shift trick** | store words in their last rotation; rotate by the difference on the next read; saves a rotator | 07 |
| **EBS** | Extended Barrel Shifter (Boutillon & Harb 2020) | 05, 09 |
| **EU** | elementary unit: smallest sub-network in the hybrid network, a barrel shifter | 06 |
| **flooding schedule** | update all checks, then all variables; slower convergence than layered | 01 |
| **IBN** | Improved Banyan Network (Song et al. 2022): 3×3 stage first, then power-of-two Banyans | 06 |
| **iLS** | lifting-set index 0–7 in TS 38.212 Table 5.3.2-1; selects which V column to use | 01 |
| **layer** | one base-matrix row = Z checks processed in parallel | 01 |
| **layered decoding** | process layers in sequence, using updated L values immediately | 01, 07 |
| **lifting size Z** | circulant size; 51 legal values 2…384 in 5G | 01 |
| **LLR** | log-likelihood ratio: sign = bit guess (+ → 0), magnitude = confidence | 01 |
| **merge network** | per-lane mux choosing between two shifter outputs with a thermometer mask | 05 |
| **min1 / min2 / idx** | smallest and second-smallest input magnitudes of a check, and the edge of the smallest | 01 |
| **Min-Sum (offset / normalized)** | hardware-friendly check-node rule; the offset/scaling corrects over-confidence | 01 |
| **multi-frame** | splitting one network into independent smaller rotators, each with its own shift | 06 |
| **P, V** | P = V mod Z is the shift used; V comes from the standard's table | 01 |
| **punctured bits** | bits never transmitted; their LLR starts at 0 (first 2Z bits in 5G) | 01 |
| **QC (quasi-cyclic)** | H built from circulant blocks | 01 |
| **QSN** | QC-LDPC shift network (Chen, Lin, Akella 2010): two shifters + merge | 05 |
| **R message** | last check-to-variable message, kept per edge (often compressed) | 01, 07 |
| **rearrangeably non-blocking** | every permutation is reachable if all switches are set together | 03 |
| **rotl(x, s)** | this tutorial's convention: out[i] = in[(i + s) mod Z] | 02 |
| **syndrome** | H·x mod 2; all zeros means every check holds | 01 |
| **Tanner graph** | bipartite graph of checks and variables; edges = 1s in H | 01 |
| **thermometer code** | k-bit vector whose low b bits are 1, i.e. (k < b) for each k | 05, 06 |
| **unique-path property** | exactly one route from each input to each output (Banyan) | 03 |
| **VBN** | Variation Banyan Network (Peng et al. 2010): 3×3 stage last; needs modulo control | 06 |
