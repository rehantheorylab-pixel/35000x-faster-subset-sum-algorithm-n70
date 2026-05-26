"""Test n=66 with fixed Rust binary."""
import subprocess, time, os, random

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
random.seed(66001)
n = 66
timeout = 600
nums = sorted(random.sample(range(10**14, 10**15), n))
k = n // 7
target = sum(random.sample(nums, k))
inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"
print(f"n={n} target={target} (digits={len(str(target))}) timeout={timeout}s")
t0 = time.time()
try:
    proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=timeout)
    t = time.time() - t0
    matched = "Match Found     : true" in proc.stdout
    print(f"time={t:.3f}s matched={matched}")
    if matched:
        eng = [l for l in proc.stdout.split('\n') if 'Winner' in l]
        sol_line = [l for l in proc.stdout.split('\n') if 'Solution' in l and 'Size' not in l]
        print(f"engine={eng[0].strip() if eng else '?'}")
        if sol_line:
            print(f"soln={sol_line[0].strip()}")
    else:
        winner = [l for l in proc.stdout.split('\n') if 'Winner' in l]
        print(f"winner={winner[0].strip() if winner else '?'}")
except subprocess.TimeoutExpired:
    print(f"TIMEOUT after {(time.time() - t0):.1f}s")
except Exception as e:
    print(f"ERROR: {e}")
