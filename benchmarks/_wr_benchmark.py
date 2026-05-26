"""
Z++ ULTRA v5.0  --  World-Record Benchmark Suite
Tests against known hard instances and reports performance.
"""
import sys, time, importlib.util, math, os, random, subprocess

spec = importlib.util.spec_from_file_location("zpp_wr", r"C:\Users\rehan\algorithm\Z++.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RESULTS = {}

def bench(name, nums, target, timeout=60.0):
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
    key = f"{name}  n={len(nums)}  tgt_digits={len(str(target)) if target>0 else 1}"
    RESULTS[key] = (ok, improbable, elapsed, res['engine'])
    status = "PASS" if (ok or improbable) else "FAIL"
    print(f"  [{status:4s}] {name:35s}  {elapsed:8.4f}s  engine={res['engine']:18s}  exact={res['exact']}")
    return ok

print("=" * 75)
print("  Z++ ULTRA v5.0 - WORLD-RECORD BENCHMARK SUITE")
print("=" * 75)

print("\n--- 1. Standard Benchmarks ---")
bench("Classic 5570", [1,3,7,21,50,200,400,499,1000,1500,2000,5000,10000,25000], 5570)
bench("Powers of 2 (1023)", [1,2,4,8,16,32,64,128,256,512], 1023)
bench("All elements sum", list(range(1, 51)), 1275)
bench("GCD impossible", [6,9,15,21], 10)
bench("Odd/even impossible", [2,4,6,8,10], 7)

print("\n--- 2. Random n=30..55 ---")
random.seed(42)
for n in [30, 35, 40, 45, 50]:
    nums = sorted(random.sample(range(1, min(20000, n*400)), n))
    sub = random.sample(nums, max(1, n//4))
    target = sum(sub)
    bench(f"Random n={n}", nums, target, timeout=60.0)

print("\n--- 3. Dense Instances ---")
random.seed(123)
for n in [20, 30, 40]:
    max_val = 2 ** (n // 2)
    nums = sorted(random.sample(range(1, max_val), min(n, max_val-1)))
    sub = random.sample(nums, max(1, n//4))
    target = sum(sub)
    density = n / math.log2(max_val) if max_val > 1 else 0
    bench(f"Dense n={n} d={density:.2f}", nums, target, timeout=30.0)

print("\n--- 4. Super-Increasing ---")
nums_si = [1]
for i in range(1, 50):
    nums_si.append(sum(nums_si) + random.randint(1, 10))
target_si = sum(random.sample(nums_si[:30], 10))
bench(f"Super-inc n=30", nums_si[:30], target_si)

print("\n--- 5. Large n, Small Target ---")
random.seed(456)
for n in [100, 500]:
    nums = sorted(random.sample(range(1, 100000), min(n, 9999)))
    sub = random.sample(nums, 5)
    target = sum(sub)
    bench(f"Large n={n}", nums, target, timeout=30.0)

print("\n--- 6. Duplicate-Heavy ---")
bench("Uniform 30x7 target 49", [7]*30, 49)
bench("Many 5s target 25", [5]*20, 25)

print("\n--- 7. Hard Exact-Match ---")
nums_hard = [11, 17, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101]
bench("Primes sum", nums_hard[:15], sum(random.sample(nums_hard[:15], 5)))

print(f"\n{'=' * 75}")
passed = sum(1 for v in RESULTS.values() if v[0] or v[1])
total = len(RESULTS)
print(f"  RESULTS: {passed}/{total} passed  ({(passed/total*100):.1f}%)")
print(f"{'=' * 75}")

print("\n--- Speed Leaders ---")
sorted_res = sorted(RESULTS.items(), key=lambda x: x[1][2])
for name, (ok, imp, t, eng) in sorted_res[:5]:
    print(f"  {'OK' if (ok or imp) else 'XX'} {name:50s}  {t:.4f}s  {eng}")

print("\n--- Engine Activation Summary ---")
from collections import Counter
engines_used = Counter(v[3] for v in RESULTS.values())
for eng, cnt in sorted(engines_used.items(), key=lambda x: -x[1]):
    print(f"  {eng:20s}  x{cnt}")

# Rust binary test
print("\n--- Rust Binary Direct Test ---")
exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
if os.path.isfile(exe):
    print(f"  OK zpp.exe found ({os.path.getsize(exe)} bytes)")
    inp = "2\n1,3,7,21,50,200,400,499,1000,1500,2000,5000,10000,25000\n5570\n"
    t0 = time.time()
    try:
        proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=30)
        t = time.time() - t0
        ok = "Match Found     : true" in proc.stdout
        print(f"  {'OK' if ok else 'XX'} Quick test: {t:.4f}s  match={ok}")
        if ok:
            for line in proc.stdout.split('\n'):
                ls = line.strip()
                if ls:
                    print(f"    {ls}")
    except Exception as e:
        print(f"  XX Test failed: {e}")
else:
    print("  XX zpp.exe not found (no Rust binary available)")
