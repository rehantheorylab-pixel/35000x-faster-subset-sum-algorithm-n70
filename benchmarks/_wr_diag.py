"""Diagnose Rust binary failure. Capture full output."""
import subprocess, time, os, random, sys

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
if not os.path.isfile(exe):
    print("NO RUST BINARY")
    sys.exit(1)

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
n = int(sys.argv[2]) if len(sys.argv) > 2 else 60

random.seed(seed)
nums = sorted(random.sample(range(10**14, 10**15), n))
k = max(1, n // 7)
target = sum(random.sample(nums, k))

print(f"==== DIAG: n={n} seed={seed} target={target} ====")
inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"

t0 = time.time()
try:
    proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=180)
    t = time.time() - t0
    print(f"Time: {t:.3f}s")
    print(f"STDOUT ({len(proc.stdout)} bytes):")
    print(proc.stdout)
    if proc.stderr:
        print(f"STDERR: {proc.stderr[:500]}")
except subprocess.TimeoutExpired:
    print(f"TIMEOUT after {(time.time() - t0):.1f}s")
except Exception as e:
    print(f"ERROR: {e}")
