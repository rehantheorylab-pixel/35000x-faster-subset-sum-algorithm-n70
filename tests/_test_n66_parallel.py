"""Test n=66 with parallel SS (shared CD heap). Runs for 660s max."""
import subprocess, time, random, sys

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"

random.seed(66001)
n = 66
nums = sorted(random.sample(range(10**14, 10**15), n))
k = n // 7
target = sum(random.sample(nums, k))
inp = f"2\n{','.join(str(x) for x in nums)}\n{target}\n"
print(f"n={n} target={target}", flush=True)

t0 = time.time()
proc = subprocess.Popen(
    [exe],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
proc.stdin.write(inp)
proc.stdin.close()

try:
    stdout, stderr = proc.communicate(timeout=660)
    t = time.time() - t0
    matched = "Match Found     : true" in stdout
    winner_line = [l for l in stdout.split("\n") if "Engine Winner" in l]
    print(f"time={t:.3f}s matched={matched} winner={winner_line[0].strip() if winner_line else '?'}")
except subprocess.TimeoutExpired:
    proc.kill()
    print(f"TIMEOUT after 660s")
