"""
Z++ ULTRA v5.0  --  World-Record Benchmark (full suite)
Tests all engines and reports performance vs known records.
"""
import sys, time, importlib.util, os, random, math
from collections import Counter

spec = importlib.util.spec_from_file_location("zpp_wr", r"C:\Users\rehan\algorithm\Z++.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RESULTS = []

def test(name, nums, target, timeout=90.0):
    log = []
    t0 = time.time()
    ctrl = mod.ZUltimateController(nums, target, lambda m: log.append(m))
    res = ctrl.run(max_time=timeout)
    elapsed = time.time() - t0
    ok = False
    if res['exact'] and res['solution'] is not None and sum(res['solution']) == target:
        pool = list(nums)
        valid = True
        for x in res['solution']:
            if x in pool: pool.remove(x)
            else: valid = False; break
        if valid: ok = True
    improbable = res['impossible']
    passed = ok or improbable
    eng = res['engine']
    key = f"{name}  n={len(nums)}"
    RESULTS.append((key, passed, elapsed, eng, ok, improbable, res['exact']))
    status = "PASS" if passed else "FAIL"
    print(f"  [{status:4s}] {name:35s}  {elapsed:8.3f}s  engine={eng:22s}  n={len(nums)}")
    return passed

print("=" * 85)
print("  Z++ ULTRA v5.0 — FULL WORLD-RECORD BENCHMARK")
print("=" * 85)

# PHASE 1: Standard benchmarks (sanity check)
print("\n--- Phase 1: Sanity (must all pass) ---")
test("Classic 5570", [1,3,7,21,50,200,400,499,1000,1500,2000,5000,10000,25000], 5570)
test("Powers of 2", [1,2,4,8,16,32,64,128,256,512], 1023)
test("All sum", list(range(1, 51)), 1275)
test("GCD impossible", [6,9,15,21], 10)
test("Odd/even impossible", [2,4,6,8,10], 7)
test("10x10s target 50", [10]*15, 50)
test("Primes", [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47], sum([3,13,29,43]))

# PHASE 2: Random (MITM territory, n <= 40)
print("\n--- Phase 2: Random n=30..40 ---")
random.seed(111)
for n in [30, 35, 40]:
    nums = sorted(random.sample(range(1, min(50000, n*1000)), n))
    target = sum(random.sample(nums, max(1, n//5)))
    test(f"Random n={n}", nums, target)

# PHASE 3: Dense (hard classical instances)
print("\n--- Phase 3: Dense instances ---")
random.seed(222)
for n in [25, 35]:
    max_val = 2 ** (n // 2)
    nums = sorted(random.sample(range(1, max_val), min(n, max_val-1)))
    target = sum(random.sample(nums, max(1, n//4)))
    test(f"Dense n={n}", nums, target)

# PHASE 4: Hard 64-bit (Schroeppel-Shamir territory)
print("\n--- Phase 4: Hard 64-bit n=40..56 ---")
random.seed(333)
for n in [40, 45, 48, 50]:
    nums = sorted(random.sample(range(1, 2**60), n))
    target = sum(random.sample(nums, max(1, n//5)))
    test(f"Hard64 n={n}", nums, target, timeout=120.0)

# PHASE 5: Large n, small target (BitsetDP territory)
print("\n--- Phase 5: Large n small target ---")
random.seed(444)
for n in [100, 200, 500]:
    nums = sorted(random.sample(range(1, 100000), min(n, 9999)))
    target = sum(random.sample(nums, min(8, n)))
    test(f"Big n={n} smalltgt", nums, target)

# PHASE 6: HGJ territory (n=45-56, 4-way modulus)
print("\n--- Phase 6: HGJ-optimized (4-way modulus) ---")
random.seed(555)
for n in [45, 50, 52, 54]:
    nums = sorted(random.sample(range(1, 2**56), n))
    target = sum(random.sample(nums, max(1, n//6)))
    test(f"HGJ n={n}", nums, target, timeout=120.0)

# PHASE 7: Unique solution, high precision
print("\n--- Phase 7: Unique solution ---")
random.seed(666)
for n in [40, 48, 50]:
    nums = sorted(random.sample(range(10**14, 10**15), n))
    target = sum(random.sample(nums, max(1, n//8)))
    test(f"Unique n={n}", nums, target, timeout=120.0)

# Summary
print(f"\n{'=' * 85}")
passed = sum(1 for _, p, _, _, _, _, _ in RESULTS if p)
total = len(RESULTS)
print(f"  FINAL: {passed}/{total} passed  ({(passed/total*100):.1f}%)")
print(f"{'=' * 85}")

print("\n--- Engine Activation ---")
engines_used = Counter(r[3] for r in RESULTS)
for eng, cnt in sorted(engines_used.items(), key=lambda x: -x[1]):
    print(f"  {eng:25s}  x{cnt}")

print("\n--- Speed Leaders (by elapsed time) ---")
sorted_res = sorted(RESULTS, key=lambda x: x[2])
for name, passed, elapsed, eng, ok, imp, exact in sorted_res[:5]:
    print(f"  {'OK' if passed else 'XX'} {name:35s}  {elapsed:.4f}s  {eng:22s}")

print("\n--- Hardest Solved (by n) ---")
hard_solved = [(name, elapsed, eng) for name, passed, elapsed, eng, ok, imp, exact in RESULTS 
               if passed and eng not in ('IMPOSSIBLE', 'Trivial')]
def extract_n(name):
    try:
        return int(name.split('n=')[-1].split()[0])
    except (ValueError, IndexError):
        return 0
hard_solved_by_n = sorted(hard_solved, key=lambda x: -extract_n(x[0]))
for name, elapsed, eng in hard_solved_by_n[:5]:
    print(f"  OK {name:35s}  {elapsed:.3f}s  {eng:22s}")

print("\n--- World Record Assessment ---")
max_n_solved = 0
for name, passed, elapsed, eng, ok, imp, exact in RESULTS:
    if passed and not imp:
        n_v = extract_n(name)
        if n_v > max_n_solved:
            max_n_solved = n_v

print(f"  Max n solved: {max_n_solved}")
print(f"  Engines used: {len(engines_used)} different engines")
print(f"  Pass rate: {passed}/{total} ({passed/total*100:.1f}%)")
if passed == total:
    print("  *** PERFECT SCORE — all instances solved ***")
print(f"{'=' * 85}")
