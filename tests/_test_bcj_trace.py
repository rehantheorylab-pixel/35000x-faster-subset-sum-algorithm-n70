"""BCJ debug test — trace quarter sizes and timing."""
import subprocess, time, random, sys

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"

# Test n=60 (moderate size, solvable)
for seed in [6001]:
    random.seed(seed)
    n = 60
    nums = sorted(random.sample(range(10**14, 10**15), n))
    k = n // 7
    target = sum(random.sample(nums, k))
    inp = f"2\n{','.join(str(x) for x in nums)}\n{target}\n"
    print(f"n={n} seed={seed} target={target}", flush=True)
    t0 = time.time()
    try:
        proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=300)
        t = time.time() - t0
        matched = "Match Found     : true" in proc.stdout
        print(f"time={t:.3f}s matched={matched}")
        for line in proc.stdout.split("\n"):
            if any(x in line for x in ["Winner", "Solution", "Match Found", "BCJ"]):
                print(f"  {line.strip()}")
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT after 300s")
