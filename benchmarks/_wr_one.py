"""Test single n with timeout, print immediate output."""
import subprocess, time, os, random, sys

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
if not os.path.isfile(exe):
    print("NO RUST BINARY")
    sys.exit(1)

n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 120
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 999

random.seed(seed)
nums = sorted(random.sample(range(10**14, 10**15), n))
k = max(1, n // 7)
target = sum(random.sample(nums, k))

print(f"n={n} timeout={timeout}s seed={seed}")
print(f"target={target} (digits={len(str(target))})")

inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"
t0 = time.time()
try:
    proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=timeout)
    t = time.time() - t0
    matched = "Match Found     : true" in proc.stdout
    print(f"time={t:.3f}s matched={matched}")
    if matched:
        eng = [l for l in proc.stdout.split('\n') if 'Winner' in l]
        print(f"engine={eng[0].strip() if eng else '?'}")
    else:
        # Print last few lines
        lines = proc.stdout.strip().split('\n')
        for l in lines[-5:]:
            print(f"  {l.strip()}")
except subprocess.TimeoutExpired:
    t = time.time() - t0
    print(f"TIMEOUT after {t:.1f}s")
except Exception as e:
    print(f"ERROR: {e}")
