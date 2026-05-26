"""Test n=68 subset sum world record."""
import subprocess, time, random
exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
random.seed(68001)
n = 68
nums = sorted(random.sample(range(10**14, 10**15), n))
k = n // 7
target = sum(random.sample(nums, k))
inp = f"2\n{','.join(str(x) for x in nums)}\n{target}\n"
print(f"n={n} target={target} (digits={len(str(target))})", flush=True)
t0 = time.time()
proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=7200)
t = time.time() - t0
matched = "Match Found     : true" in proc.stdout
print(f"time={t:.3f}s matched={matched}")
for line in proc.stdout.split("\n"):
    if any(x in line for x in ["Winner", "Solution", "Match Found", "Elapsed"]):
        print(line.strip())
