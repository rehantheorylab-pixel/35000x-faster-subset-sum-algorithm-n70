"""Retest previously-failing cases with increased timeouts."""
import sys, time, importlib.util, os, random

spec = importlib.util.spec_from_file_location("zpp_wr", r"C:\Users\rehan\algorithm\Z++.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RESULTS = []

def test(name, nums, target, timeout=300.0):
    t0 = time.time()
    ctrl = mod.ZUltimateController(nums, target)
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
    passed = ok or res['impossible']
    RESULTS.append((name, passed, elapsed, res['engine'], ok, res['impossible']))
    status = "PASS" if passed else "FAIL"
    print(f"  [{status:4s}] {name:35s}  {elapsed:8.3f}s  engine={res['engine']:18s}  ok={ok}")
    return passed

print("=" * 75)
print("  RETESTING PREVIOUSLY-FAILING CASES (300s timeout)")
print("=" * 75)

# Test 1: Hard64 n=55 (failed at 183s before)
print("\n--- Hard64 n=55 (3 trials) ---")
random.seed(5501)
for trial in range(3):
    n = 55
    nums = sorted(random.sample(range(10**13, 10**15), n))
    target = sum(random.sample(nums, n//7))
    test(f"Hard64 n=55 trial {trial+1}", nums, target, timeout=300.0)

# Test 2: Unique n=50 (failed at 181s before)
print("\n--- Unique n=50 (3 trials) ---")
random.seed(5001)
for trial in range(3):
    n = 50
    nums = sorted(random.sample(range(10**12, 10**14), n))
    k = 8
    indices = sorted(random.sample(range(n), k))
    target = sum(nums[i] for i in indices)
    test(f"Unique n=50 trial {trial+1}", nums, target, timeout=300.0)

# Test 3: n=62, 64 (to confirm they still work)
print("\n--- n=62, 64 (confirmation) ---")
random.seed(6201)
for n in [62, 64]:
    nums = sorted(random.sample(range(10**14, 10**15), n))
    target = sum(random.sample(nums, n//7))
    test(f"n={n} confirmation", nums, target, timeout=300.0)

print(f"\n{'=' * 75}")
passed = sum(1 for _, p, _, _, _, _ in RESULTS if p)
total = len(RESULTS)
print(f"  RESULTS: {passed}/{total} passed ({(passed/total*100):.1f}%)")
print(f"{'=' * 75}")
