# FP64 through FP8: study report

Prepared 18 September 2026. This is a first-pass research and course-design package, not an implemented tutor or a validated GPU reproduction.

## Sources and scope

Primary source **P**: Daichi Mukunoki, *DGEMM without FP64 Arithmetic — Using FP64 Emulation and FP8 Tensor Cores with Ozaki Scheme*, [arXiv:2508.00441v3](https://arxiv.org/html/2508.00441v3), 25 September 2025, 9 pages. The 2018 conference/date/DOI fields inside this PDF are unfilled template metadata; use the arXiv identifier. All nine pages, references, equations, listing, tables and figures were inspected. No appendix is present. No separately verified supplementary archive was found.

Author-linked implementation: [OzBLAS](https://github.com/mukunoki/ozblas). The retrieved main tree identifies commit `a6f6198bc7af6cf288607ef867693f991cf48862`. README reports 1.6a, January 2025. The inspected [CUDA splitter](https://github.com/mukunoki/ozblas/blob/a6f6198bc7af6cf288607ef867693f991cf48862/src/cuda/cuozblas_split.cu) implements the sigma/add/subtract pattern and exponent storage, but does not establish availability of the exact FP8 plus integer-FP64 variant used in P. Do not call this a verified replication repository.

## Plain truth

The workload is dense matrix multiplication of binary64 inputs. The method decomposes inputs into scaled low-precision slices, computes every slice-pair product with FP8 E4M3 operands and FP32 accumulation, and combines partial products using binary64 semantics. An integer implementation can supply those binary64 operations without native FP64 arithmetic instructions. Exactness of slice products does not make the final rounded matrix product bitwise identical to every DGEMM implementation. The integer emulator omits overflow, underflow and subnormals. The reported accuracy and speed concern selected experiments, not arbitrary scientific workloads. [P, §§3–5](https://arxiv.org/html/2508.00441v3#S3)

## Read the architecture as three precision contracts

| Stage | Stored information | Arithmetic contract | What can round? |
|---|---|---|---|
| Split | binary64 residual; integer scale; E4M3 slice | binary64 RNE add/subtract and powers of two | Deliberate extraction rounding; residual retained |
| Compute | two E4M3 slices; FP32 output | Exact slice products/sums under the slicing budget | Must be proved/tested for the chosen slice range and k |
| Reconstruct | scale-adjusted partial products; binary64 output | binary64 RNE additions | Final accumulation and block accumulation |

These contracts are the course's interpretation of P §3 Eqs. 1–11, with explicit checks added for teaching. E4M3 is an operand encoding, not the accumulator. This is neither stochastic rounding nor iterative refinement; those topics are optional contrasts, not core algorithm stages.

## Mathematical reconstruction for the portable course

The following derivations and small examples are original teaching material. The equations being reconstructed are P §3, Eqs. 1–11. Use `R64` and `R32` for a single round-to-nearest, ties-to-even operation. Never allow a compiler to simplify `(r + sigma) - sigma` to `r`.

### Symbols and types

| Symbol | Shape/type | Meaning |
|---|---|---|
| A, B, C | m×k, k×n, m×n binary64 | Input matrices and result |
| r, x, y | length k, binary64 | Current residual and original dot-product inputs |
| p1, p2, p3 | integers | Significand precision INCLUDING implicit leading bit: 53, 4, 24 |
| gamma, xi, rho | integers | Accumulator budget, format budget, selected split parameter |
| c | integer per vector per slice | External power-of-two exponent |
| sigma, v | scalar/vector binary64 | Extraction offset and extracted component |
| q | length k, E4M3 bytes | Normalized low-precision component |
| sA, sB | nonnegative integers | Number of slices; zero input may use zero slices |
| D[p,q] | m×n FP32 | One slice-pair product |

P uses m_Type for significand precision and also m for matrix dimension. We use p1/p2/p3 to avoid that collision.

### Budget and extraction

For k ≥ 1:

    gamma = ceil(p1 - (p3 - log2(k))/2)
    xi = p1 - p2
    rho = max(gamma, xi)

Given a nonzero residual vector:

    c = ceil(log2(max_i abs(r_i)))
    sigma = 0.75 × 2^(rho+c)
    t_i = R64(r_i + sigma)
    v_i = R64(t_i - sigma)
    next_i = R64(r_i - v_i)
    q_i = convert_E4M3_RNE(R64(2^(-c) × v_i))

The source writes a rounded logarithm before the ceiling. Course decision: obtain the mathematical ceiling of log2 from exponent/significand bits, with a separate exact-power-of-two case. Near powers of two, rounded libm log2 may disagree. This is an explicitly documented robustness choice, to compare against source behavior rather than silently assume equivalence.

Why extraction works: near sigma its unbiased exponent is rho+c−1. Binary64 spacing is therefore 2^(rho+c−53). Adding a small residual deliberately rounds it to that grid. Subtracting sigma exposes the grid multiple. Saving the residual preserves the discarded information. Scaling by 2^(−c) gives a common grid with spacing 2^(rho−53). For the usual E4M3 budget rho=49, this is 1/16; values of magnitude at most 1 on that grid are representable in E4M3. This is a fixed-point grid inside a floating-point format. It is not arbitrary E4M3 quantization of the original input.

For a small-domain teaching implementation, require finite normal inputs or zero, magnitudes between 2^−100 and 2^100, k≤4096, and reject any nonzero subnormal intermediate. Require sigma and all rescaled terms to remain finite normal or zero. Verify exact `r = v + next` using rational arithmetic OUTSIDE the implementation. Verify that conversion to E4M3 changes no extracted value. If a nonzero residual stops decreasing, return `unsupported_domain` instead of looping or dropping it. These restrictions are course choices, not the full supported range claimed by P.

### A fully inspectable two-component example

Let x=[1.0625, −0.9375], y=[1,1], k=2. With p1=53, p2=4, p3=24, gamma=42, xi=49, rho=49.

| Step | c | Extracted v | Stored q | Remaining residual |
|---|---:|---|---|---|
| x slice 1 | 1 | [1,−1] | [0.5,−0.5] | [0.0625,0.0625] |
| x slice 2 | −4 | [0.0625,0.0625] | [1,1] | [0,0] |
| y slice 1 | 0 | [1,1] | [1,1] | [0,0] |

The first sigma is 844424930131968. Both x components land at ties on a grid of spacing 0.125; even rounding produces 1 and −1. The slice-pair dots are 0 and 2. Reconstruction gives 2^(1+0)×0 + 2^(−4+0)×2 = 0.125, the exact dot product. Casting x directly to E4M3 gives [1,−0.9375], whose dot with y is 0.0625. Retaining the residual matters. These extraction values were independently checked with host binary64; this is an illustrative arithmetic check, not a full method reproduction.

### A conservative proof of exact inner sums

On the rho=49 grid, write q_i=a_i/16 with integer |a_i|≤16. Products are a_i b_i/256. A sum of k products has numerator magnitude at most 256k. For k≤65536, every partial integer sum has magnitude at most 2^24 and is exactly representable by FP32 after rescaling. Thus in this restricted grid regime FP32 accumulation is exact. This proof depends on the common grid and magnitude bound; merely saying that each E4M3 product fits in FP32 is insufficient. At larger k the slice budget must tighten. Check real hardware for reduced precision and flush behavior; a CPU semantic model cannot certify a Tensor Core kernel.

### Matrix assembly and reconstruction contract

Slice each A row along k, and each B column along k. Their exponents depend on row/column and slice index: cA[i,p], cB[j,q]. With zero padding of missing slices:

    C_ij (exact real identity) = Σ_p Σ_q 2^(cA[i,p]+cB[j,q]) D[p,q]_ij
    D[p,q]_ij = Σ_l Q_A[p]_il × Q_B[q]_lj

This follows by substituting each expansion and distributing the product. There are sA×sB pair products, not sA+sB. Pair products cannot be omitted merely because a slice looks small: cancellation can make them decisive.

Portable pseudocode (algorithm specification, not a drop-in reference program):

    validate shapes and supported domain
    split each A row and each B column until residual is exactly zero
    pad missing row/column slices with zeros
    for every pair of slice indices:
        compute matrix product using explicit FP32-rounded accumulation
        verify common-grid/range invariants using external oracle tests
        attach each output's row exponent plus column exponent
    for each output entry:
        form scaled partials with exact power-of-two scaling where in range
        order by increasing absolute value, with (p,q) as stable tie breaker
        fold using one R64 addition per partial, starting at +0
    return result and trace of slice counts, exponent ranges and partial count

Increasing-magnitude order is a reproducible COURSE convention. P §4 says ordering was optimized but does not fully specify the schedule here. Exact numerical replication requires obtaining that schedule. It is not guaranteed to minimize error on all inputs.

### Error and tolerance, derived for this implementation

Let t_l be the exactly rescaled slice-pair dot results, L their count, u=2^−53, and g_j=ju/(1−ju). For sequential RNE summation without overflow/underflow, `|computed − Σt_l| ≤ g_(L−1) Σ|t_l|`. If scaling rounds, its error must be added; the initial domain rejects that case. Against a rounded exact binary64 oracle, add the oracle rounding error (at most half its local rounding interval). Using the exact rational target avoids that extra term. For L=0 return +0; for L=1 no summation rounding occurs when scaling is exact. Apply the g formula only for L≥2. This is an absolute forward-error bound. Divide by |exact result| only for nonzero targets. Near cancellation, report absolute error and the condition indicator `Σ|x_i y_i|/|x^T y|`; a fixed relative threshold is inappropriate.

For block outputs B_b, bound each block's error first, then add `g_(number_of_blocks−1) Σ|computed B_b|` for their accumulation. Small block size can reduce GEMM work but adds reconstruction and memory costs. No promise of bitwise agreement with a differently ordered BLAS reduction follows.

### Integer binary64 emulation track

Decode finite normal values as sign, 53-bit integer significand and exponent. Addition aligns integer significands with sticky bits; signed addition/subtraction and renormalization precede one RNE rounding. Multiplication computes the exact up-to-106-bit significand product, adds exponents, normalizes, then rounds. If retained low bit is l, guard is g, round is r and sticky is s, increment iff `g AND (r OR s OR l)`. A carry from rounding may require another exponent increment. max/compare compare signs, exponents and significands with negative ordering reversed. abs clears the sign bit. Power-of-two scaling changes the exponent subject to domain checks. Conversion to E4M3 needs its own rounding, not a silent intermediate FP32 cast.

Listing 1 of P supplies mantissa multiplication only, not an entire IEEE emulator. The course will begin with multiplication and use a separately reviewed provided addition primitive for capstone integration; implementing full addition is an extension. Python big integers teach semantics but do not demonstrate the performance of fixed 32/64-bit limbs. C migration must introduce limb carry tests and inspect generated instructions.

## Evidence and claim ledger

Labels: AUTHOR = reported by source; DERIVED = course reasoning; CHECKED = limited local arithmetic check; OPEN = not verified. No GPU benchmark was reproduced.

| Claim | Exact location | Type | Reproduction status | Notes |
|---|---|---|---|---|
| Slicing, all cross products, reconstruction | P §3 Eqs.1–11, p.3 | AUTHOR | Not fully reproduced | Core scientific method |
| E4M3 and FP32 accumulation | P §4.1, p.4 | AUTHOR | Not hardware-tested | Distinguish operand and accumulator |
| Current implementation uses dimensions divisible by 16 | P §4.1, p.4 | AUTHOR | Not reproduced | Padding is a course extension |
| Integer emulation omits underflow/overflow/subnormals | P §4.2, p.5 | AUTHOR | Not reproduced | Not full IEEE coverage |
| RTX5060Ti, CUDA12.9, best of three; allocation excluded | P §5.1, p.5 | AUTHOR | Not reproduced | Different benchmark policy in course |
| 121 FP8 pair GEMMs at k=8192 versus 81 FP16 | P Table3, p.4 | AUTHOR | Analytical count only | Not universal for arbitrary exponent spread |
| FP8/FP16 speedup ≈1.26 at n=16384 | P §5.4, p.6 | AUTHOR | Not reproduced | Do not imply this is speedup over native DGEMM |
| Figure3 compares to 128-bit MPFR rounded to binary64 | P §5.3, pp.6–7 | AUTHOR | Not reproduced | m=n=128 in figure; distinguish square performance tests |
| 4096 is best tested overall block in Figure5 | P §5.4/Fig.5, pp.7–8 | AUTHOR | Not reproduced | 1024 discussion earlier is GEMM-only tradeoff |
| x example produces exact 0.125 | This report, worked example | CHECKED | First split independently checked | Educational input, not author data |
| Common-grid numerator proves exact sums | This report, proof | DERIVED | Algebraic bound | Restricted domain |
| Figure3 error levels require metadata investigation | Fig.3 vs §5.1 | OPEN | Visual inspection | Do not reverse-engineer unreported numeric samples |

## Related work and why it belongs

| Source | Contribution | Relationship | Course concepts | Confidence / inspection |
|---|---|---|---|---|
| [Goldberg, 1991](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html) | Representation, rounding, cancellation | Foundations | ULP, RNE, nonassociativity | High; primary article |
| [Micikevicius et al., FP8 formats, 2022](https://arxiv.org/abs/2209.05433) | E4M3 and E5M2 encodings | Defines format used here | Range vs precision; special encodings | High; format paper/abstract and CUDA docs |
| [CUDA FP8 API](https://docs.nvidia.com/cuda/cuda-math-api/cuda_math_api/group__CUDA__MATH__FP8__MISC.html) | Conversion and saturation semantics | Implementation contract | SATFINITE is separate from encoding | High; official documentation |
| Ozaki et al., 2012, Numerical Algorithms 59:95–118; P ref.28 | Error-free matrix transformations | Foundational Ozaki scheme | Common-grid exactness | Bibliography verified in P; original full text not retrieved |
| [Mukunoki et al., 2020](https://doi.org/10.1007/978-3-030-50743-5_12) | Tensor-core DGEMM | Direct mixed-precision predecessor | Split/compute/sum architecture | Bibliography and linked code; not full-text audited |
| [Ootomo, Ozaki, Yokota](https://arxiv.org/abs/2306.11975) | DGEMM with integer units | Alternative low-precision substrate | Fixed-point slices | High-level source inspected; not replication |
| [Abdelfattah et al., v3 2026](https://arxiv.org/abs/2506.11277v3) | Error analysis of integer-based multiplication | Helps design adversarial scaling tests | Accuracy/cost and ill-scaled rows/columns | Abstract-level review; do not transfer its theorem verbatim to FP8 |
| [Ozaki Scheme II, v4](https://arxiv.org/abs/2504.08009v4) | Chinese remainder reconstruction | Different algorithmic branch | Residues versus slice cross products | Abstract inspected; version updated September 2026 |
| [Uchino et al., 2026](https://arxiv.org/html/2603.10634v2) | FP8 adaptation of Ozaki-II | Relevant follow-up; optional next course | Quantization and Karatsuba extension | Intro/structure inspected; no benchmark independently verified |
| [MPFR manual](https://www.mpfr.org/mpfr-current/mpfr.html) | Explicit precision and rounding | Numerical oracle | 128/256-bit convergence checks | Official documentation |
| [Ozaki 2.5, September 2026](https://arxiv.org/abs/2609.09095) | Deconstruction performance modeling | Later engineering outlook | Model projections versus measurements | Abstract only; explicitly projected results |

Compensated/multiword arithmetic is a useful contrast to integer emulation, but not a substitute for the taught method. Iterative refinement solves a different problem and is omitted from required checkpoints. Stochastic rounding changes the extraction contract and is not used. A complete/Kulisch accumulator can be discussed as an exact oracle architecture; it is not claimed to be this paper's reconstruction implementation.

## Risks and recommendation

The largest risks are exact source-version availability, reduction-order details, exceptional-value behavior, and unclear accuracy-figure metadata. Fig.3's plotted baseline errors appear unexpectedly large for positive (1,10) inputs under ordinary full-precision binary64 arithmetic; this is a question, not a finding of a bug. Request matrix seeds/distributions, cuBLAS math mode, and the metric implementation before matching that figure numerically.

Ready for a **Python-first, 14-checkpoint semantic course**, with GPU timing and exact figure replication explicitly pending. The course should reproduce an exact dot product, then a small controlled accuracy experiment with disclosed deviations. The next concrete action after curriculum review is to inspect the actual tutor repository and implement checkpoint 1 plus the deterministic runner boundary. No existing cache-lab code or learner data was accessed or modified.
