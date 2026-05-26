"""Check if Rust binary works directly for n=60 seed 6001."""
import subprocess, time, os, random

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
random.seed(6001)
nums = sorted(random.sample(range(10**14, 10**15), 60))
target = sum(random.sample(nums, 10))
inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"
print(f"n=60 target digits={len(str(target))}")
t0 = time.time()
proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=120)
t = time.time() - t0
matched = "Match Found     : true" in proc.stdout
eng = [l for l in proc.stdout.split('\n') if 'Winner' in l]
print(f"time={t:.2f}s matched={matched} eng={eng[0].strip() if eng else '?'}")

random.seed(6401)
nums = sorted(random.sample(range(10**14, 10**15), 64))
target = sum(random.sample(nums, 10))
inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"
print(f"n=64 target digits={len(str(target))}")
t0 = time.time()
proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=120)
t = time.time() - t0
matched = "Match Found     : true" in proc.stdout
eng = [l for l in proc.stdout.split('\n') if 'Winner' in l]
print(f"time={t:.2f}s matched={matched} eng={eng[0].strip() if eng else '?'}")
