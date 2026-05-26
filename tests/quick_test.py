"""Quick test: load z_test_elements.txt and solve with Z++"""
import time
from z_colab_benchmark import ZUltimateController

with open('jnh1.cnf/z_test_elements.txt') as f:
    data = f.read()

parts = data.split('goal:')
elems = [int(x.strip()) for x in parts[0].strip().split(',') if x.strip()]
target = int(parts[1].strip())

print(f"Elements: {len(elems)}")
print(f"Target digits: {len(str(target))}")
print(f"Running Z++...\n")

t0 = time.time()
ctrl = ZUltimateController(elems, target, print)
res = ctrl.run(max_time=60, verbose=True)
elapsed = time.time() - t0

print(f"\n{'='*60}")
print(f"  RESULT: exact={res['exact']}  engine={res['engine']}  time={elapsed:.2f}s")
if res['exact']:
    print(f"  Solution has {len(res['solution'])} elements")
    print(f"  Sum verified: {sum(res['solution']) == target}")
print(f"{'='*60}")
