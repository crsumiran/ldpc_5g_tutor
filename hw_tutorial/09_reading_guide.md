# 09 · Reading Guide

> **Goal:** Know which paper to read, in what order, and how to translate each one's notation into this tutorial's.
>
> * **Papers next to this repo:** Song/Cui/Wang 2022 and Huang/Walrand 2012 (§1)
> * **Downloaded papers:** `../../references/` (§2)

## 1. The Two Papers Next to This Repo

### Song, Cui, Wang: "A Universal Efficient Circular-Shift Network for Reconfigurable QC-LDPC Decoders", IEEE TVLSI 30(10), 2022

This is the paper the IBN design in chapter 06 comes from. Read it **after chapter 06**, section by section, using the table below to find the matching tutorial material:

| Paper section | What it is | Tutorial chapter |
|---|---|---|
| I. Introduction | Survey: Benes [5], Oh & Parhi [6], QSN [7], EBS [8], Harb & Chavet [9], VBN [10], [11], Lam [12] | 03, 05, 06 |
| II-A Banyan network, Fig. 1 | BN and VBN structure | 03 §5, 06 §6 |
| II-B Barrel shifter, Fig. 2 | 7×7 barrel; "SV is the natural control signal" | 04 |
| II-C Bypass network | two shifters + merge | 05 |
| III-A Improved BN, Fig. 3, Alg. 1 vs Alg. 2 | 3×3 stage first → no modulo | 06 §6 |
| Table I | controller complexity (modulo ops, LUTs, comparators) | 06 §4, §6 |
| III-B Hybrid architecture, Fig. 4, 5 | EU = barrel shifter leaves, IBN above, bypass/merge | 06 §7 |
| III-C, Fig. 6, Table II | 5G: two 3·2^7 IBNs + merge; 8 parallelism options | 06 §7, `rtl/rot_5g.v` |
| IV, Tables III–IV | 90 nm synthesis results, area breakdown | 06 §7 |

**Notation map.** The paper's symbols translate to this tutorial's as follows:

| Paper | This tutorial |
|---|---|
| IN (input size) | Z |
| N (network size) | N (= 384 for 5G) |
| SV (shift value) | s, shift, P |
| SV_k | b_d (shift seen by the stage-d sub-networks) |
| C_k, C_k[j] | swap_d, swap_d[k] |
| Th_k (threshold) | the thermometer boundary b_d (`k < b_d`) |
| bar state | swap = 0 |
| EU (elementary unit) | a small barrel rotator at the leaves |
| Merge Network | the per-lane `i < Z − s` mux (ch. 05) |
| p | smallest Z the network must support |

**Watch the shift direction.** Their figures draw shifts in the opposite direction in places. Use the Z = 4, P = 1 check from chapter 02 §3 before mapping a formula.

**One citation error to know about:** reference [7] (QSN) gives the volume and pages of reference [6]. The QSN paper is X. Chen, S. Lin, V. Akella, *IEEE TCAS-II*, vol. 57, no. 10, pp. 782–786, Oct. 2010.

### Huang, Walrand: "A Benes Packet Network", arXiv 1208.0561, 2012

**This is not an LDPC paper.** It proposes building a data-center network out of a Benes topology, with queues in every switch and a backpressure scheduling algorithm. Only a small part of it is relevant here:

* **Read:** Section III-A and Fig. 2, which show how a 2^n × 2^n Benes network is built recursively from an input switch column, two half-size Benes networks and an output switch column. That is a good picture of chapter 03 §6.
* **Skip:** Sections II and IV–VII (utility maximization, Lyapunov drift, queue stability). These are packet-scheduling theory and have no counterpart in a decoder's combinational rotator.

## 2. Downloaded Open-Access Papers (`../../references/`)

These are listed in the suggested reading order:

