"""Retest one failing case at a time."""
import sys, time, importlib.util, os, random

spec = importlib.util.spec_from_file_location("zpp_wr", r"C:\Users\rehan\algorithm\Z++.py")
if not spec or not spec.loader:
    print("FAIL: could not load Z++.py")
    sys.exit(1)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_once(name, nums, target, timeout=300.0):
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
    print(f"  time={elapsed:.2f}s  passed={passed}  engine={res['engine']}  ok={ok}")
    return passed

print("Test 1: Hard64 n=55 (1 trial, 300s)")
random.seed(5501)
n = 55
nums = sorted(random.sample(range(10**13, 10**15), n))
target = sum(random.sample(nums, n//7))
print(f"  n={n} target digits={len(str(target))}")
test_once("n=55", nums, target, 300.0)

print("\nTest 2: Unique n=50 (1 trial, 300s)")
random.seed(5001)
n = 50
nums = sorted(random.sample(range(10**12, 10**14), n))
indices = sorted(random.sample(range(n), 8))
target = sum(nums[i] for i in indices)
print(f"  n={n} target digits={len(str(target))}")
test_once("n=50", nums, target, 300.0)

print("\nDone.")
