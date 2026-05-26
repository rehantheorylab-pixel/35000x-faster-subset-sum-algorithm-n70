"""Test Rust binary scaling from n=50 to n=66."""
import subprocess, time, os, random, sys

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
if not os.path.isfile(exe):
    print("No zpp.exe found")
    sys.exit(1)

random.seed(999999)

for n in [50, 52, 54, 56, 58, 60, 62]:
    max_val = 10**15
    nums = sorted(random.sample(range(10**14, 10**15), min(n, 10**5)))
    if len(nums) < n:
        nums = sorted(random.sample(range(1, 10**15), n))
    k = max(1, n // 6)
    indices = sorted(random.sample(range(len(nums)), k))
    target = sum(nums[i] for i in indices)
    inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"
    
    t0 = time.time()
    proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=300)
    t = time.time() - t0
    
    matched = "Match Found     : true" in proc.stdout
    if matched:
        eng_line = [l for l in proc.stdout.split('\n') if 'Winner' in l]
        eng = eng_line[0].strip() if eng_line else "?"
        print(f"  n={n:2d}: OK  {t:8.3f}s  Engine: {eng}")
    elif "TIMEOUT" in proc.stdout or t >= 298:
        print(f"  n={n:2d}: TIMEOUT  (300s)")
    else:
        print(f"  n={n:2d}: FAIL {t:8.3f}s")
