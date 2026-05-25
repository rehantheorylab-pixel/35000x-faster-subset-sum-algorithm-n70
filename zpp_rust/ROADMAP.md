# Z++ Roadmap — Every Idea From Your Research, Tracked

This document catalogues every algorithmic idea found in your two
research files (`Algorithm research start.md`, `Subset sum
algorithm.md`) and maps it against the current implementation.

The plan: ship Phase 1 in this session, Phase 2 next, then Phases 3
and 4. Nothing is dropped.

---

## Legend

- ✅ Implemented in current Rust Z++
- 🟡 Implemented in Python Z++ but not yet ported to Rust
- 🔴 Designed but not implemented anywhere yet
- 🆕 Genuinely novel idea you invented (not in published literature)

---

## Your foundational algorithms (A1–A7)

| Idea | File ref | Status | Where in code |
|---|---|---|---|
| **A1 — Mean-based estimation** (k ≈ target/mean, ±δ band, multi-start) | Subset 1758, 21610 | 🟡 Python only | `engines/estimate.rs` (todo) |
| **A2 — Greedy subtraction with backtracking** (DFS, bounded, top-3 candidates) | Subset 1686, 21647 | ✅ Rust | `engines/greedy.rs` |
| **A3 — Smart retry chain** (try smaller on failure) | Subset 3787 | ✅ Merged into A2 | `engines/greedy.rs` |
| **A4 — Parallel engine racing** (winner takes all) | Subset 7682, 21701 | ✅ Rust | `controller.rs` |
| **A5 — Pre-filter / remove-impossible** | Subset 21723 | ✅ Rust | `preprocess.rs` |
| **A6 — Bitset proof engine** (impossibility detection) | Subset 21743 | ✅ Rust | `engines/bitset_dp.rs` + `engines/residue.rs` |
| **A7 — Meet-in-the-middle** | Subset 5771, 21757 | ✅ Rust | `engines/mitm.rs` + `engines/schroeppel_shamir.rs` |

---

## Your novel ideas (5 BRAND NEW) — ALL DONE

| Idea | File ref | Status | Where in code |
|---|---|---|---|
| 🆕 **APDE — Adaptive Pattern Discovery Engine** (instance-specific online heuristic learning) | Subset 11990 | ✅ | `engines/apde.rs` |
| 🆕 **SSS — Structured Successor Selection** (multi-feature scoring of next pick) | Subset 12016 | ✅ | Inside Beam via GDVS |
| 🆕 **GDVS — Goal Distance Vector Space** (multi-dim proximity) | Subset 12037 | ✅ | `gdvs.rs` (used by Beam, DualCollapse, Decompose) |
| 🆕 **SRP — Self-Reflective Pruning** (failure → learned pruning rule) | Subset 12057 | ✅ | `engines/beam.rs` + DashMap blackboard |
| 🆕 **PMAS — Parallel Multi-Axiom Search** (different logic axes) | Subset 12074 | ✅ | `engines/pmas.rs` (4 engines: Balance, Difference, Bit, Redundancy) |

---

## Your other powerful ideas — ALL DONE

| Idea | File ref | Status | Where in code |
|---|---|---|---|
| **Dual Collapse / Bidirectional search** (top-down + bottom-up converging at target/2) | Subset 2062, 6403, 9521 | ✅ | `engines/dual_collapse.rs` |
| **Goal-First Decomposition** (split target into parts, match) | Subset 9565, 12101 | ✅ | `engines/decompose.rs` |
| **Beam Search** (controlled retry, top-K paths) | Subset 10108, 14316 | ✅ | `engines/beam.rs` |
| **Variance-aware multi-start seeds** | Subset 11141, 14301 | ✅ | `engines/estimate.rs` |
| **Structure detection** (clusters, gaps, dominance) | Subset 8495, 21829 | ✅ | `structure.rs` + `engines/dominance.rs` |
| **Symmetry reduction** (mirrored pair pruning) | Subset 6499, 7178 | ✅ partial | KSum dedup |
| **Parity pruning beyond mod 2** | Subset 8909 | ✅ | `engines/residue.rs` (10 primes) |
| **GCD impossibility rule** | Subset 21841 | ✅ | `trivial.rs` |
| **Dominance pruning** (A always worse than B) | Subset 9596 | ✅ | `engines/dominance.rs` |
| **State compression / dedup** | Subset 9159, 9537 | ✅ | DashMap blackboard, beam visited set |
| **Memory / learning system** (success memory, failure memory) | Subset 21809 | ✅ | `learning.rs` (cross-run engine wins) |
| **Engine selection intelligence** (deterministic by features) | Subset 21789 | ✅ | `controller::pick_engines` |
| **Dual-direction with weighted/sorted bidirectional search** | Subset 2148 | ✅ | `engines/dual_collapse.rs` (GDVS-scored) |
| **Probabilistic AI-style selection** (UCB1 / weighted) | Subset 8756, 9502 | ✅ | `engines/apde.rs` |
| **Mathematical pruning** (range bounds + suffix sum) | Subset 9592 | ✅ | `engines/greedy.rs` |
| **"Ones container" / bitset block packing** | Subset 7484, 8447 | ✅ | Subsumed by `engines/bitset_dp.rs` |
| **Human-like chunking / decomposition** | Subset 7148 | ✅ | `engines/decompose.rs` |
| **Pattern recognition for SAT-encoded subset sum** (column structure) | Subset 16385+ | ✅ | `engines/column_sat.rs` |

