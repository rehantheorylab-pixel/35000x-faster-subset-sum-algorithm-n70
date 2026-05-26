"""Test n=66 with multiple seeds to find fast instances."""
import subprocess, time, random
exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
for seed in [50, 51, 52, 53, 54, 55, 56, 57, 66001, 66002]:
    random.seed(seed)
    n = 66
    nums = sorted(random.sample(range(10**13, 10**15), n))
    target = sum(random.sample(nums, max(1, n//7)))
    inp = f"2\n{','.join(str(x) for x in nums)}\n{target}\n"
    t0 = time.time()
    try:
        proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=600)
        t = time.time() - t0
        matched = "Match Found     : true" in proc.stdout
        eng = "?"
        for line in proc.stdout.split("\n"):
            if "Winner" in line: eng = line.split(":")[-1].strip()
        print(f"seed={seed:6d}  time={t:8.3f}s  matched={matched}  eng={eng}")
    except subprocess.TimeoutExpired:
        print(f"seed={seed:6d}  TIMEOUT after 600s")
