"""Debug Rust binary on specific instances to understand engine behavior."""
import subprocess, time, os, random, sys

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"
if not os.path.isfile(exe):
    print("No zpp.exe found")
    sys.exit(1)

print(f"zpp.exe: {os.path.getsize(exe)} bytes")
print()

# Test 1: Classic 5570
print("=" * 70)
print("TEST 1: Classic 5570")
print("=" * 70)
inp = "2\n1,3,7,21,50,200,400,499,1000,1500,2000,5000,10000,25000\n5570\n"
t0 = time.time()
proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=30)
t = time.time() - t0
print(proc.stdout)
print(f"Time: {t:.4f}s, Error: {proc.stderr[:200] if proc.stderr else 'none'}")

# Test 2: n=30 random
print("\n" + "=" * 70)
print("TEST 2: Random n=30")
print("=" * 70)
random.seed(42)
nums = sorted(random.sample(range(1, 20000), 30))
k = random.randint(1, 8)
sol = sorted(random.sample(nums, k))
target = sum(sol)
inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"
t0 = time.time()
proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=30)
t = time.time() - t0
matched = "Match Found     : true" in proc.stdout
if matched:
    eng_line = [l for l in proc.stdout.split('\n') if 'Winner' in l]
    eng = eng_line[0].strip() if eng_line else "?"
    sol_size = [l for l in proc.stdout.split('\n') if 'Solution Size' in l]
    print(f"Matched: YES, Engine: {eng}, Size: {sol_size}, Time: {t:.4f}s")
else:
    print(f"Matched: NO, Time: {t:.4f}s")

# Test 3: n=40 random 
print("\n" + "=" * 70)
print("TEST 3: Random n=40")
print("=" * 70)
random.seed(123)
nums = sorted(random.sample(range(1, 10**12), 40))
k = random.randint(1, 10)
sol = sorted(random.sample(nums, k))
target = sum(sol)
inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"
t0 = time.time()
proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=120)
t = time.time() - t0
matched = "Match Found     : true" in proc.stdout
if matched:
    eng_line = [l for l in proc.stdout.split('\n') if 'Winner' in l]
    eng = eng_line[0].strip() if eng_line else "?"
    sol_size = [l for l in proc.stdout.split('\n') if 'Solution Size' in l]
    print(f"Matched: YES, Engine: {eng}, Size: {sol_size}, Time: {t:.4f}s")
    timing_line = [l for l in proc.stdout.split('\n') if 'Seconds' in l and 'CPU' not in l and 'Active' not in l]
    if timing_line:
        print(f"  Time: {timing_line[0].strip()}")
else:
    print(f"Matched: NO, Time: {t:.4f}s")
    for line in proc.stdout.split('\n'):
        if 'Match' in line or 'Engine' in line or 'Winner' in line or 'Elements' in line:
            print(f"  {line.strip()}")

# Test 4: n=50 random (the right way - construct solution)
print("\n" + "=" * 70)
print("TEST 4: Random n=50 with constructed solution")
print("=" * 70)
random.seed(456)
nums = sorted(random.sample(range(1, 10**15), 50))
k = random.randint(1, 12)
indices = sorted(random.sample(range(50), k))
target = sum(nums[i] for i in indices)
inp = f"2\n{', '.join(str(x) for x in nums)}\n{target}\n"
print(f"  n=50, k={k}, target digits={len(str(target))}")
t0 = time.time()
proc = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=120)
t = time.time() - t0
matched = "Match Found     : true" in proc.stdout
if matched:
    eng_line = [l for l in proc.stdout.split('\n') if 'Winner' in l]
    eng = eng_line[0].strip() if eng_line else "?"
    timing_line = [l for l in proc.stdout.split('\n') if 'Seconds' in l and 'CPU' not in l and 'Active' not in l]
    print(f"  Matched: YES, Engine: {eng}, Time: {t:.4f}s")
    if timing_line:
        print(f"  Time: {timing_line[0].strip()}")
else:
    print(f"  Matched: NO, Time: {t:.4f}s")
    for line in proc.stdout.split('\n'):
        if 'Match' in line or 'Winner' in line or 'Error' in line or 'Engine' in line:
            print(f"  {line.strip()}")
