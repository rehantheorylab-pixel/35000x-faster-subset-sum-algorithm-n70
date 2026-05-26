import sys, time, importlib.util, random
spec = importlib.util.spec_from_file_location("zpp_wr", r"C:\Users\rehan\algorithm\Z++.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test(name, nums, target, timeout=600.0):
    t0 = time.time()
    ctrl = mod.ZUltimateController(nums, target)
    res = ctrl.run(max_time=timeout)
    elapsed = time.time() - t0
    ok = False
    if res["exact"] and res["solution"] is not None and sum(res["solution"]) == target:
        pool = list(nums)
        valid = True
        for x in res["solution"]:
            if x in pool:
                pool.remove(x)
            else:
                valid = False
                break
        if valid:
            ok = True
    status = "PASS" if ok else "FAIL"
    print(f"{name}: {status}  {elapsed:.3f}s  eng={res['engine']}")
    return ok

random.seed(50)
nums55 = sorted(random.sample(range(10**13, 10**15), 55))
target55 = sum(random.sample(nums55, max(1, 55//7)))
test("Hard64 n=55", nums55, target55)

random.seed(53)
nums50 = sorted(random.sample(range(10**12, 10**14), 50))
indices = sorted(random.sample(range(50), max(1, 50//6)))
target50 = sum(nums50[i] for i in indices)
test("UniqueSol n=50", nums50, target50)