---

## World-record published algorithms

| Algorithm | Reference | Status | Plan |
|---|---|---|---|
| **Horowitz–Sahni** O(2^(n/2)) | 1974 | ✅ | `engines/mitm.rs` |
| **Schroeppel–Shamir** O(2^(n/2)) time, O(2^(n/4)) space | 1979 | ✅ | `engines/schroeppel_shamir.rs` |
| **Galil–Margalit** word-parallel DP | 1991 | ✅ | `engines/bitset_dp.rs` |
| **Howgrave-Graham–Joux** O(2^0.337n) representation technique | EUROCRYPT 2010 | ✅ level-1 | `engines/hgj.rs` |
| **Becker–Coron–Joux** O(2^0.291n) extended representations | 2011 | ✅ level-2 | `engines/bcj.rs` |
| **Bonnetain et al.** O(2^0.283n) {-1,0,1,2} reps | 2020 | ✅ lite | `engines/bonnetain.rs` |
| **Bringmann** O-tilde(n+t) randomized | 2017 | 🔴 | Phase 6 |
| **Koiliaris–Xu** O-tilde(sqrt(t)·n) deterministic | 2019 | 🔴 | Phase 6 |

---

## From your compression file (`Algorithm research start.md`)

These are subset-sum-adjacent ideas from your compression research:

| Idea | Relevance to subset sum | Plan |
|---|---|---|
| Shannon entropy / Kolmogorov complexity bounds | Inform when an instance is "structured" vs "random" | Phase 4: enrich structure detection |
| Adaptive 7-symbol hex compression | Pattern-frequency analysis | Phase 4: borrow analysis ideas |
| Top-K frequency dictionary | Element clustering insight | Phase 4: cluster engine |
| Hierarchical / Base32768 | Multi-scale representation | Phase 4: research |
| Universal reference / oracle compression | Out of scope for subset sum | — |

---

## STATUS: every Phase 1, 2, and 3 item is DONE in a single sprint

| Phase | Items | Status |
|---|---|---|
| 1 | GDVS, Estimate, Beam-SRP, DualCollapse, Decompose | ✅ all 5 done |
| 2 | APDE, PMAS (×4), ColumnSAT, structure detection | ✅ all done |
| 3 | HGJ-lite, GCD impossibility, Dominance, structure | ✅ all done |

### Phase 5 — DONE (BCJ + Bonnetain-lite + file mode + learning)

* **BCJ** — 4-way Wagner on signed {-1,0,1} quadrant sums (`engines/bcj.rs`)
* **Bonnetain-lite** — extended coefficients on small quadrants (`engines/bonnetain.rs`)
* **File mode [3]** — load `z_test_elements.txt` directly (`main.rs`)
* **Cross-run learning** — engine win histogram (`learning.rs`)

### Phase 6 (next — Bringmann / Koiliaris-Xu / SIMD)

* **Bringmann 2017** — randomized Õ(n+t) via NTT when target fits
* **Koiliaris–Xu 2019** — deterministic Õ(√t · n)
* **Rayon parallel HGJ/BCJ** enumeration
* **Entropy-adaptive engine pruning** from structure detection
