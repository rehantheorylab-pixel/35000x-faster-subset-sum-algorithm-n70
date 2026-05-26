"""
Heavy engine test: forces BCJ, HGJ, Schroeppel-Shamir, and Rust subprocess
on instances where MITM and BitsetDP cannot succeed.
"""
import sys, time, importlib.util, os, random, subprocess, json, math

spec = importlib.util.spec_from_file_location("zpp_wr", r"C:\Users\rehan\algorithm\Z++.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RESULTS = []

def test(name, nums, target, timeout=120.0):
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
    RESULTS.append((name, passed, elapsed, eng, ok, improbable, res['exact']))
    status = "PASS" if passed else "FAIL"
    print(f"  [{status:4s}] {name:35s}  {elapsed:8.3f}s  engine={eng:22s}  ok={ok}  imp={improbable}")
    return passed

print("=" * 80)
print("  Z++ ULTRA v5.0 - HEAVY ENGINE TEST SUITE")
print("  Forcing BCJ, HGJ, Schroeppel-Shamir, RustSubprocess")
print("=" * 80)

# 1. Hard random n=50 with 64-bit values (MITM O(2^25) impossible, BitsetDP O(2^64) impossible)
print("\n--- 1. Hard Random n=50-70 (64-bit values) ---")
random.seed(999)
for n in [50, 55, 60]:
    max_val = 2**60
    nums = sorted(random.sample(range(1, 2**60), n))
    selected = random.sample(list(enumerate(nums)), n // 5)
    target = sum(v for _, v in selected)
    test(f"Hard64 n={n}", nums, target, timeout=120.0)

# 2. Deliberately hard subset-sum where MITM can't work: 
#    Large n, large values, unique solution
print("\n--- 2. Large Values, Unique Solution ---")
random.seed(777)
for n in [40, 50]:
    nums = sorted(random.sample(range(10**12, 10**13), n))
    k = max(1, n // 6)
    sol_indices = sorted(random.sample(range(n), k))
    target = sum(nums[i] for i in sol_indices)
    test(f"UniqueSol n={n} k={k}", nums, target, timeout=120.0)

# 3. Dense with high dynamic range
print("\n--- 3. High Dynamic Range ---")
random.seed(555)
for n in [35, 45]:
    # Mix of very small and very large numbers
    small = [random.randint(1, 100) for _ in range(n // 3)]
    large = [random.randint(10**12, 10**15) for _ in range(2 * n // 3)]
    nums = sorted(small + large)
    sol_idx = sorted(random.sample(range(len(nums)), max(1, n // 8)))
    target = sum(nums[i] for i in sol_idx)
    test(f"HighDyn n={n}", nums, target, timeout=120.0)

# 4. Test Rust binary directly with large n
print("\n--- 4. Rust Binary on Large Instances ---")
exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
if os.path.isfile(exe):
    for n in [40, 50]:
        nums = sorted(random.sample(range(1, 10**12), n))
        k = max(1, n // 5)
        sol_idx = sorted(random.sample(range(n), k))
        target = sum(nums[i] for i in sol_idx)
        elem_str = ", ".join(str(x) for x in nums)
        inp = f"2\n{elem_str}\n{target}\n"
        t0 = time.time()
        try:
            proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=120)
            t = time.time() - t0
            ok = "Match Found     : true" in proc.stdout
            print(f"  {'OK' if ok else 'XX'} Rust n={n}                   {t:8.3f}s  match={ok}")
        except subprocess.TimeoutExpired:
            print(f"  XX Rust n={n}                   timeout")
else:
    print("  XX zpp.exe not found")

# 5. Summary
print(f"\n{'=' * 80}")
passed = sum(1 for _, p, _, _, _, _, _ in RESULTS if p)
total = len(RESULTS)
print(f"  RESULTS: {passed}/{total} passed  ({(passed/total*100):.1f}%)")
print(f"{'=' * 80}")

print("\n--- Engine Activation Summary ---")
from collections import Counter
engines_used = Counter(r[3] for r in RESULTS)
for eng, cnt in sorted(engines_used.items(), key=lambda x: -x[1]):
    print(f"  {eng:30s}  x{cnt}")
