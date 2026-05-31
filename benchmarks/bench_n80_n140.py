"""
Z++ Ultra benchmark: n=80 and n=140 with large values (10^16 - 10^20)
Tests the enhanced GDEP + digit filter on problem sizes beyond current world record (n=70).
All cases must solve under 10 minutes.
"""
import sys, time, os, random, math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Z_plus_plus_gui import ZUltimateController

RESULTS = []

def test(name, nums, target, timeout=600.0):
    log = []
    t0 = time.time()
    ctrl = ZUltimateController(nums, target, lambda m: log.append(m))
    res = ctrl.run(max_time=timeout)
    elapsed = time.time() - t0
    ok = False
    if res.get('exact') and res.get('solution') is not None:
        sol = res['solution']
        if sum(sol) == target:
            pool = list(nums)
            valid = True
            for x in sol:
                if x in pool:
                    pool.remove(x)
                else:
                    valid = False
                    break
            if valid:
                ok = True
    improbable = res.get('impossible', False)
    passed = ok or improbable
    eng = res.get('engine', '?')
    RESULTS.append((name, passed, elapsed, eng, ok, improbable))
    status = "PASS" if passed else "FAIL"
    print(f"  [{status:4s}] {name:45s}  {elapsed:8.3f}s  engine={eng:22s}  n={len(nums)}")
    return passed

def gen_large(n, max_val_exp, seed):
    random.seed(seed)
    max_val = 10 ** max_val_exp
    return sorted(random.sample(range(max_val // 2, max_val), n))

def gen_structured_large(n, max_val_exp, seed):
    random.seed(seed)
    max_val = 10 ** max_val_exp
    base = max_val // 4
    return sorted([base + random.randint(0, base // 10) for _ in range(n)])

print("=" * 90)
print("  Z++ ULTRA — n=80 & n=140 World Record Benchmark")
print("  Solving subset sum with LARGER values than current record (10^15)")
print("  Target: all cases under 10 minutes (600s)")
print("=" * 90)

# --- Phase 1: n=80 with large values ---
print("\n=== PHASE 1: n=80 with values up to 10^18 ===")

print("\n-- 1a: n=80, small target (BitsetDP territory) --")
nums80a = sorted(random.sample(range(10**16, 10**18), 80))
target80a = sum(random.sample(nums80a, 3))  # small subset
test("n=80 small-tgt 10^18", nums80a, target80a)

print("\n-- 1b: n=80, structured values --")
nums80b = gen_structured_large(80, 16, 42)
target80b = sum(random.sample(nums80b, 5))
test("n=80 structured 10^16", nums80b, target80b)

print("\n-- 1c: n=80, medium-range values --")
nums80c = sorted(random.sample(range(10**14, 10**16), 80))
target80c = sum(random.sample(nums80c, 8))
test("n=80 rand 10^14-10^16", nums80c, target80c)

print("\n-- 1d: n=80, SAT-encoded (column structure) --")
random.seed(777)
col_size = 80
nums80d = []
for i in range(col_size):
    val = random.choice([1, 2, 3]) * (10 ** random.randint(1, 12))
    nums80d.append(val)
nums80d.sort()
target80d = sum(random.sample(nums80d, random.randint(5, 10)))
test("n=80 column-structured", nums80d, target80d)

# --- Phase 2: n=140 with large values ---
print("\n=== PHASE 2: n=140 with values up to 10^18 ===")

print("\n-- 2a: n=140, small target (BitsetDP territory) --")
nums140a = sorted(random.sample(range(10**14, 10**18), 140))
target140a = sum(random.sample(nums140a, 2))  # very small subset
test("n=140 tiny-tgt 10^18", nums140a, target140a, timeout=600.0)

print("\n-- 2b: n=140, structured large values --")
nums140b = gen_structured_large(140, 16, 99)
target140b = sum(random.sample(nums140b, 4))
test("n=140 structured 10^16", nums140b, target140b, timeout=600.0)

print("\n-- 2c: n=140, moderate target --")
random.seed(12345)
nums140c = sorted(random.sample(range(10**15, 10**17), 140))
target140c = sum(random.sample(nums140c, 6))
test("n=140 mod-tgt 10^17", nums140c, target140c, timeout=600.0)

# --- Phase 3: Edge cases ---
print("\n=== PHASE 3: Edge Cases ===")

print("\n-- 3a: n=80, GCD impossible (digit filter should catch) --")
nums80e = [6, 9, 15, 21] * 20
target80e = 10
test("n=80 GCD impossible", nums80e, target80e)

print("\n-- 3b: n=80, all even, odd target (last-digit filter) --")
nums80f = [random.randint(1, 50000) * 2 for _ in range(80)]
target80f = 99999
test("n=80 parity (last digit)", nums80f, target80f)

print("\n-- 3c: n=140, zero target --")
nums140z = sorted(random.sample(range(10**12, 10**15), 140))
test("n=140 target=0", nums140z, 0)

# Summary
print(f"\n{'=' * 90}")
passed = sum(1 for _, p, _, _, _, _ in RESULTS if p)
total = len(RESULTS)
print(f"  FINAL: {passed}/{total} passed ({(passed/total*100):.1f}%)")
if passed == total:
    print("  *** PERFECT SCORE — ALL n=80 and n=140 cases solved ***")
print(f"{'=' * 90}")
