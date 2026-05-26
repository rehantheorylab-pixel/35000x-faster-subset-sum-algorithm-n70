import subprocess, time
exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
with open(r"C:\Users\rehan\algorithm\jnh1.cnf\z_test_elements.txt") as f:
    elem_line = f.readline().strip()
    f.readline()
    target_line = f.readline().strip()
target = target_line.split(": ")[1] if ": " in target_line else target_line
elems = elem_line.split(", ")
print(f"Elements: {len(elems)}  Target digits: {len(target)}", flush=True)
inp = f"2\n{elem_line}\n{target}\n"
t0 = time.time()
proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=600)
t = time.time() - t0
matched = "Match Found     : true" in proc.stdout
print(f"time={t:.3f}s matched={matched}")
for line in proc.stdout.split("\n"):
    if any(x in line for x in ["Winner", "Solution", "Match Found", "Elapsed"]):
        print(line.strip())
