"""Test n=70 with 16 threads."""
import subprocess, time, random
exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
random.seed(70001)
n = 70
nums = sorted(random.sample(range(10**14, 10**15), n))
k = n // 7
target = sum(random.sample(nums, k))
csv = ",".join(str(x) for x in nums)
inp = f"2\n{csv}\n{target}\n"
t0 = time.time()
proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=600)
t = time.time() - t0
ok = "Match Found     : true" in proc.stdout
w = [l for l in proc.stdout.split("\n") if "Winner" in l]
print(f"n={n} time={t:.3f}s ok={ok}")
if w:
    print(f"  {w[0].strip()}")
