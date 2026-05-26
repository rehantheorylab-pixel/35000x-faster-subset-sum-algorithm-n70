"""Test n=66 with debug output — run for 120s to get quarter sizes."""
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
# Use a pipe; manually read stderr with a timeout
proc = subprocess.Popen(
    [exe],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
stdout_data = []
stderr_data = []
# Send input
proc.stdin.write(inp)
proc.stdin.close()

# Poll for 120s, capturing stderr
deadline = time.time() + 120
while time.time() < deadline:
    line = proc.stderr.readline()
    if line:
        print(f"[STDERR] {line.strip()}", flush=True)
    if proc.poll() is not None:
        break

if proc.poll() is None:
    proc.kill()
    print("KILLED after 120s", flush=True)

t = time.time() - t0
stdout = proc.stdout.read() if proc.stdout else ""
matched = "Match Found     : true" in stdout
print(f"\ntime={t:.3f}s matched={matched}", flush=True)
for line in stdout.split("\n"):
    if any(x in line for x in ["Winner", "Solution", "Match Found"]):
        print(f"  {line.strip()}")
