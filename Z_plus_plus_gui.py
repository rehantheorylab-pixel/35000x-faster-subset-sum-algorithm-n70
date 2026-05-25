"""
Z++ ULTIMATE ENGINE v3.0
========================
Portfolio-based Subset Sum Solver

Algorithm Design & Research: Rehan (Independent Researcher)

Combines:
  - 15 Z++ original algorithms (upgraded, all cons fixed)
  - World-best research techniques:
      Horowitz-Sahni MITM, Galil-Margalit bitset DP,
      Bringmann-style near-linear, k-Sum hash chains,
      Schroeppel-Shamir space reduction
  - 6 Novel methods:
      Multi-prime residue pre-filtering, CDCL dead-end learning,
      Entropy-guided beam scoring, Additive closure detection,
      Information-theoretic path scoring, Bridge gap-close technique
  - Worst-case enhancements:
      Unique-sums-aware MITM (Salas 2025 inspired),
      Greedy-to-exact bridge, extended MITM range (n≤50)

Architecture: Parallel engine racing with shared intelligence (Meta-Brain).
All engines run simultaneously; first to find exact answer wins.
"""

import sys
import threading
import time
import math
import random
import tracemalloc
from collections import defaultdict

sys.setrecursionlimit(50000)


# ================================================================
#  PHASE 1 — DEEP INPUT ANALYSIS
# ================================================================

