"""
n=72 subset sum — world record test with fail-fast.
Threshold: 3600s (our n=70 took 566s, n=72 has ~2x work).
If exceeded, kill and report FAIL for optimization.
"""
import subprocess, time, random, sys

EXE = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
WR_THRESHOLD = 3600  # World record threshold in seconds

random.seed(72001)
n = 72
nums = sorted(random.sample(range(10**14, 10**15), n))
k = n // 7
target = sum(random.sample(nums, k))
inp = f"2\n{','.join(str(x) for x in nums)}\n{target}\n"

print(f"n={n} target={target} threshold={WR_THRESHOLD}s", flush=True)
t0 = time.time()
try:
    proc = subprocess.run([EXE], input=inp, capture_output=True, text=True, timeout=WR_THRESHOLD)
    t = time.time() - t0
    matched = "Match Found     : true" in proc.stdout
    if matched:
        for line in proc.stdout.split("\n"):
            if any(x in line for x in ["Winner", "Solution", "Match Found"]):
                print(line.strip(), flush=True)
        print(f"PASS: n={n} solved in {t:.1f}s (threshold {WR_THRESHOLD}s)", flush=True)
    else:
        print(f"FAIL: n={n} no solution found in {t:.1f}s (threshold {WR_THRESHOLD}s)", flush=True)
except subprocess.TimeoutExpired:
    t = time.time() - t0
    print(f"WORLD RECORD FAIL: n={n} exceeded threshold {WR_THRESHOLD}s (ran for {t:.1f}s)", flush=True)
    print("Need to optimize Hard-U128 for n>=72", flush=True)
