"""Test Hard-U128 only on n=66 seed=66001, with quarter size logging."""
import subprocess, time, random, sys

exe = r"C:\Users\rehan\algorithm\zpp_rust\target\release\zpp.exe"

random.seed(66001)
n = 66
nums = sorted(random.sample(range(10**14, 10**15), n))
k = n // 7
target = sum(random.sample(nums, k))
inp = f"2\n{','.join(str(x) for x in nums)}\n{target}\n"
print(f"n={n} target={target}", flush=True)

# Quarter sizes
q = n // 4
qa = nums[0:q]
qb = nums[q:2*q]
qc = nums[2*q:3*q]
qd = nums[3*q:]
print(f"q={q} qa={len(qa)} qb={len(qb)} qc={len(qc)} qd={len(qd)}")
print(f"qa range [{min(qa):.2e}, {max(qa):.2e}] avg={sum(qa)/len(qa):.2e}")
print(f"qd range [{min(qd):.2e}, {max(qd):.2e}] avg={sum(qd)/len(qd):.2e}")

# Count how many subset sums <= target for each quarter
def count_subsets(els, tgt):
    cnt = 0
    for mask in range(1 << len(els)):
        s = 0
        m = mask
        while m:
            bit = (m & -m).bit_length() - 1
            s += els[bit]
            if s > tgt:
                break
            m ^= (1 << bit)
        if s <= tgt:
            cnt += 1
    return cnt

t0 = time.time()
print(f"Counting qd subsets...", end=" ", flush=True)
cnt_d = count_subsets(qd, target)
print(f"{cnt_d} (t={time.time()-t0:.2f}s)", flush=True)
print(f"Counting qa subsets...", end=" ", flush=True)
cnt_a = count_subsets(qa, target)
print(f"{cnt_a} (t={time.time()-t0:.2f}s)", flush=True)