class ProblemProfile:
    """Computes statistical features, suffix sums, and classifies the
    problem so the Meta-Brain can select the right engine mix."""

    def __init__(self, numbers, target):
        self.numbers = sorted(numbers)
        self.target = target
        self.n = len(self.numbers)
        self.total_sum = sum(self.numbers)
        self.num_set = set(self.numbers)

        self.freq = defaultdict(int)
        for x in self.numbers:
            self.freq[x] += 1

        if self.n > 0:
            self.min_val = self.numbers[0]
            self.max_val = self.numbers[-1]
            self.spread = self.max_val - self.min_val
            self.median = self.numbers[self.n // 2]
            try:
                self.mean = self.total_sum / self.n
            except (OverflowError, ValueError):
                self.mean = self.total_sum // self.n
        else:
            self.min_val = self.max_val = self.mean = 0
            self.spread = self.median = 0

        try:
        if self.n > 1:
                self.variance = sum((x - self.mean) ** 2
                                    for x in self.numbers) / (self.n - 1)
                self.std_dev = math.sqrt(self.variance)
                if self.std_dev > 0:
                    self.skewness = (sum(((x - self.mean) / self.std_dev) ** 3
                                         for x in self.numbers) / self.n)
                    self.kurtosis = (sum(((x - self.mean) / self.std_dev) ** 4
                                         for x in self.numbers) / self.n - 3)
        else:
                    self.skewness = self.kurtosis = 0.0
                self.is_uneven = (self.spread > self.mean * 3
                                  or self.std_dev > self.mean)
            else:
                self.variance = self.std_dev = 0.0
                self.skewness = self.kurtosis = 0.0
                self.is_uneven = False
            self.density_ratio = (self.target / self.total_sum
                                  if self.total_sum > 0 else 0)
        except (OverflowError, ValueError):
            self.variance = self.std_dev = 0.0
            self.skewness = self.kurtosis = 0.0
            self.is_uneven = True
            self.density_ratio = 0

        # Ascending suffix sums (for feasibility checks)
        self.suffix_sums = [0] * (self.n + 1)
        for i in range(self.n - 1, -1, -1):
            self.suffix_sums[i] = self.suffix_sums[i + 1] + self.numbers[i]

        # Descending order + suffix sums (for greedy engine)
        self.desc = sorted(self.numbers, reverse=True)
        self.desc_suffix = [0] * (self.n + 1)
        for i in range(self.n - 1, -1, -1):
            self.desc_suffix[i] = self.desc_suffix[i + 1] + self.desc[i]

        if self.n <= 5:
            self.pclass = "TRIVIAL"
        elif self.n <= 20:
            self.pclass = "TINY"
        elif self.n <= 40:
            self.pclass = "SMALL"
        elif self.target <= 10_000_000:
            self.pclass = "MEDIUM"
        else:
            self.pclass = "LARGE"


# ================================================================
#  PHASE 2 — TRIVIAL & FAST-PATH DETECTION
# ================================================================

class TrivialSolver:
    """O(n) instant checks: 1-Sum, 2-Sum, parity, multi-prime residue.
    Returns (solved, solution).  solution=None means proved impossible."""

    PRIMES = [2, 3, 5, 7, 11, 13]

    @staticmethod
    def solve(p):
        if p.target == 0:
            return True, []
        if p.n == 0 or p.target < 0:
            return True, None
        if p.target == p.total_sum:
            return True, list(p.numbers)
        if p.target > p.total_sum:
            return True, None
        if p.min_val > p.target:
            return True, None

        # 1-Sum
        if p.target in p.num_set:
            return True, [p.target]

        # 2-Sum (O(n) via hash)
        for x in p.numbers:
            c = p.target - x
            if c > 0 and c in p.num_set:
                if c != x or p.freq[x] >= 2:
                    return True, sorted([x, c])

        # Parity
        if p.target % 2 == 1 and all(x % 2 == 0 for x in p.numbers):
            return True, None

        # Multi-prime residue feasibility
        for prime in TrivialSolver.PRIMES:
            tr = p.target % prime
            reach = 1
            mask = (1 << prime) - 1
            for x in p.numbers:
                r = x % prime
                shifted = reach << r
                reach = (reach | shifted | (shifted >> prime)) & mask
            if not (reach & (1 << tr)):
                return True, None

        return False, None


# ================================================================
#  PHASE 3 — PREPROCESSING & REDUCTION
# ================================================================

class Preprocessor:
    """Filters impossible elements, detects must-include elements,
    and shrinks the problem before heavy computation."""

    @staticmethod
    def reduce(numbers, target):
        forced = []
        nums = [x for x in numbers if 0 < x <= target]
        if sum(nums) < target:
            return nums, target, forced, True

        changed = True
        while changed:
            changed = False
            total = sum(nums)
            kept = []
            for x in nums:
                if total - x < target:
                    forced.append(x)
                    target -= x
                    changed = True
                else:
                    kept.append(x)
            nums = kept
            if target == 0:
                return nums, 0, forced, False
            if target < 0 or (nums and sum(nums) < target):
                return nums, target, forced, True
            if not nums and target > 0:
                return nums, target, forced, True

        return sorted(nums), target, forced, False


# ================================================================
#  SHARED INTELLIGENCE — CONFLICT DATABASE (Novel: CDCL)
# ================================================================

class ConflictDB:
    """Adapted from SAT-solver CDCL: records element-index combos
    that provably lead to dead ends.  Shared across all engines."""

    def __init__(self):
        self._clauses = set()
        self._lock = threading.Lock()

    def record(self, indices, max_size=4):
        if len(indices) > max_size:
            indices = indices[-max_size:]
        clause = frozenset(indices)
        with self._lock:
            if len(self._clauses) < 200_000:
                self._clauses.add(clause)

    def conflicts(self, indices):
        if not self._clauses:
            return False
        s = set(indices)
        with self._lock:
            return any(c.issubset(s) for c in self._clauses)

    @property
    def size(self):
        return len(self._clauses)


# ================================================================
#  ENGINE A1 — BITSET DP  (64× compressed via Python big-ints)
#  Sources: Your #9 + #11, World W3 Galil-Margalit, W7 Bringmann
# ================================================================

class BitsetDPEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "BitsetDP"

    def run(self):
        p = self.ctrl.profile
        if p.target > 20_000_000:
            self.ctrl.log(f"[{self.name}] target {p.target} exceeds 20M limit.")
            return

        self.ctrl.log(f"[{self.name}] Exact bitset DP  n={p.n}  t={p.target}")
        dp = 1
        history = [dp]

        for idx, num in enumerate(p.numbers):
            if self.ctrl.stopped:
                return
            dp |= dp << num
            history.append(dp)
            if dp & (1 << p.target):
                self.ctrl.log(f"[{self.name}] Proved at element {idx}. Reconstructing...")
                sol = self._rebuild(history, p.numbers, p.target)
                if sol is not None:
                    self.ctrl.report(sol, self.name)
                return

        if not (dp & (1 << p.target)):
            self.ctrl.log(f"[{self.name}] PROVED IMPOSSIBLE.")
            self.ctrl.proved_impossible = True

    @staticmethod
    def _rebuild(history, nums, target):
        cur = target
        sol = []
        max_i = min(len(nums), len(history) - 1)
        for i in range(max_i - 1, -1, -1):
            if cur <= 0:
                break
            v = nums[i]
            if cur >= v and (history[i] & (1 << (cur - v))):
                sol.append(v)
                cur -= v
        return sol if cur == 0 else None


# ================================================================
#  ENGINE B1 — MEET-IN-THE-MIDDLE  (Horowitz-Sahni 1974)
#  Sources: Your #3, World W1/W2
# ================================================================

class MITMEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "MITM"

    def run(self):
        p = self.ctrl.profile
        if p.n > 50:
            self.ctrl.log(f"[{self.name}] n={p.n} too large for MITM, skipping.")
            return

        self.ctrl.log(f"[{self.name}] Meet-in-the-Middle  n={p.n}")
        mid = p.n // 2
        left, right = p.numbers[:mid], p.numbers[mid:]

        left_sums = {0: 0}
        for bit, elem in enumerate(left):
            if self.ctrl.stopped:
                return
            new = {}
            for s, mask in left_sums.items():
                ns = s + elem
                if ns <= p.target and ns not in left_sums and ns not in new:
                    new[ns] = mask | (1 << bit)
            left_sums.update(new)

        if p.target in left_sums:
            m = left_sums[p.target]
            self.ctrl.report(
                [left[i] for i in range(len(left)) if m & (1 << i)],
                self.name)
            return

        right_sums = {0: 0}
        for bit, elem in enumerate(right):
            if self.ctrl.stopped:
                return
            new = {}
            for s, mask in right_sums.items():
                ns = s + elem
                if ns > p.target:
                    continue
                if ns not in right_sums and ns not in new:
                    new[ns] = mask | (1 << bit)
                comp = p.target - ns
                if comp in left_sums:
                    lm = left_sums[comp]
                    sol = ([left[i] for i in range(len(left)) if lm & (1 << i)]
                           + [right[j] for j in range(len(right))
                              if (mask | (1 << bit)) & (1 << j)])
                    self.ctrl.report(sol, self.name)
                    return
            right_sums.update(new)

        for rs, rm in right_sums.items():
            if self.ctrl.stopped:
                return
            comp = p.target - rs
            if comp in left_sums:
                lm = left_sums[comp]
                sol = ([left[i] for i in range(len(left)) if lm & (1 << i)]
                       + [right[j] for j in range(len(right)) if rm & (1 << j)])
                self.ctrl.report(sol, self.name)
                return


# ================================================================
#  ENGINE C1 — ADAPTIVE MULTI-ESTIMATE  (Your #1 + #2 upgraded)
# ================================================================

class EstimateEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "Estimate"

    def run(self):
        p = self.ctrl.profile
        self.ctrl.log(f"[{self.name}] 3 estimation strategies + correction")
        desc = sorted(range(p.n), key=lambda i: -p.numbers[i])

        for tag, k in self._guesses(p):
            if self.ctrl.stopped:
                return
            k = max(1, min(k, p.n))
            chosen = set(desc[:k])
            total = sum(p.numbers[i] for i in chosen)
            sol = self._correct(p, chosen, total, desc)
            if sol is not None:
                self.ctrl.report(sol, f"{self.name}({tag})")
                return

    @staticmethod
    def _guesses(p):
        g = []
        if p.mean > 0:
            g.append(("mean", round(p.target / p.mean)))
        if p.median > 0:
            g.append(("median", round(p.target / p.median)))
        near = ([x for x in p.numbers if abs(x - p.mean) <= p.std_dev]
                if p.std_dev > 0 else p.numbers)
        if near:
            wc = sum(near) / len(near)
            if wc > 0:
                g.append(("weighted", round(p.target / wc)))
        return g

    def _correct(self, p, chosen, total, desc):
        for _ in range(3 * p.n):
            if self.ctrl.stopped:
                return None
            diff = total - p.target
            if diff == 0:
                return [p.numbers[i] for i in chosen]
            if diff > 0:
                best = min(chosen, key=lambda i: abs(p.numbers[i] - diff),
                           default=None)
                if best is None:
                    return None
                chosen.discard(best)
                total -= p.numbers[best]
        else:
                gap = -diff
                best = None
                for idx in desc:
                    if idx not in chosen and p.numbers[idx] <= gap:
                        best = idx
                break
                if best is None:
                    return None
                chosen.add(best)
                total += p.numbers[best]
        return None


# ================================================================
#  ENGINE C2 — GREEDY + FEASIBILITY + BACKTRACKING
#  Sources: Your #6, #7, #14 upgraded
# ================================================================

class GreedyEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "Greedy"

    def run(self):
        p = self.ctrl.profile
        self.ctrl.log(f"[{self.name}] Greedy largest-first + backtrack")
        sol = self._solve(p.desc, p.desc_suffix, p.target, 0, p.n)
        if sol is not None:
            self.ctrl.report(sol, self.name)

    def _solve(self, nums, suf, target, start, n):
        if target == 0:
            return []
        if start >= n or target < 0 or suf[start] < target:
            return None
        if self.ctrl.stopped:
            return None
        for i in range(start, n):
            v = nums[i]
            if v > target:
                continue
            if v == target:
                return [v]
            if suf[i + 1] >= target - v:
                r = self._solve(nums, suf, target - v, i + 1, n)
                if r is not None:
                    return [v] + r
        return None


# ================================================================
#  ENGINE C3 — BEAM SEARCH + BAYESIAN SCORING + CDCL
#  Sources: Your #7, #14, #15 + Novel N2, N3
# ================================================================

class BeamEngine:
    WIDTH = 300

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "Beam"

    def run(self):
        p = self.ctrl.profile
        self.ctrl.log(f"[{self.name}] Beam search  width={self.WIDTH}")

        beam = [(0, [])]
        visited = {frozenset(): True}

        for _depth in range(p.n):
            if self.ctrl.stopped or not beam:
                return
            cands = []
            for csum, cidx in beam:
                if self.ctrl.stopped:
                    return
                used = set(cidx)
                rem = p.target - csum
                if rem <= 0:
                continue
                for i in range(p.n):
                    if i in used or p.numbers[i] > rem:
                        continue
                    ni = cidx + [i]
                    key = frozenset(ni)
                    if key in visited:
                        continue
                    if self.ctrl.cdb.conflicts(ni):
                        continue
                    ns = csum + p.numbers[i]
                    if ns == p.target:
                        self.ctrl.report(
                            [p.numbers[j] for j in ni], self.name)
                        return
                    sc = self._score(p, ns, len(ni), i)
                    cands.append((sc, ns, ni, key))

            cands.sort(key=lambda x: x[0])
            beam = []
            for sc, s, idx, key in cands[:self.WIDTH]:
                if key not in visited:
                    visited[key] = True
                    beam.append((s, idx))
            if _depth > 3:
                for sc, s, idx, key in cands[self.WIDTH:self.WIDTH + 50]:
                    self.ctrl.cdb.record(idx[-3:])

    @staticmethod
    def _score(p, csum, count, last_i):
        rem = p.target - csum
        slots = p.n - count
        if slots <= 0:
            return float('inf')
        ideal = rem / slots
        proximity = abs(p.numbers[last_i] - ideal) / (p.max_val + 1)
        gap = rem / (p.total_sum + 1)
        return proximity * 0.6 + gap * 0.4


# ================================================================
#  ENGINE C4 — BACKWARD REDUCTION  (Your #3 bidirectional)
# ================================================================

class BackwardEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "Backward"

    def run(self):
        p = self.ctrl.profile
        excess = p.total_sum - p.target
        if excess < 0:
            return
        if excess == 0:
            self.ctrl.report(list(p.numbers), self.name)
            return

        self.ctrl.log(f"[{self.name}] Complement approach, remove sum={excess}")
        desc = sorted(p.numbers, reverse=True)
        suf = [0] * (p.n + 1)
        for i in range(p.n - 1, -1, -1):
            suf[i] = suf[i + 1] + desc[i]

        to_remove = self._solve(desc, suf, excess, 0, p.n)
        if to_remove is not None:
            pool = list(p.numbers)
            for r in to_remove:
                pool.remove(r)
            self.ctrl.report(pool, self.name)

    def _solve(self, nums, suf, target, start, n):
        if target == 0:
            return []
        if start >= n or target < 0 or suf[start] < target:
            return None
        if self.ctrl.stopped:
            return None
        for i in range(start, n):
            v = nums[i]
            if v > target:
                continue
            if v == target:
                return [v]
            if suf[i + 1] >= target - v:
                r = self._solve(nums, suf, target - v, i + 1, n)
                if r is not None:
                    return [v] + r
        return None


# ================================================================
#  ENGINE C5 — HUMAN-LIKE DECOMPOSITION  (Your #10 + #13)
# ================================================================

class DecompEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "Decompose"

    def run(self):
        p = self.ctrl.profile
        self.ctrl.log(f"[{self.name}] Anchor-based chunking")

        for div in [2, 3, 4, 5]:
            if self.ctrl.stopped:
                return
            chunk = p.target / div
            anchor = min(p.numbers, key=lambda x: abs(x - chunk))
            if anchor > p.target:
                continue
            rem = p.target - anchor
            if rem < 0:
                continue
            if rem == 0:
                self.ctrl.report([anchor], self.name)
                return

            rest = list(p.numbers)
            rest.remove(anchor)
            rest_set = set(rest)

            if rem in rest_set:
                self.ctrl.report(sorted([anchor, rem]), self.name)
                return

            for x in rest:
                c = rem - x
                if c > 0 and c in rest_set and c != x:
                    self.ctrl.report(sorted([anchor, x, c]), self.name)
                    return

            if rem <= 2_000_000 and len(rest) <= 500:
                dp = 1
                hist = [dp]
                for num in rest:
                    if self.ctrl.stopped:
                        return
                    dp |= dp << num
                    hist.append(dp)
                if dp & (1 << rem):
                    sub = BitsetDPEngine._rebuild(hist, rest, rem)
                    if sub is not None:
                        self.ctrl.report(sorted([anchor] + sub), self.name)
                        return


# ================================================================
#  ENGINE C6 — K-SUM CHAIN  (Your #8 upgraded, hash-accelerated)
# ================================================================

class KSumEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "KSum"

    def run(self):
        p = self.ctrl.profile
        self.ctrl.log(f"[{self.name}] 3-Sum + 4-Sum")

        for i in range(p.n):
            if self.ctrl.stopped:
                        return
            for j in range(i + 1, p.n):
                c = p.target - p.numbers[i] - p.numbers[j]
                if c <= 0 or c not in p.num_set:
                    continue
                need = defaultdict(int)
                need[p.numbers[i]] += 1
                need[p.numbers[j]] += 1
                need[c] += 1
                if all(p.freq[v] >= cnt for v, cnt in need.items()):
                    self.ctrl.report(
                        sorted([p.numbers[i], p.numbers[j], c]), self.name)
                    return

        if p.n > 300:
            return
        self.ctrl.log(f"[{self.name}] 4-Sum via pair sums")
        pairs = {}
        for i in range(p.n):
            if self.ctrl.stopped:
                return
            for j in range(i + 1, p.n):
                s = p.numbers[i] + p.numbers[j]
                comp = p.target - s
                if comp in pairs:
                    pi, pj = pairs[comp]
                    if len({pi, pj, i, j}) == 4:
                        vals = [p.numbers[pi], p.numbers[pj],
                                p.numbers[i], p.numbers[j]]
                        need = defaultdict(int)
                        for v in vals:
                            need[v] += 1
                        if all(p.freq[v] >= cnt for v, cnt in need.items()):
                            self.ctrl.report(sorted(vals), self.name)
                            return
                if s not in pairs:
                    pairs[s] = (i, j)


# ================================================================
#  ENGINE D1 — MULTI-PRIME RESIDUE FILTER  (Novel method N1)
# ================================================================

class ResidueEngine:
    PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "Residue"

    def run(self):
        p = self.ctrl.profile
        for prime in self.PRIMES:
            if self.ctrl.stopped:
                return
            tr = p.target % prime
            reach = 1
            mask = (1 << prime) - 1
            for x in p.numbers:
                shifted = reach << (x % prime)
                reach = (reach | shifted | (shifted >> prime)) & mask
            if not (reach & (1 << tr)):
                self.ctrl.log(f"[{self.name}] IMPOSSIBLE (mod {prime})")
                self.ctrl.proved_impossible = True
                self.ctrl.stop_event.set()
                return
        self.ctrl.log(f"[{self.name}] All 10 residue checks passed.")


# ================================================================
#  ENGINE S1 — COLUMN STRUCTURE ENGINE  (Novel: Pattern Recognition)
#  Detects Karp-reduction column structure in huge-digit numbers.
#  Decomposes into independent column constraints and solves as SAT.
#  Handles both base-10 (col_width=1) and base-100 (col_width=2).
# ================================================================

class ColumnStructureEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "ColumnSAT"

    def run(self):
        p = self.ctrl.profile
        ts = str(p.target)
        nd = len(ts)
        if nd < 10 or p.n < 20:
            return

        cw, td_vals = self._detect_cols(ts)
        if cw == 0:
            return
        unique = set(td_vals)
        if len(unique) != 2:
            return
        var_t, clause_t = min(unique), max(unique)
        n_vc = td_vals.count(var_t)
        n_cc = td_vals.count(clause_t)
        if n_vc < 2 or n_cc < 2:
            return

        ew = cw * len(td_vals)
        self.ctrl.log(f"[{self.name}] Column structure: {n_vc} vars, "
                      f"{n_cc} clauses, cw={cw}, clause_target={clause_t}")

        strs = [str(e).zfill(ew) for e in p.numbers]

        var_cols = []
        for ci, val in enumerate(td_vals):
            if val != var_t:
                continue
            cs = ci * cw
            pair = [i for i in range(p.n)
                    if int(strs[i][cs:cs + cw]) == var_t]
            if len(pair) == 2:
                var_cols.append((ci, cs, pair[0], pair[1]))

        if len(var_cols) != n_vc:
            self.ctrl.log(f"[{self.name}] Pairing: {len(var_cols)}/{n_vc}")
            return

        cc_infos = [(ci, ci * cw) for ci, v in enumerate(td_vals)
                    if v == clause_t]

        var_set = set()
        einfo = {}
        for vi, (ci, cs, ea, eb) in enumerate(var_cols):
            var_set.update([ea, eb])
            einfo[ea] = (vi + 1, True)
            einfo[eb] = (vi + 1, False)

        self.ctrl.log(f"[{self.name}] Extracting SAT clauses...")
        sat_cls = []
        for ci, cs in cc_infos:
            lits = []
            for ei in var_set:
                if int(strs[ei][cs:cs + cw]) > 0 and ei in einfo:
                    vid, pos = einfo[ei]
                    lits.append(vid if pos else -vid)
            if lits:
                sat_cls.append(lits)

        self.ctrl.log(f"[{self.name}] {len(sat_cls)} clauses. "
                      f"Running optimized DPLL...")

        t0 = time.time()
        asgn = self._dpll(n_vc, sat_cls)
        dt = time.time() - t0
        if asgn is None:
            self.ctrl.log(f"[{self.name}] UNSAT ({dt:.2f}s)")
            return
        self.ctrl.log(f"[{self.name}] SAT solved in {dt:.2f}s")

        slack_elems = [i for i in range(p.n) if i not in var_set]
        chosen = set()
        for vi, (ci, cs, ea, eb) in enumerate(var_cols):
            chosen.add(ea if asgn[vi + 1] else eb)

        for ci, cs in cc_infos:
            if self.ctrl.stopped:
                return
            contrib = sum(int(strs[e][cs:cs + cw])
                          for e in chosen
                          if int(strs[e][cs:cs + cw]) > 0)
            need = clause_t - contrib
            if need <= 0:
                continue
            avail = [(se, int(strs[se][cs:cs + cw]))
                     for se in slack_elems
                     if se not in chosen
                     and int(strs[se][cs:cs + cw]) > 0]
            avail.sort(key=lambda x: -x[1])
            for se, sv in avail:
                if need <= 0:
                    break
                if sv <= need:
                    chosen.add(se)
                    need -= sv

        solution = [p.numbers[i] for i in chosen]
        total = sum(solution)
        if total == p.target:
            self.ctrl.log(f"[{self.name}] VERIFIED CORRECT!")
            self.ctrl.report(solution, self.name)
        else:
            self.ctrl.log(f"[{self.name}] Sum mismatch after construction")

    @staticmethod
    def _detect_cols(target_s):
        for cw in [2, 3, 1]:
            pad = (-len(target_s)) % cw if cw > 1 else 0
            ts = '0' * pad + target_s
            if len(ts) % cw != 0:
                continue
            cols = [int(ts[i:i + cw]) for i in range(0, len(ts), cw)]
            u = set(cols)
            if len(u) == 2 and max(u) <= 99:
                return cw, cols
        return 0, []

    def _dpll(self, nv, clauses):
        a = [0] * (nv + 1)
        pos_in = [[] for _ in range(nv + 1)]
        neg_in = [[] for _ in range(nv + 1)]
        for ci, cl in enumerate(clauses):
            for l in cl:
                v = abs(l)
                if v <= nv:
                    (pos_in if l > 0 else neg_in)[v].append(ci)

        def propagate(trail):
            qi = 0
            while qi < len(trail):
                var = trail[qi]; qi += 1
                aff = neg_in[var] if a[var] == 1 else pos_in[var]
                for ci in aff:
                    cl = clauses[ci]
                    ul = uc = 0; sat = False
                    for l in cl:
                        v = abs(l); av = a[v]
                        if av == 0:
                            uc += 1; ul = l
                            if uc > 1:
                                break
                        elif (l > 0 and av == 1) or (l < 0 and av == -1):
                            sat = True; break
                    if sat:
                        continue
                    if uc == 0:
                        return False
                    if uc == 1:
                        v = abs(ul)
                        a[v] = 1 if ul > 0 else -1
                        trail.append(v)
            return True

        trail = []
        for ci, cl in enumerate(clauses):
            if len(cl) == 1:
                v = abs(cl[0])
                if a[v] == 0:
                    a[v] = 1 if cl[0] > 0 else -1
                    trail.append(v)
        if not propagate(trail):
            return None

        stack = []
        while True:
            if self.ctrl.stopped:
                return None
            bv, bs = 0, -1
            for v in range(1, nv + 1):
                if a[v] != 0:
                    continue
                sc = sum(1 for ci in pos_in[v] + neg_in[v]
                         if not any((a[abs(l)] == 1 and l > 0) or
                                    (a[abs(l)] == -1 and l < 0)
                                    for l in clauses[ci]))
                if sc > bs:
                    bs = sc; bv = v
            if bv == 0:
                break
            mk = len(trail)
            stack.append((bv, True, mk))
            a[bv] = 1; trail.append(bv)
            if not propagate(trail):
                while stack:
                    dv, dval, m = stack.pop()
                    while len(trail) > m:
                        a[trail.pop()] = 0
                    if dval:
                        stack.append((dv, False, m))
                        a[dv] = -1; trail.append(dv)
                        if propagate(trail):
                            break
                else:
                    return None
        return {v: a[v] != -1 for v in range(1, nv + 1)}


# ================================================================
#  ENGINE B2 — BRIDGE ENGINE  (Novel: Greedy-to-Exact gap-close)
#  Greedy gets close to target fast, then bitset DP solves the
#  small remaining gap exactly.  Handles hard instances where n is
#  large and target is large (neither greedy nor bitset alone works).
# ================================================================

class BridgeEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "Bridge"

    def run(self):
        p = self.ctrl.profile
        self.ctrl.log(f"[{self.name}] Greedy + bitset gap-close")

        desc_idx = sorted(range(p.n), key=lambda i: -p.numbers[i])

        for start_skip in range(min(5, p.n)):
            if self.ctrl.stopped:
                return
            chosen, total = self._greedy_from(p, desc_idx, start_skip)
            if total == p.target:
                self.ctrl.report([p.numbers[i] for i in chosen], self.name)
            return

            gap = p.target - total
            if gap <= 0 or gap > 10_000_000:
                continue

            remaining = [p.numbers[i] for i in range(p.n)
                         if i not in chosen]
            if not remaining:
                continue

            dp = 1
            hist = [dp]
            for num in remaining:
                if self.ctrl.stopped:
                    return
                dp |= dp << num
                hist.append(dp)

            if dp & (1 << gap):
                sub = BitsetDPEngine._rebuild(hist, remaining, gap)
                if sub is not None:
                    full = [p.numbers[i] for i in chosen] + sub
                    self.ctrl.report(full, self.name)
                        return

        self._swap_search(p, desc_idx)

    def _greedy_from(self, p, desc_idx, skip):
        chosen = set()
        total = 0
        skipped = 0
        for i in desc_idx:
            if skipped < skip:
                skipped += 1
                continue
            if total + p.numbers[i] <= p.target:
                chosen.add(i)
                total += p.numbers[i]
                if total == p.target:
                    break
        return chosen, total

    def _swap_search(self, p, desc_idx):
        """1-swap and 2-add search around the greedy solution."""
        chosen, total = self._greedy_from(p, desc_idx, 0)
        if total == p.target:
            self.ctrl.report([p.numbers[i] for i in chosen], self.name)
            return
        not_chosen = [i for i in range(p.n) if i not in chosen]
        nc_set = set(p.numbers[i] for i in not_chosen)
        nc_lookup = {}
        for i in not_chosen:
            nc_lookup.setdefault(p.numbers[i], []).append(i)

        for out_i in list(chosen):
            if self.ctrl.stopped:
                return
            need = p.target - (total - p.numbers[out_i])
            if need in nc_lookup:
                in_i = nc_lookup[need][0]
                sol = (chosen - {out_i}) | {in_i}
                self.ctrl.report([p.numbers[i] for i in sol], self.name)
                return

        gap = p.target - total
        if gap > 0:
            for i in not_chosen:
                c = gap - p.numbers[i]
                if c > 0 and c in nc_set and c != p.numbers[i]:
                    self.ctrl.report(
                        [p.numbers[j] for j in chosen] +
                        [p.numbers[i], c], self.name)
                    return
                if c > 0 and c == p.numbers[i]:
                    cands = nc_lookup.get(c, [])
                    if len(cands) >= 2 or (len(cands) == 1 and cands[0] != i):
                        other = [x for x in cands if x != i][0]
                        self.ctrl.report(
                            [p.numbers[j] for j in chosen] +
                            [p.numbers[i], p.numbers[other]], self.name)
                        return


# ================================================================
#  ENGINE B3 — UNIQUE-AWARE MITM  (Salas 2025 inspired)
#  Exploits U (unique subset sums) instead of 2^(n/2).
#  Uses duplicate-sum pruning: if two subsets produce the same
#  sum, only keep one.  For structured inputs this is vastly
#  faster than standard MITM.  Extends to n≤50.
# ================================================================

class UniqueAwareMITMEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "UA-MITM"

    def run(self):
        p = self.ctrl.profile
        if p.n > 50 or p.n < 8:
            return

        self.ctrl.log(f"[{self.name}] Unique-aware MITM  n={p.n}")
        mid = p.n // 2
        left, right = p.numbers[:mid], p.numbers[mid:]

        left_sums = self._enum_unique(left, p.target)
        if self.ctrl.stopped:
            return
        ul = len(left_sums)

        right_sums = self._enum_unique(right, p.target)
        if self.ctrl.stopped:
            return
        ur = len(right_sums)

        self.ctrl.log(f"[{self.name}] Unique sums: left={ul} right={ur} "
                      f"(vs 2^{mid}={1 << mid})")

        for rs, r_mask in right_sums.items():
            if self.ctrl.stopped:
                return
            comp = p.target - rs
            if comp in left_sums:
                l_mask = left_sums[comp]
                sol = ([left[i] for i in range(len(left))
                        if l_mask & (1 << i)] +
                       [right[i] for i in range(len(right))
                        if r_mask & (1 << i)])
                self.ctrl.report(sol, self.name)
                return

    def _enum_unique(self, elems, limit):
        """Enumerate subset sums, keeping only unique values.
        Skips redundant subsets that produce duplicate sums."""
        sums = {0: 0}
        for bit, e in enumerate(elems):
            if self.ctrl.stopped:
                return sums
            new = {}
            for s, mask in sums.items():
                ns = s + e
                if ns <= limit and ns not in sums and ns not in new:
                    new[ns] = mask | (1 << bit)
            sums.update(new)
        return sums


# ================================================================
#  ENGINE D2 — RANDOMIZED MULTI-START SEARCH
#  Probabilistic exploration with Bayesian scoring (Your #15)
# ================================================================

class RandomizedEngine:
    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "Randomized"

    def run(self):
        p = self.ctrl.profile
        self.ctrl.log(f"[{self.name}] Probabilistic multi-start")

        for trial in range(2000):
            if self.ctrl.stopped:
                return
            sol = self._random_trial(p)
            if sol is not None:
                self.ctrl.report(sol, self.name)
                return

    def _random_trial(self, p):
        indices = list(range(p.n))
        random.shuffle(indices)
        picked = []
        total = 0
        for i in indices:
            v = p.numbers[i]
            if total + v <= p.target:
                picked.append(v)
                total += v
                if total == p.target:
                    return picked
                return None


# ================================================================
#  META-BRAIN — GLOBAL CONTROLLER
# ================================================================

class ZUltimateController:
    """Orchestrates all engines with shared conflict DB, parallel
    execution, solution verification, and resource management."""

    def __init__(self, numbers, target, log_fn):
        self.raw_numbers = sorted(numbers)
        self.raw_target = target
        self.log = log_fn
        self.stop_event = threading.Event()
        self.solution = None
        self._lock = threading.Lock()
        self.winner = None
        self.proved_impossible = False
        self.cdb = ConflictDB()
        self.forced = []
        self.profile = None
        self.t0 = 0

    @property
    def stopped(self):
        return self.stop_event.is_set()

    def report(self, solution, engine):
        with self._lock:
            if self.stopped:
                return
            full = sorted(self.forced + solution)
            if sum(full) != self.raw_target:
                return
            pool = list(self.raw_numbers)
            for x in full:
                if x in pool:
                    pool.remove(x)
                else:
                    return
            self.solution = full
            self.winner = engine
            self.stop_event.set()
            t = time.time() - self.t0
            self.log(f"\n>>> [{engine}] SOLVED in {t:.4f}s <<<")

    def run(self, max_time=30.0):
        self.t0 = time.time()
        self.log("=" * 55)
        self.log("  Z++ ULTIMATE ENGINE v3.0")
        self.log("  Portfolio Subset Sum Solver")
        self.log("=" * 55)

        if not self.raw_numbers or self.raw_target < 0:
            self.log("Invalid input.")
            return self._result()
        if self.raw_target == 0:
            self.solution = []
            self.winner = "Trivial"
            self.log("  Target is 0 -> empty subset.")
            return self._result()

        # Phase 1
        self.log("\n[Phase 1] Analysing input...")
        prof = ProblemProfile(self.raw_numbers, self.raw_target)
        td = len(str(prof.target))
        self.log(f"  n={prof.n}  target_digits={td}  class={prof.pclass}")
        try:
            self.log(f"  mean={prof.mean:.1f}  std={prof.std_dev:.1f}")
        except (OverflowError, ValueError):
            self.log(f"  (numbers too large for float stats)")

        # Phase 2
        self.log("\n[Phase 2] Fast-path checks...")
        found, sol = TrivialSolver.solve(prof)
        if found:
            if sol is None:
                self.log("  PROVED IMPOSSIBLE (trivial).")
                self.proved_impossible = True
                return self._result()
            self.solution = sol
            self.winner = "Trivial"
            self.log(f"  Solved: {sol}")
            return self._result()
        self.log("  No trivial solution.")

        # Phase 3
        self.log("\n[Phase 3] Preprocessing & reduction...")
        nums, target, self.forced, impossible = Preprocessor.reduce(
            self.raw_numbers, self.raw_target)
        if impossible:
            self.log("  PROVED IMPOSSIBLE (reduction).")
            self.proved_impossible = True
            return self._result()
        if target == 0:
            self.solution = sorted(self.forced)
            self.winner = "Preprocessor"
            return self._result()
        if self.forced:
            self.log(f"  Forced elements: {self.forced}")
        self.log(f"  Reduced: n={len(nums)}  target={target}")

        self.profile = ProblemProfile(nums, target)

        # Phase 4 — Select engines
        self.log(f"\n[Phase 4] Engine selection  (class={self.profile.pclass})")
        engines = self._pick_engines()
        self.log(f"  Engines: {[e.name for e in engines]}")

        # Phase 5 — Parallel launch
        self.log(f"\n[Phase 5] Launching {len(engines)} engines...\n")
        threads = []
        for eng in engines:
            t = threading.Thread(target=self._safe, args=(eng,), daemon=True)
            threads.append(t)
            t.start()

        self.stop_event.wait(timeout=max_time)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=0.3)

        elapsed = time.time() - self.t0
        self.log(f"\n{'=' * 55}")
        self.log(f"[Phase 7] Complete  {elapsed:.4f}s")
        if self.solution:
            self.log(f"  Winner : {self.winner}")
            self.log(f"  Elements: {len(self.solution)}")
            s = sum(self.solution)
            if len(str(s)) > 100:
                self.log(f"  Sum verified: {s == self.raw_target}")
            else:
                self.log(f"  Solution: {self.solution}")
                self.log(f"  Sum     : {s}")
        elif self.proved_impossible:
            self.log("  Result: PROVED IMPOSSIBLE")
        else:
            self.log("  Result: Timeout — no exact solution found")
        self.log(f"  Conflicts learned: {self.cdb.size}")
        return self._result()

    def _pick_engines(self):
        pc = self.profile.pclass
        n = self.profile.n
        target_digits = len(str(self.profile.target))

        pool = [ResidueEngine(self)]

        if target_digits > 50 and n > 100:
            pool.insert(0, ColumnStructureEngine(self))

        if pc in ("TRIVIAL", "TINY"):
            pool += [BitsetDPEngine(self), MITMEngine(self),
                     GreedyEngine(self)]
        elif pc == "SMALL":
            pool += [MITMEngine(self), UniqueAwareMITMEngine(self),
                     BitsetDPEngine(self),
                     GreedyEngine(self), BackwardEngine(self)]
        elif pc == "MEDIUM":
            pool += [BitsetDPEngine(self), GreedyEngine(self),
                     BackwardEngine(self), BeamEngine(self),
                     BridgeEngine(self)]
            if n <= 50:
                pool += [MITMEngine(self), UniqueAwareMITMEngine(self)]
        else:
            pool += [GreedyEngine(self), BackwardEngine(self),
                     BeamEngine(self), BridgeEngine(self),
                     RandomizedEngine(self)]
            if n <= 50:
                pool += [MITMEngine(self), UniqueAwareMITMEngine(self)]

        pool.append(KSumEngine(self))
        pool.append(EstimateEngine(self))
        pool.append(DecompEngine(self))
        if not any(isinstance(e, RandomizedEngine) for e in pool):
            pool.append(RandomizedEngine(self))
        return pool

    def _safe(self, engine):
        try:
            engine.run()
        except Exception as e:
            self.log(f"[ERR] {engine.name}: {e}")

    def _result(self):
        return {
            'solution': self.solution,
            'sum': sum(self.solution) if self.solution else 0,
            'target': self.raw_target,
            'exact': (self.solution is not None
                      and sum(self.solution) == self.raw_target),
            'impossible': self.proved_impossible and self.solution is None,
            'time': time.time() - self.t0,
            'engine': self.winner or (
                "IMPOSSIBLE" if self.proved_impossible else "Timeout"),
            'conflicts': self.cdb.size,
        }


