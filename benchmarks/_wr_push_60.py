"""Push Rust binary beyond n=50. Try multiple instances per n to find success rate."""
import subprocess, time, os, random, sys
from collections import Counter

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
if not os.path.isfile(exe):
    print("No zpp.exe found")
    sys.exit(1)

def try_instance(nums, target, timeout=300):
    inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"
    t0 = time.time()
    try:
        proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=timeout)
        t = time.time() - t0
        matched = "Match Found     : true" in proc.stdout
        if matched:
            eng_line = [l for l in proc.stdout.split('\n') if 'Winner' in l]
            eng = eng_line[0].strip() if eng_line else "?"
            time_line = [l for l in proc.stdout.split('\n') if 'Seconds' in l and 'CPU' not in l and 'Active' not in l]
            return True, t, eng, time_line[0].strip() if time_line else ""
        return False, t, "", ""
    except subprocess.TimeoutExpired:
        return False, timeout, "", "timeout"

print(f"{'n':>4s}  {'inst':>4s}  {'result':>6s}  {'time':>8s}  {'engine':>30s}")
print("-" * 65)

results = Counter()
for n in [48, 50, 52, 54, 56, 58, 60]:
    for inst in range(5):
        random.seed(n * 1000 + inst)
        nums = sorted(random.sample(range(10**13, 10**15), n))
        k = max(1, n // 7)
        target = sum(random.sample(nums, k))
        ok, t, eng, detail = try_instance(nums, target, timeout=120 if n < 58 else 180)
        eng_short = eng.replace("Engine Winner   : ", "") if ok else "-"
        status = "OK" if ok else "FAIL"
        results[(n, ok)] += 1
        print(f"  {n:2d}  {inst+1:2d}/5  {status:>4s}  {t:7.2f}s  {eng_short:>30s}")

print(f"\n--- Summary ---")
for n in [48, 50, 52, 54, 56, 58, 60]:
    ok = sum(1 for (nn, o) in results if nn == n and o)
    total_inst = sum(1 for (nn, _) in results if nn == n)
    rate = ok / total_inst * 100 if total_inst > 0 else 0
    print(f"  n={n:2d}: {ok}/{total_inst} passed ({rate:.0f}%)")
