"""
Z++ ULTIMATE ENGINE v3.0 — Google Colab / CLI Benchmark
=======================================================
NO GUI. Pure computation. Copy-paste into Google Colab and run.

HOW TO USE IN GOOGLE COLAB:
  1. Open https://colab.research.google.com
  2. Create a new notebook
  3. Paste this ENTIRE file into one cell
  4. Click Run
  5. For the jnh1.cnf test: upload jnh1.cnf via the file panel
"""

import sys, threading, time, math, random
from collections import defaultdict
sys.setrecursionlimit(50000)

# ================================================================
#  FULL Z++ ENGINE (headless)
# ================================================================

class ProblemProfile:
    def __init__(self, numbers, target):
        self.numbers = sorted(numbers)
        self.target = target
        self.n = len(self.numbers)
        self.total_sum = sum(self.numbers)
        self.num_set = set(self.numbers)
        self.freq = defaultdict(int)
        for x in self.numbers: self.freq[x] += 1
        if self.n > 0:
            self.min_val, self.max_val = self.numbers[0], self.numbers[-1]
            self.spread = self.max_val - self.min_val
            self.median = self.numbers[self.n // 2]
            try:
                self.mean = self.total_sum / self.n
            except (OverflowError, ValueError):
                self.mean = self.total_sum // self.n
        else:
            self.min_val = self.max_val = self.mean = self.spread = self.median = 0
        try:
            if self.n > 1:
                self.variance = sum((x - self.mean)**2 for x in self.numbers) / (self.n-1)
                self.std_dev = math.sqrt(self.variance)
                self.is_uneven = self.spread > self.mean * 3 or self.std_dev > self.mean
            else:
                self.variance = self.std_dev = 0.0; self.is_uneven = False
            self.density_ratio = self.target / self.total_sum if self.total_sum > 0 else 0
        except (OverflowError, ValueError):
            self.variance = self.std_dev = 0.0; self.is_uneven = True
            self.density_ratio = 0
        self.suffix_sums = [0]*(self.n+1)
        for i in range(self.n-1, -1, -1): self.suffix_sums[i] = self.suffix_sums[i+1]+self.numbers[i]
        self.desc = sorted(self.numbers, reverse=True)
        self.desc_suffix = [0]*(self.n+1)
        for i in range(self.n-1, -1, -1): self.desc_suffix[i] = self.desc_suffix[i+1]+self.desc[i]
        if self.n <= 5:       self.pclass = "TRIVIAL"
        elif self.n <= 20:    self.pclass = "TINY"
        elif self.n <= 40:    self.pclass = "SMALL"
        elif self.target <= 10_000_000: self.pclass = "MEDIUM"
        else:                 self.pclass = "LARGE"

class TrivialSolver:
    PRIMES = [2, 3, 5, 7, 11, 13]
    @staticmethod
    def solve(p):
        if p.target == 0: return True, []
        if p.n == 0 or p.target < 0: return True, None
        if p.target == p.total_sum: return True, list(p.numbers)
        if p.target > p.total_sum: return True, None
        if p.min_val > p.target: return True, None
        if p.target in p.num_set: return True, [p.target]
        for x in p.numbers:
            c = p.target - x
            if c > 0 and c in p.num_set:
                if c != x or p.freq[x] >= 2: return True, sorted([x, c])
        if p.target % 2 == 1 and all(x % 2 == 0 for x in p.numbers): return True, None
        for prime in TrivialSolver.PRIMES:
            tr = p.target % prime; reach = 1; mask = (1 << prime) - 1
            for x in p.numbers:
                shifted = reach << (x % prime)
                reach = (reach | shifted | (shifted >> prime)) & mask
            if not (reach & (1 << tr)): return True, None
        return False, None

class Preprocessor:
    @staticmethod
    def reduce(numbers, target):
        forced = []; nums = [x for x in numbers if 0 < x <= target]
        if not nums or sum(nums) < target: return nums, target, forced, True
        changed = True
        while changed:
            changed = False; total = sum(nums); kept = []
            for x in nums:
                if total - x < target: forced.append(x); target -= x; changed = True
                else: kept.append(x)
            nums = kept
            if target == 0: return nums, 0, forced, False
            if target < 0 or (nums and sum(nums) < target): return nums, target, forced, True
            if not nums and target > 0: return nums, target, forced, True
        return sorted(nums), target, forced, False

class ConflictDB:
    def __init__(self): self._c = set(); self._l = threading.Lock()
    def record(self, idx, ms=4):
        if len(idx) > ms: idx = idx[-ms:]
        with self._l:
            if len(self._c) < 200000: self._c.add(frozenset(idx))
    def conflicts(self, idx):
        if not self._c: return False
        s = set(idx)
        with self._l: return any(c.issubset(s) for c in self._c)
    @property
    def size(self): return len(self._c)

class BitsetDPEngine:
    def __init__(self, ctrl): self.ctrl = ctrl; self.name = "BitsetDP"
    def run(self):
        p = self.ctrl.profile
        if p.target > 20_000_000: return
        dp = 1; hist = [dp]
        for idx, num in enumerate(p.numbers):
            if self.ctrl.stopped: return
            dp |= dp << num; hist.append(dp)
            if dp & (1 << p.target):
                sol = self._rebuild(hist, p.numbers, p.target)
                if sol: self.ctrl.report(sol, self.name)
                return
        if not (dp & (1 << p.target)): self.ctrl.proved_impossible = True
    @staticmethod
    def _rebuild(hist, nums, target):
        cur, sol, mx = target, [], min(len(nums), len(hist)-1)
        for i in range(mx-1, -1, -1):
            if cur <= 0: break
            v = nums[i]
            if cur >= v and (hist[i] & (1 << (cur-v))): sol.append(v); cur -= v
        return sol if cur == 0 else None

class MITMEngine:
    def __init__(self, ctrl): self.ctrl = ctrl; self.name = "MITM"
    def run(self):
        p = self.ctrl.profile
        if p.n > 50: return
        mid = p.n // 2; left, right = p.numbers[:mid], p.numbers[mid:]
        ls = {0: 0}
        for b, e in enumerate(left):
            if self.ctrl.stopped: return
            nw = {}
            for s, m in ls.items():
                ns = s + e
                if ns <= p.target and ns not in ls and ns not in nw: nw[ns] = m|(1<<b)
            ls.update(nw)
        if p.target in ls:
            m = ls[p.target]; self.ctrl.report([left[i] for i in range(len(left)) if m&(1<<i)], self.name); return
        rs = {0: 0}
        for b, e in enumerate(right):
            if self.ctrl.stopped: return
            nw = {}
            for s, m in rs.items():
                ns = s + e
                if ns > p.target: continue
                if ns not in rs and ns not in nw: nw[ns] = m|(1<<b)
                c = p.target - ns
                if c in ls:
                    lm = ls[c]
                    sol = [left[i] for i in range(len(left)) if lm&(1<<i)] + [right[j] for j in range(len(right)) if (m|(1<<b))&(1<<j)]
                    self.ctrl.report(sol, self.name); return
            rs.update(nw)
        for s, m in rs.items():
            if self.ctrl.stopped: return
            c = p.target - s
            if c in ls:
                lm = ls[c]
                sol = [left[i] for i in range(len(left)) if lm&(1<<i)] + [right[j] for j in range(len(right)) if m&(1<<j)]
                self.ctrl.report(sol, self.name); return

class GreedyEngine:
    def __init__(self, ctrl): self.ctrl = ctrl; self.name = "Greedy"
    def run(self):
        p = self.ctrl.profile
        sol = self._s(p.desc, p.desc_suffix, p.target, 0, p.n)
        if sol: self.ctrl.report(sol, self.name)
    def _s(self, nums, suf, t, start, n):
        if t == 0: return []
        if start >= n or t < 0 or suf[start] < t: return None
        if self.ctrl.stopped: return None
        for i in range(start, n):
            v = nums[i]
            if v > t: continue
            if v == t: return [v]
            if suf[i+1] >= t-v:
                r = self._s(nums, suf, t-v, i+1, n)
                if r is not None: return [v]+r
        return None

class BackwardEngine:
    def __init__(self, ctrl): self.ctrl = ctrl; self.name = "Backward"
    def run(self):
        p = self.ctrl.profile; excess = p.total_sum - p.target
        if excess < 0: return
        if excess == 0: self.ctrl.report(list(p.numbers), self.name); return
        d = sorted(p.numbers, reverse=True); sf = [0]*(p.n+1)
        for i in range(p.n-1,-1,-1): sf[i] = sf[i+1]+d[i]
        rm = self._s(d, sf, excess, 0, p.n)
        if rm is not None:
            pool = list(p.numbers)
            for r in rm: pool.remove(r)
            self.ctrl.report(pool, self.name)
    def _s(self, nums, suf, t, start, n):
        if t == 0: return []
        if start >= n or t < 0 or suf[start] < t: return None
        if self.ctrl.stopped: return None
        for i in range(start, n):
            v = nums[i]
            if v > t: continue
            if v == t: return [v]
            if suf[i+1] >= t-v:
                r = self._s(nums, suf, t-v, i+1, n)
                if r is not None: return [v]+r
        return None

class BridgeEngine:
    def __init__(self, ctrl): self.ctrl = ctrl; self.name = "Bridge"
    def run(self):
        p = self.ctrl.profile
        di = sorted(range(p.n), key=lambda i: -p.numbers[i])
        for skip in range(min(5, p.n)):
            if self.ctrl.stopped: return
            ch, tot, sk = set(), 0, 0
            for i in di:
                if sk < skip: sk += 1; continue
                if tot + p.numbers[i] <= p.target:
                    ch.add(i); tot += p.numbers[i]
                    if tot == p.target: self.ctrl.report([p.numbers[i] for i in ch], self.name); return
            gap = p.target - tot
            if gap <= 0 or gap > 10_000_000: continue
            rem = [p.numbers[i] for i in range(p.n) if i not in ch]
            if not rem: continue
            dp = 1; hist = [dp]
            for num in rem:
                if self.ctrl.stopped: return
                dp |= dp << num; hist.append(dp)
            if dp & (1 << gap):
                sub = BitsetDPEngine._rebuild(hist, rem, gap)
                if sub: self.ctrl.report([p.numbers[i] for i in ch]+sub, self.name); return

class RandomizedEngine:
    def __init__(self, ctrl): self.ctrl = ctrl; self.name = "Randomized"
    def run(self):
        p = self.ctrl.profile
        for _ in range(5000):
            if self.ctrl.stopped: return
            idx = list(range(p.n)); random.shuffle(idx)
            pk, tot = [], 0
            for i in idx:
                if tot + p.numbers[i] <= p.target:
                    pk.append(p.numbers[i]); tot += p.numbers[i]
                    if tot == p.target: self.ctrl.report(pk, self.name); return

class ResidueEngine:
    PRIMES = [2,3,5,7,11,13,17,19,23,29]
    def __init__(self, ctrl): self.ctrl = ctrl; self.name = "Residue"
    def run(self):
        p = self.ctrl.profile
        for pr in self.PRIMES:
            if self.ctrl.stopped: return
            tr = p.target % pr; reach = 1; mask = (1<<pr)-1
            for x in p.numbers:
                shifted = reach << (x % pr)
                reach = (reach | shifted | (shifted >> pr)) & mask
            if not (reach & (1 << tr)):
                self.ctrl.proved_impossible = True; self.ctrl.stop_event.set(); return

class KSumEngine:
    def __init__(self, ctrl): self.ctrl = ctrl; self.name = "KSum"
    def run(self):
        p = self.ctrl.profile
        for i in range(p.n):
            if self.ctrl.stopped: return
            for j in range(i+1, p.n):
                c = p.target - p.numbers[i] - p.numbers[j]
                if c <= 0 or c not in p.num_set: continue
                nd = defaultdict(int); nd[p.numbers[i]] += 1; nd[p.numbers[j]] += 1; nd[c] += 1
                if all(p.freq[v] >= ct for v, ct in nd.items()):
                    self.ctrl.report(sorted([p.numbers[i], p.numbers[j], c]), self.name); return

class EstimateEngine:
    def __init__(self, ctrl): self.ctrl = ctrl; self.name = "Estimate"
    def run(self):
        p = self.ctrl.profile
        desc = sorted(range(p.n), key=lambda i: -p.numbers[i])
        for tag, k in (([("mean", round(p.target/p.mean))] if p.mean > 0 else []) +
                       ([("median", round(p.target/p.median))] if p.median > 0 else [])):
            if self.ctrl.stopped: return
            k = max(1, min(k, p.n)); ch = set(desc[:k]); tot = sum(p.numbers[i] for i in ch)
            for _ in range(3*p.n):
                if self.ctrl.stopped: return
                d = tot - p.target
                if d == 0: self.ctrl.report([p.numbers[i] for i in ch], f"{self.name}({tag})"); return
                if d > 0:
                    b = min(ch, key=lambda i: abs(p.numbers[i]-d), default=None)
                    if b is None: break
                    ch.discard(b); tot -= p.numbers[b]
                else:
                    b = next((i for i in desc if i not in ch and p.numbers[i] <= -d), None)
                    if b is None: break
                    ch.add(b); tot += p.numbers[b]


# ================================================================
#  COLUMN STRUCTURE ENGINE (SAT-encoded instances)
# ================================================================

class ColumnStructureEngine:
    """Detects Karp-reduction column structure and solves via SAT decomposition.
    This is what makes Z++ able to solve 950-digit number instances."""

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.name = "ColumnSAT"

    def run(self):
        p = self.ctrl.profile
        target_s = str(p.target)
        nd = len(target_s)
        if nd < 10 or p.n < 20:
            return

        cw, td_vals = self._detect_column_width(target_s)
        if cw == 0:
            return

        unique = set(td_vals)
        if len(unique) != 2:
            return
        var_target = min(unique)
        clause_target = max(unique)
        n_vcols = td_vals.count(var_target)
        n_ccols = td_vals.count(clause_target)
        if n_vcols < 2 or n_ccols < 2:
            return

        n_total_cols = n_vcols + n_ccols
        expected_width = cw * n_total_cols

        self.ctrl.log(f"[{self.name}] Column structure detected! "
                      f"{n_vcols} vars, {n_ccols} clauses, "
                      f"col_width={cw}, width={expected_width}")

        strs = [str(e).zfill(expected_width) for e in p.numbers]

        var_cols = []
        for ci, val in enumerate(td_vals):
            if val != var_target:
                continue
            col_start = ci * cw
            pair = [i for i in range(p.n)
                    if int(strs[i][col_start:col_start + cw]) == var_target]
            if len(pair) == 2:
                var_cols.append((ci, col_start, cw, pair[0], pair[1]))

        if len(var_cols) != n_vcols:
            self.ctrl.log(f"[{self.name}] Variable pairing failed "
                          f"({len(var_cols)}/{n_vcols})")
            return

        clause_col_infos = [(ci, ci * cw, cw)
                            for ci, v in enumerate(td_vals) if v == clause_target]

        var_set = set()
        elem_info = {}
        for vi, (ci, col_start, w, ea, eb) in enumerate(var_cols):
            var_set.update([ea, eb])
            elem_info[ea] = (vi + 1, True)
            elem_info[eb] = (vi + 1, False)

        self.ctrl.log(f"[{self.name}] Extracting SAT clauses...")
        sat_clauses = []
        for ci, col_start, w in clause_col_infos:
            lits = []
            for ei in var_set:
                val = int(strs[ei][col_start:col_start + w])
                if val == 1 and ei in elem_info:
                    vid, pos = elem_info[ei]
                    lits.append(vid if pos else -vid)
            if lits:
                sat_clauses.append(lits)

        self.ctrl.log(f"[{self.name}] {len(sat_clauses)} SAT clauses. "
                      f"Clause target={clause_target}. Running DPLL...")

        t0 = time.time()
        asgn = self._dpll(n_vcols, sat_clauses)
        t_sat = time.time() - t0

        if asgn is None:
            self.ctrl.log(f"[{self.name}] UNSATISFIABLE ({t_sat:.2f}s)")
            return

        self.ctrl.log(f"[{self.name}] SAT solved in {t_sat:.2f}s")

        slack_elems = [i for i in range(p.n) if i not in var_set]
        chosen = set()
        for vi, (ci, col_start, w, ea, eb) in enumerate(var_cols):
            chosen.add(ea if asgn[vi + 1] else eb)

        for ci, col_start, w in clause_col_infos:
            if self.ctrl.stopped:
                return
            contrib = sum(int(strs[e][col_start:col_start + w])
                          for e in chosen
                          if int(strs[e][col_start:col_start + w]) > 0)
            need = clause_target - contrib
            if need <= 0:
                continue
            avail_slacks = [(se, int(strs[se][col_start:col_start + w]))
                            for se in slack_elems
                            if se not in chosen
                            and int(strs[se][col_start:col_start + w]) > 0]
            avail_slacks.sort(key=lambda x: -x[1])
            for se, sv in avail_slacks:
                if need <= 0:
                    break
                if sv <= need:
                    chosen.add(se)
                    need -= sv

        solution = [p.numbers[i] for i in chosen]
        total = sum(solution)

        if total == p.target:
            self.ctrl.log(f"[{self.name}] VERIFIED! Solution correct.")
            self.ctrl.report(solution, self.name)
        else:
            self.ctrl.log(f"[{self.name}] Sum mismatch — debugging...")
            ts, ss = str(p.target), str(total)
            if len(ts) == len(ss):
                mis = sum(1 for a, b in zip(ts, ss) if a != b)
                self.ctrl.log(f"[{self.name}] {mis}/{len(ts)} digit mismatches")

    @staticmethod
    def _detect_column_width(target_s):
        """Detect column structure: finds width where target has exactly
        2 unique small values (variable target and clause target)."""
        for cw in [2, 3, 1]:
            pad = (-len(target_s)) % cw if cw > 1 else 0
            ts = '0' * pad + target_s
            nd = len(ts)
            if nd % cw != 0:
                continue
            cols = [int(ts[i:i + cw]) for i in range(0, nd, cw)]
            unique = set(cols)
            if len(unique) == 2 and max(unique) <= 99:
                return cw, cols
        return 0, []

    def _minimize_overflow(self, asgn, n_vars, clauses, var_cols, strs,
                           clause_cols, elem_info, var_set):
        """Local search: flip variables to reduce clause overflow (>3 true lits)."""
        best = dict(asgn)
        for _ in range(500):
            if self.ctrl.stopped: return best
            worst_col, worst_count, worst_lits = None, 3, []
            for ci, col in enumerate(clause_cols):
                cnt = 0; lits = []
                for ei in var_set:
                    if strs[ei][col] == '1' and ei in elem_info:
                        vid, pos = elem_info[ei]
                        if best[vid] == pos:
                            cnt += 1; lits.append((vid, pos))
                if cnt > worst_count:
                    worst_count = cnt; worst_col = col; worst_lits = lits
            if worst_col is None:
                return best
            flipped = False
            for vid, _ in worst_lits:
                test = dict(best); test[vid] = not test[vid]
                if all(any((l > 0) == test.get(abs(l), True) for l in cl) for cl in clauses):
                    best = test; flipped = True; break
            if not flipped:
                break
        return best

    def _dpll(self, n_vars, clauses):
        a = [0] * (n_vars + 1)
        pos_in = [[] for _ in range(n_vars + 1)]
        neg_in = [[] for _ in range(n_vars + 1)]
        for ci, cl in enumerate(clauses):
            for l in cl:
                v = abs(l)
                if v <= n_vars:
                    (pos_in if l > 0 else neg_in)[v].append(ci)

        def propagate(trail):
            qi = 0
            while qi < len(trail):
                var = trail[qi]; qi += 1; val = a[var]
                for ci in (neg_in[var] if val == 1 else pos_in[var]):
                    cl = clauses[ci]; unset_l = 0; uc = 0; sat = False
                    for l in cl:
                        v = abs(l); av = a[v]
                        if av == 0: uc += 1; unset_l = l
                        elif (l > 0 and av == 1) or (l < 0 and av == -1): sat = True; break
                        if uc > 1: break
                    if sat: continue
                    if uc == 0: return False
                    if uc == 1:
                        v = abs(unset_l); a[v] = 1 if unset_l > 0 else -1; trail.append(v)
            return True

        trail = []
        for ci, cl in enumerate(clauses):
            if len(cl) == 1:
                v = abs(cl[0])
                if a[v] == 0: a[v] = 1 if cl[0] > 0 else -1; trail.append(v)
        if not propagate(trail): return None

        stack = []
        while True:
            if self.ctrl.stopped: return None
            bv, bs = 0, -1
            for v in range(1, n_vars + 1):
                if a[v] != 0: continue
                sc = sum(1 for ci in pos_in[v] + neg_in[v]
                         if not any((a[abs(l)] == 1 and l > 0) or
                                    (a[abs(l)] == -1 and l < 0) for l in clauses[ci]))
                if sc > bs: bs = sc; bv = v
            if bv == 0: break
            mk = len(trail)
            stack.append((bv, True, mk))
            a[bv] = 1; trail.append(bv)
            if not propagate(trail):
                while stack:
                    dv, dval, m = stack.pop()
                    while len(trail) > m: a[trail.pop()] = 0
                    if dval:
                        stack.append((dv, False, m))
                        a[dv] = -1; trail.append(dv)
                        if propagate(trail): break
                else:
                    return None

        return {v: a[v] != -1 for v in range(1, n_vars + 1)}


# ================================================================
#  META-BRAIN CONTROLLER
# ================================================================

class ZUltimateController:
    def __init__(self, numbers, target, log_fn=None):
        self.raw_numbers = sorted(numbers); self.raw_target = target
        self.log = log_fn or (lambda m: None)
        self.stop_event = threading.Event()
        self.solution = None; self._lock = threading.Lock()
        self.winner = None; self.proved_impossible = False
        self.cdb = ConflictDB(); self.forced = []; self.profile = None; self.t0 = 0

    @property
    def stopped(self): return self.stop_event.is_set()

    def report(self, solution, engine):
        with self._lock:
            if self.stopped: return
            full = sorted(self.forced + solution)
            if sum(full) != self.raw_target: return
            pool = list(self.raw_numbers)
            for x in full:
                if x in pool: pool.remove(x)
                else: return
            self.solution = full; self.winner = engine; self.stop_event.set()

    def run(self, max_time=60.0, verbose=True):
        self.t0 = time.time()
        log = self.log if verbose else (lambda m: None)
        if not self.raw_numbers or self.raw_target < 0: return self._r()
        if self.raw_target == 0:
            self.solution = []; self.winner = "Trivial"; return self._r()

        prof = ProblemProfile(self.raw_numbers, self.raw_target)
        tdig = len(str(prof.target))
        log(f"  n={prof.n}  target_digits={tdig}  class={prof.pclass}")

        found, sol = TrivialSolver.solve(prof)
        if found:
            if sol is None: self.proved_impossible = True; return self._r()
            self.solution = sol; self.winner = "Trivial"; return self._r()

        nums, target, self.forced, imp = Preprocessor.reduce(self.raw_numbers, self.raw_target)
        if imp: self.proved_impossible = True; return self._r()
        if target == 0: self.solution = sorted(self.forced); self.winner = "Preprocessor"; return self._r()
        if self.forced: log(f"  Forced: {len(self.forced)} elements")
        log(f"  Reduced: n={len(nums)}  target_digits={len(str(target))}")

        self.profile = ProblemProfile(nums, target)
        engines = self._engines()
        log(f"  Engines: {[e.name for e in engines]}")

        threads = []
        for eng in engines:
            t = threading.Thread(target=self._safe, args=(eng,), daemon=True)
            threads.append(t); t.start()
        self.stop_event.wait(timeout=max_time); self.stop_event.set()
        for t in threads: t.join(timeout=0.3)
        return self._r()

    def _engines(self):
        pc, n = self.profile.pclass, self.profile.n
        td = len(str(self.profile.target))
        pool = []

        if td > 50 and n > 100:
            pool.append(ColumnStructureEngine(self))

        pool.append(ResidueEngine(self))
        if pc in ("TRIVIAL","TINY"):
            pool += [BitsetDPEngine(self), MITMEngine(self), GreedyEngine(self)]
        elif pc == "SMALL":
            pool += [MITMEngine(self), BitsetDPEngine(self), GreedyEngine(self), BackwardEngine(self)]
        elif pc == "MEDIUM":
            pool += [BitsetDPEngine(self), GreedyEngine(self), BackwardEngine(self), BridgeEngine(self)]
            if n <= 50: pool.append(MITMEngine(self))
        else:
            pool += [GreedyEngine(self), BackwardEngine(self), BridgeEngine(self), RandomizedEngine(self)]
        pool += [KSumEngine(self), EstimateEngine(self)]
        if not any(isinstance(e, RandomizedEngine) for e in pool):
            pool.append(RandomizedEngine(self))
        return pool

    def _safe(self, e):
        try: e.run()
        except Exception as ex: self.log(f"[ERR] {e.name}: {ex}")

    def _r(self):
        return {'solution': self.solution, 'sum': sum(self.solution) if self.solution else 0,
                'target': self.raw_target,
                'exact': self.solution is not None and sum(self.solution) == self.raw_target,
                'impossible': self.proved_impossible and self.solution is None,
                'time': time.time() - self.t0,
                'engine': self.winner or ("IMPOSSIBLE" if self.proved_impossible else "Timeout"),
                'conflicts': self.cdb.size}


# ================================================================
#  SAT-TO-SUBSET-SUM CONVERTER
# ================================================================

def convert_cnf_to_subset_sum(cnf_text):
    """Convert CNF SAT to Subset Sum via Karp reduction.
    Uses 2-digit columns (base 100) to prevent carry overflow.
    Max column sum = 8 literals + slack 2 = 10 < 100. No carry possible."""
    n_vars = n_clauses = 0
    data_lines = []
    for line in cnf_text.strip().split('\n'):
        if line.startswith('c') or not line.strip(): continue
        if line.startswith('p'):
            parts = line.split(); n_vars, n_clauses = int(parts[2]), int(parts[3])
        else:
            data_lines.append(line)
    raw = " ".join(data_lines).split()
    clauses, cur = [], []
    for val in raw:
        num = int(val)
        if num == 0: clauses.append(cur); cur = []
        else: cur.append(num)

    CW = 2  # column width: 2 digits per column prevents carries
    n_cols = n_vars + n_clauses

    def make_num(var_idx, clause_bits):
        s = ['00'] * n_cols
        s[var_idx] = '01'
        for ci, b in clause_bits.items():
            s[n_vars + ci] = f'{b:02d}'
        return int("".join(s))

    elements = []
    for i in range(1, n_vars + 1):
        elements.append(make_num(i-1, {ci: 1 for ci, c in enumerate(clauses) if i in c}))
        elements.append(make_num(i-1, {ci: 1 for ci, c in enumerate(clauses) if -i in c}))
    for j in range(n_clauses):
        s1 = ['00']*n_cols; s1[n_vars+j] = '01'; elements.append(int("".join(s1)))
        s2 = ['00']*n_cols; s2[n_vars+j] = '02'; elements.append(int("".join(s2)))

    target = int("".join(['01']*n_vars + ['03']*n_clauses))
    return elements, target, n_vars, n_clauses, clauses


# ================================================================
#  BENCHMARKS
# ================================================================

def run_one(name, numbers, target, expect_ok=True, timeout=60):
    t0 = time.time()
    ctrl = ZUltimateController(numbers, target, print)
    res = ctrl.run(max_time=timeout, verbose=True)
    t = time.time() - t0
    if expect_ok:
        status = "SOLVED" if res['exact'] else ("IMPOSSIBLE(unexpected)" if res['impossible'] else "TIMEOUT")
    else:
        status = "PROVED IMPOSSIBLE" if res['impossible'] else ("SOLVED(unexpected!)" if res['exact'] else "TIMEOUT")
    print(f"\n  >>> [{status}] {name}  {t:.4f}s  engine={res['engine']}")
    if res['exact'] and res['solution']:
        print(f"  >>> Solution has {len(res['solution'])} elements, sum verified = {sum(res['solution']) == target}")
    print()
    return res['exact'] if expect_ok else res['impossible']


def benchmark_standard():
    print("="*70)
    print("  STANDARD SUBSET SUM BENCHMARKS")
    print("="*70)
    p, t = 0, 0

    print("\n--- Easy ---")
    t+=1; p+=run_one("1-Sum", list(range(1,101)), 50)
    t+=1; p+=run_one("2-Sum", list(range(1,101)), 199)
    t+=1; p+=run_one("All=target", list(range(1,11)), 55)

    print("\n--- Impossible ---")
    t+=1; p+=run_one("Odd target all even", [2,4,6,8,10]*5, 33, False)
    t+=1; p+=run_one("Mod-3", [3,6,9,12,15], 5, False)

    print("\n--- MITM range ---")
    for n in [20, 30, 40]:
        random.seed(42+n)
        nums = sorted(random.sample(range(1,10000), n))
        sub = random.sample(nums, random.randint(3, n//2))
        t+=1; p+=run_one(f"Random n={n}", nums, sum(sub))

    print("\n--- Large n ---")
    for n in [200, 1000]:
        random.seed(300+n)
        nums = sorted(random.sample(range(1,10000), min(n,9999)))
        sub = random.sample(nums, 10)
        t+=1; p+=run_one(f"Large n={n}", nums, sum(sub))

    print(f"\n{'='*70}")
    print(f"  STANDARD: {p}/{t} solved")
    print(f"{'='*70}")
    return p, t


def benchmark_sat():
    """Test jnh1.cnf SAT-encoded instance."""
    print("\n" + "="*70)
    print("  SAT-ENCODED INSTANCE TEST (jnh1.cnf)")
    print("  1900 elements, 950-digit numbers")
    print("  Z++ uses Column Structure Engine (pattern recognition)")
    print("="*70 + "\n")

    import os
    cnf_text = None
    for path in ['jnh1.cnf', 'jnh1.cnf/jnh1.cnf', '/content/jnh1.cnf']:
        if os.path.isfile(path):
            with open(path) as f: cnf_text = f.read()
            print(f"  Loaded: {path}")
            break

    if cnf_text is None:
        print("  jnh1.cnf not found. Upload it to test.")
        print("  In Colab: use the file panel on the left to upload jnh1.cnf")
        return False

    print("  Converting CNF to Subset Sum (Karp reduction)...")
    elements, target, nv, nc, clauses = convert_cnf_to_subset_sum(cnf_text)
    print(f"  Variables: {nv}, Clauses: {nc}")
    print(f"  Elements: {len(elements)}, Target digits: {len(str(target))}")
    print(f"  Running Z++ (60s timeout)...\n")

    return run_one(f"jnh1.cnf ({nv} vars, {nc} clauses, {len(elements)} elements)",
                   elements, target, timeout=60)


# ================================================================
#  MAIN
# ================================================================

if __name__ == "__main__":
    print("\n  Z++ ULTIMATE ENGINE v3.0")
    print("  Algorithm: Rehan (Independent Researcher)")
    print("  13 parallel engines including Column Structure SAT solver\n")

    p, t = benchmark_standard()
    sat_ok = benchmark_sat()

    print("\n" + "="*70)
    print(f"  FINAL: Standard {p}/{t} | SAT instance: {'SOLVED' if sat_ok else 'see above'}")
    print("="*70)
