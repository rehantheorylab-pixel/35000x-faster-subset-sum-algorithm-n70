"""Test the exact n=55 instance that failed in the comprehensive test."""
import subprocess, time, os, random, sys, importlib.util

# Reproduce exact instance from wr_final_v2.py seed=50, 4th call
random.seed(50)
for _ in range(3):
    n = [40,45,50][_]
    nums = sorted(random.sample(range(10**13, 10**15), n))
    target = sum(random.sample(nums, max(1, n//7)))
# 4th: n=55
nums = sorted(random.sample(range(10**13, 10**15), 55))
target = sum(random.sample(nums, max(1, 55//7)))
print(f"n=55 target={target} digits={len(str(target))}")

# Rust direct
exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"
t0 = time.time()
proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=600)
t = time.time() - t0
matched = "Match Found     : true" in proc.stdout
eng = [l for l in proc.stdout.split('\n') if 'Winner' in l]
print(f"Rust direct: time={t:.2f}s matched={matched} eng={eng[0].strip() if eng else '?'}")

# Z++ system
spec = importlib.util.spec_from_file_location("zpp_wr", r"C:\Users\rehan\algorithm\Z++.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
t0 = time.time()
ctrl = mod.ZUltimateController(nums, target)
res = ctrl.run(max_time=600.0)
t = time.time() - t0
print(f"Z++ system: time={t:.2f}s engine={res['engine']} exact={res['exact']}")
if res['solution']:
    print(f"  solution sum={sum(res['solution'])} target={target} valid={sum(res['solution'])==target}")