| File | What it is | Why read it |
|---|---|---|
| `Studer_2008_ASILOMAR_LDPC.pdf` | Studer et al., "Configurable High-Throughput Decoder Architecture for QC-LDPC Codes", Asilomar 2008 (ETH Zurich) | A clear, short description of a configurable block-serial QC decoder (802.11n). The closest match to chapter 07 |
| `arXiv_2102.13228_Multimode_5G_NR_LDPC_decoder_2021.pdf` | Pourjabar & Choi, "A High-Throughput Multi-Mode LDPC Decoder for 5G NR", 2021 | A 5G decoder that doubles or quadruples parallelism at small Z: multi-frame in practice; shift network discussion |
| `arXiv_2310.15801_Generalized_adjusted_minsum_5G_2023.pdf` | Ren, Harb, Shen, Balatsoukas-Stimming, Burg, "A Generalized Adjusted Min-Sum Decoder for 5G LDPC Codes", 2023/24 | A complete, fully reconfigurable 5G ASIC (28 nm, 24 Gb/s): memory compression, CNU approximations. Harb is a co-author of two shifter papers cited by Song |
| `arXiv_2505.19027_Layered_QC_LDPC_schedule_2025.pdf` | Chang et al., "High Throughput QC-LDPC Decoder With Optimized Schedule Policy in Layered Decoding", 2025 | Pipeline hazards and layer ordering (chapter 07 §5) |
| `arXiv_1505.04339_QC_LDPC_decoder_USRP_2015.pdf` | Mhaske et al., "A 2.48 Gb/s QC-LDPC Decoder Implementation on the NI USRP-2953R", 2015 | FPGA layered decoder; massively parallel style |
| `Polito_thesis_5G_LDPC_DSE.pdf` | Barrera, "A Design Space Exploration Tool for LDPC Decoder Architectures in 5G NR", MSc thesis, Politecnico di Torino, 2023 (77 pp.) | Survey-style background chapters and an area/frequency/throughput model for BG1 decoders. Good when choosing your architecture |
| `ETSI_TS_138212_v17.9.0.pdf` | 3GPP TS 38.212 v17.9.0 | §5.3.2: base graphs (Tables 5.3.2-2/3), lifting sets (5.3.2-1), P = V mod Z |

## 3. Open Access, but Needs a Manual Download (Sites Block Scripts)

These papers are free to read, but the hosting sites block scripted downloads, so fetch them by hand:

| Paper | Link |
|---|---|
| Boutillon & Harb, "Extended Barrel-Shifter for Versatile QC-LDPC Decoders", IEEE WCL 2020 (EBS, ref [8]) | <https://hal.science/hal-02441491> |
| Harb & Chavet, "Fully Parallel Circular-Shift Rotation Network for Communication Standards", IEEE TCAS-II 2020 (ref [9]) | <https://hal.science/hal-02804289> (check for an attached PDF) |
| "Low-Complexity Multi-Size Circular-Shift Network for 5G New Radio LDPC Decoders", *Sensors* 22(5):1792, 2022 | <https://www.mdpi.com/1424-8220/22/5/1792> |
| Nguyen, Tan, Lee, pipelined layered QC-LDPC decoder for 5G NR, *Electronics* 10(4):516, 2021 | <https://www.mdpi.com/2079-9292/10/4/516> |

## 4. Paywalled Classics (IEEE Xplore)

Your organization's IEEE access (the Song paper's download stamp suggests you have it) should cover these:

| Paper | Why |
|---|---|
| X. Chen, S. Lin, V. Akella, "QSN — a simple circular-shift network for reconfigurable QC-LDPC decoders", TCAS-II 57(10), 2010 | Original two-shifter + merge (chapter 05) |
| D. Oh, K. K. Parhi, "Low-complexity switch network for reconfigurable LDPC decoders", TVLSI 18(1), 2010 | Benes variant with 3×3/5×5 switches |
| X. Peng et al., "High parallel variation Banyan network based permutation network for reconfigurable LDPC decoder", ASAP 2010 | The VBN (chapter 06 §6) |
| Z. Zhong et al., "A flexible and high parallel permutation network for 5G LDPC decoders", TCAS-II 67(12), 2020 | The 5G VBN baseline Song et al. compare against |
| H.-M. Lam et al., "A high-efficiency segmented reconfigurable cyclic shifter for 5G QC-LDPC decoder", TCAS-I 69(1), 2022 | Alternative 5G shifter |
| D. Hocevar, "A reduced complexity decoder architecture via layered decoding of LDPC codes", IEEE SiPS 2004 | The layered schedule (chapter 01 §5) |
| M. Mansour, N. Shanbhag, "High-throughput LDPC decoders", TVLSI 11(6), 2003 | Turbo-decoding message passing; memory-efficient architecture |
| V. E. Beneš, "Optimal rearrangeable multistage connecting networks", Bell Syst. Tech. J. 43(4), 1964 | The original Benes network |

## 5. Suggested Path

Putting it all together, a reading order that alternates between this tutorial and the papers:

1. **Chapters 00–06 here:** running the models as you go.
2. **Song et al.:** with the notation map above.
3. **Studer 2008, then chapter 07.**
4. **Pourjabar 2021:** multi-frame in a real 5G design.
5. **Ren 2023:** what a complete modern 5G decoder looks like.
6. **EBS and QSN:** alternative shifter designs.
