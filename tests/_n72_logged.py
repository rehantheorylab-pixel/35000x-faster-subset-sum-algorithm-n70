"""Test n=72 subset sum world record - file logging."""
import subprocess, time, random, sys

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
outfile = r"C:\Users\rehan\algorithm\_n72_result.txt"

random.seed(72001)
n = 72
nums = sorted(random.sample(range(10**14, 10**15), n))
k = n // 7
target = sum(random.sample(nums, k))
inp = f"2\n{','.join(str(x) for x in nums)}\n{target}\n"

with open(outfile, "w") as f:
    f.write(f"n={n} target={target} (digits={len(str(target))})\n")

print(f"n={n} target={target} (digits={len(str(target))})", flush=True)
t0 = time.time()
try:
    proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=7200)
    t = time.time() - t0
    matched = "Match Found     : true" in proc.stdout
    line = f"time={t:.3f}s matched={matched}\n"
    with open(outfile, "a") as f:
        f.write(line)
    print(line.strip(), flush=True)
    for l in proc.stdout.split("\n"):
        if any(x in l for x in ["Winner", "Solution", "Match Found", "Elapsed"]):
            with open(outfile, "a") as f:
                f.write(l.strip() + "\n")
            print(l.strip(), flush=True)
except subprocess.TimeoutExpired:
    line = f"TIMEOUT after {time.time() - t0:.1f}s\n"
    with open(outfile, "a") as f:
        f.write(line)
    print(line.strip(), flush=True)
except Exception as e:
    line = f"ERROR: {e}\n"
    with open(outfile, "a") as f:
        f.write(line)
    print(line.strip(), flush=True)