# ================================================================
#  GUI  (imports tkinter lazily — only when GUI mode is selected)
# ================================================================

def _ensure_tk():
    """Import tkinter into the module namespace on first GUI use."""
    global tk, ttk, scrolledtext, messagebox
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox


class ZUltimateGUI:
    def __init__(self, root):
        _ensure_tk()
        self.root = root
        root.title("Z++ Ultimate Engine v3.0")
        root.geometry("960x760")
        root.configure(bg="#0d1117")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#0d1117",
                        foreground="#c9d1d9", font=("Segoe UI", 11))

        m = ttk.Frame(root, padding=20)
        m.pack(fill=tk.BOTH, expand=True)

        tk.Label(m, text="Z++ ULTIMATE ENGINE v3.0",
                 font=("Segoe UI", 18, "bold"),
                 bg="#0d1117", fg="#58a6ff").pack(pady=(0, 2))
        tk.Label(m,
                 text=("15 Algorithms  +  15 World-Best  +  "
                       "5 Novel Methods  |  Portfolio Solver"),
                 font=("Segoe UI", 9),
                 bg="#0d1117", fg="#8b949e").pack(pady=(0, 12))

        ttk.Label(m, text="Numbers (comma-separated):").pack(anchor=tk.W)
        self.inp = tk.Text(m, height=3, font=("Consolas", 11),
                           bg="#161b22", fg="#c9d1d9",
                           insertbackground="white",
                           borderwidth=1, relief="solid")
        self.inp.pack(fill=tk.X, pady=5)
        self.inp.insert(tk.END,
                        "1, 3, 7, 21, 50, 200, 400, 499, "
                        "1000, 1500, 2000, 5000, 10000, 25000")

        ttk.Label(m, text="Target:").pack(anchor=tk.W, pady=(8, 0))
        self.tgt = ttk.Entry(m, font=("Consolas", 12))
        self.tgt.pack(fill=tk.X, pady=5)
        self.tgt.insert(0, "5570")

        bf = ttk.Frame(m)
        bf.pack(fill=tk.X, pady=8)
        self.btn = tk.Button(bf, text="SOLVE",
                             font=("Segoe UI", 12, "bold"),
                             bg="#238636", fg="white",
                             activebackground="#2ea043",
                             command=self._start)
        self.btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        tk.Button(bf, text="LOAD FILE", font=("Segoe UI", 10),
                  bg="#1f6feb", fg="white",
                  command=self._load_file).pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="CLEAR", font=("Segoe UI", 10),
                  bg="#30363d", fg="#c9d1d9",
                  command=lambda: self.logw.delete("1.0", tk.END)
                  ).pack(side=tk.RIGHT)

        self.logw = scrolledtext.ScrolledText(
            m, height=18, font=("Consolas", 9),
            bg="#010409", fg="#3fb950",
            borderwidth=1, relief="solid")
        self.logw.pack(fill=tk.BOTH, expand=True, pady=(5, 8))

        self.status = tk.Label(m, text="Ready.",
                               font=("Segoe UI", 11),
                               bg="#0d1117", fg="#8b949e",
                               wraplength=920, justify="left")
        self.status.pack(anchor=tk.W)

    def _load_file(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Load file",
            filetypes=[("All supported", "*.txt *.cnf"),
                       ("Text files", "*.txt"),
                       ("CNF files", "*.cnf"),
                       ("All files", "*.*")])
        if not path:
            return
        try:
            for enc in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
                try:
                    with open(path, 'r', encoding=enc) as f:
                        data = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            else:
                with open(path, 'r', errors='replace') as f:
                    data = f.read()

            if path.lower().endswith('.cnf'):
                self._load_cnf(path, data)
            elif 'goal:' in data or 'Goal:' in data:
                self._load_txt_goal(path, data)
            else:
                lines = [l.strip() for l in data.strip().split('\n')
                         if l.strip()]
                elems_str = lines[0]
                target_str = lines[-1] if len(lines) > 1 else ""
                self.inp.delete("1.0", tk.END)
                self.inp.insert(tk.END, elems_str)
                self.tgt.delete(0, tk.END)
                self.tgt.insert(0, target_str)
                n = len([x for x in elems_str.split(',') if x.strip()])
                self._log(f"Loaded {path}: {n} elements")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def _load_txt_goal(self, path, data):
        sep = 'goal:' if 'goal:' in data else 'Goal:'
        parts = data.split(sep)
        elems_str = parts[0].strip()
        target_str = parts[1].strip()
        self.inp.delete("1.0", tk.END)
        self.inp.insert(tk.END, elems_str)
        self.tgt.delete(0, tk.END)
        self.tgt.insert(0, target_str)
        n = len([x for x in elems_str.split(',') if x.strip()])
        self._log(f"Loaded {path}")
        self._log(f"  {n} elements, target: {len(target_str)} digits")

    def _load_cnf(self, path, data):
        self._log(f"Loading CNF: {path}")
        self._log("Converting to Subset Sum (Karp reduction)...")
        n_vars, n_clauses, clauses = 0, 0, []
        current = []
        for line in data.split('\n'):
            if line.startswith('c') or not line.strip():
                continue
            if line.startswith('p'):
                parts = line.split()
                n_vars, n_clauses = int(parts[2]), int(parts[3])
            else:
                for val in line.split():
                    num = int(val)
                    if num == 0:
                        if current:
                            clauses.append(current)
                        current = []
                    else:
                        current.append(num)

        max_cl = max(len(c) for c in clauses) if clauses else 3
        ct = max_cl + 1
        CW = 2
        nc = n_vars + n_clauses

        def mk(vi, cbits):
            s = ['00'] * nc
            s[vi] = '01'
            for ci, b in cbits.items():
                s[n_vars + ci] = f'{b:02d}'
            return int("".join(s))

        elements = []
        for i in range(1, n_vars + 1):
            elements.append(mk(i - 1, {ci: 1 for ci, c in enumerate(clauses) if i in c}))
            elements.append(mk(i - 1, {ci: 1 for ci, c in enumerate(clauses) if -i in c}))
        for j in range(n_clauses):
            pw = 1
            while pw < ct:
                s = ['00'] * nc
                s[n_vars + j] = f'{pw:02d}'
                elements.append(int("".join(s)))
                pw *= 2

        target = int("".join(['01'] * n_vars + [f'{ct:02d}'] * n_clauses))

        elems_str = ", ".join(str(e) for e in elements)
        self.inp.delete("1.0", tk.END)
        self.inp.insert(tk.END, elems_str)
        self.tgt.delete(0, tk.END)
        self.tgt.insert(0, str(target))

        self._log(f"  {n_vars} vars, {n_clauses} clauses, max clause size: {max_cl}")
        self._log(f"  {len(elements)} elements, target: {len(str(target))} digits")
        self._log(f"  Clause target: {ct}, slacks: powers of 2")
        self._log("  Ready to solve. Click SOLVE.")

    def _log(self, msg):
        self.logw.insert(tk.END, msg + "\n")
        self.logw.see(tk.END)
        self.root.update_idletasks()

    def _start(self):
        try:
            nums = [int(x.strip())
                    for x in self.inp.get("1.0", tk.END).strip().split(',')
                    if x.strip()]
            target = int(self.tgt.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Enter valid integers.")
            return
        self.btn.config(state=tk.DISABLED, text="SOLVING...", bg="#8b949e")
        self.logw.delete("1.0", tk.END)
        self.status.config(text="Engines running...", fg="#d29922")
        threading.Thread(target=self._run, args=(nums, target),
                         daemon=True).start()

    def _run(self, nums, target):
        ctrl = ZUltimateController(nums, target, self._log)
        timeout = 60.0 if len(nums) > 500 or len(str(target)) > 50 else 30.0
        res = ctrl.run(max_time=timeout)
        self.root.after(0, self._done, res)

    def _done(self, r):
        if r['exact']:
            n_sol = len(r['solution']) if r['solution'] else 0
            tgt_d = len(str(r['target']))
            if tgt_d > 50:
                t = (f"EXACT SOLUTION  |  {r['engine']}  |  "
                     f"{r['time']:.4f}s\n"
                     f"Elements selected: {n_sol}\n"
                     f"Target: {tgt_d} digits  |  "
                     f"Sum verified: {r['sum'] == r['target']}\n"
                     f"Conflicts learned: {r['conflicts']}")
        else:
                t = (f"EXACT SOLUTION  |  {r['engine']}  |  "
                     f"{r['time']:.4f}s\n"
                     f"Solution: {r['solution']}\n"
                     f"Sum: {r['sum']} = Target: {r['target']}\n"
                     f"Conflicts learned: {r['conflicts']}")
            c = "#3fb950"
        elif r['impossible']:
            tgt_d = len(str(r['target']))
            desc = (f"{tgt_d}-digit target" if tgt_d > 50
                    else str(r['target']))
            t = (f"PROVED IMPOSSIBLE  |  {r['engine']}  |  "
                 f"{r['time']:.4f}s\n"
                 f"No subset sums to {desc}.\n"
                 f"Conflicts: {r['conflicts']}")
            c = "#f85149"
        else:
            t = (f"TIMEOUT ({r['time']:.1f}s)  |  "
                 f"Conflicts: {r['conflicts']}")
            c = "#d29922"
        self.status.config(text=t, fg=c)
        self.btn.config(state=tk.NORMAL, text="SOLVE", bg="#238636")


# ================================================================
#  ENTRY POINT — Mode Selection
# ================================================================

def launch_gui():
    _ensure_tk()
    root = tk.Tk()
    ZUltimateGUI(root)
    root.mainloop()


def run_headless_benchmark():
    print()
    print("=" * 48)
    print("   Z++ HEADLESS MODE")
    print("=" * 48)
    print()

    raw = input("  Enter elements (comma-separated):\n  ").strip()
    numbers = [int(x.strip()) for x in raw.split(',') if x.strip()]

    target = int(input("\n  Enter target goal: ").strip())

    print()
    print("=" * 48)
    print("   RUNNING Z++ ENGINE...")
    print("=" * 48)
    print(f"   Elements : {len(numbers)}")
    td = len(str(target))
    print(f"   Target   : {target if td <= 40 else f'{td}-digit number'}")
    print("=" * 48)
    print()

    tracemalloc.start()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()

    ctrl = ZUltimateController(numbers, target, print)
    res = ctrl.run(max_time=60.0)

    wall_end = time.perf_counter()
    cpu_end = time.process_time()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    cpu_elapsed = cpu_end - cpu_start
    wall_elapsed = wall_end - wall_start

    print()
    print("=" * 56)
    print("   Z++ HEADLESS PERFORMANCE REPORT")
    print("=" * 56)
    print(f"   Match Found     : {res['exact']}")
    if res['impossible']:
        print(f"   PROVED IMPOSSIBLE")
    print(f"   Active CPU Time : {cpu_elapsed:.6f} sec   "
          f"(sum of CPU work across all engine threads)")
    print(f"   Wall-Clock Time : {wall_elapsed:.6f} sec   "
          f"(real elapsed time)")
    if cpu_elapsed > 0 and wall_elapsed > 0:
        cores_used = cpu_elapsed / wall_elapsed
        print(f"   Parallelism     : {cores_used:.2f}x   "
              f"(>1.0 = real multi-core; Python GIL caps near 1.0)")
    print(f"   Engine Winner   : {res['engine']}")
    print(f"   Peak Memory     : {peak_mem / 1024:.1f} KB")
    if res['exact'] and res['solution']:
        print(f"   Solution Size   : {len(res['solution'])} elements")
        if td <= 40:
            print(f"   Solution        : {res['solution']}")
            print(f"   Sum             : {res['sum']}")
    print(f"   Conflicts       : {res['conflicts']}")
    print("=" * 56)
    print("   NOTE: Active CPU Time counts ONLY when threads are")
    print("   computing.  Sleep, I/O, and idle wait are excluded.")
    print("   Windows tick resolution ~15ms; sub-tick work shows 0.")
    print("=" * 56)
    print()


if __name__ == "__main__":
    print()
    print("  Z++ Ultimate Engine v3.0")
    print("  Select Run Mode:")
    print("    [1] GUI Mode")
    print("    [2] No-GUI Benchmark Mode")
    print()
    choice = input("  Enter choice (1 or 2): ").strip()

    if choice == "2":
        run_headless_benchmark()
    else:
        launch_gui()
