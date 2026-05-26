"""Test n=72 — can we solve it in <10 min?"""
import subprocess, time, random, sys
exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
n = 72
q = n // 4
random.seed(72001)
nums = sorted(random.sample(range(10**14, 10**15), n))
k = n // 7
target = sum(random.sample(nums, k))
csv = ",".join(str(x) for x in nums)
inp = f"2\n{csv}\n{target}\n"
print(f"n={n} q={q} target={target}")
sys.stdout.flush()
t0 = time.time()
proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
proc.stdin.write(inp)
proc.stdin.close()
try:
    stdout, stderr = proc.communicate(timeout=600)
    t = time.time() - t0
    ok = "Match Found     : true" in stdout
    w = [l for l in stdout.split("\n") if "Winner" in l]
    print(f"n={n} time={t:.3f}s ok={ok} {w[0].strip() if w else ''}")
except subprocess.TimeoutExpired:
    proc.kill()
    print(f"n={n} TIMEOUT after 600s")
