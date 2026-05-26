"""
Z++ Ultimate Engine v3.0 — Automated Test Suite
Tests correctness across diverse problem types:
  trivial, small, medium, impossible, edge cases, random.
"""

import time
import random
from Z_plus_plus_gui import ZUltimateController


def run_test(name, numbers, target, expect_possible=True):
    """Run a single test and print pass/fail."""
    log_lines = []
    ctrl = ZUltimateController(numbers, target, lambda msg: log_lines.append(msg))
    res = ctrl.run(max_time=15.0)

    status = ""
    if expect_possible:
        if res['exact']:
            if sum(res['solution']) == target:
                pool = list(numbers)
                valid = True
                for x in res['solution']:
                    if x in pool:
                        pool.remove(x)
                    else:
                        valid = False
                        break
                if valid:
                    status = "PASS"
                else:
                    status = "FAIL (element not in input)"
            else:
                status = "FAIL (sum mismatch)"
        else:
            status = "FAIL (no solution found)"
    else:
        if res['impossible']:
            status = "PASS"
        elif res['exact']:
            status = "FAIL (found solution for impossible case!)"
        else:
            status = "WARN (timeout, not proved impossible)"

    engine = res['engine']
    t = res['time']
    print(f"  [{status}] {name:40s}  {t:8.4f}s  engine={engine}")
    if "FAIL" in status:
        print(f"         Solution: {res['solution']}")
        print(f"         Sum: {res['sum']}  Target: {target}")
    return "PASS" in status


def main():
    print("=" * 70)
    print("  Z++ ULTIMATE ENGINE v3.0 — TEST SUITE")
    print("=" * 70)
    results = []

    # --- Trivial cases ---
    print("\n--- Trivial Cases ---")
    results.append(run_test(
        "Empty target (goal=0)",
        [1, 2, 3], 0))
    results.append(run_test(
        "Single element match",
        [10, 20, 30], 20))
    results.append(run_test(
        "All elements = target",
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 55))
    results.append(run_test(
        "Two element (2-Sum)",
        [3, 7, 11, 15], 18))

    # --- Impossible cases ---
    print("\n--- Impossible Cases ---")
    results.append(run_test(
        "Target > total sum",
        [1, 2, 3], 100, expect_possible=False))
    results.append(run_test(
        "Odd target, all even elements",
        [2, 4, 6, 8, 10], 7, expect_possible=False))
    results.append(run_test(
        "Residue impossible (mod 3)",
        [3, 6, 9, 12], 5, expect_possible=False))
    results.append(run_test(
        "No valid combination",
        [10, 20, 30], 15, expect_possible=False))

    # --- Small cases (MITM territory) ---
    print("\n--- Small Cases (n<=40, MITM) ---")
    results.append(run_test(
        "Classic candy problem",
        [1, 3, 7, 21, 50, 200, 400, 499, 1000, 1500, 2000, 5000, 10000, 25000],
        5570))
    results.append(run_test(
        "Powers of 2",
        [1, 2, 4, 8, 16, 32, 64, 128, 256, 512], 1023))
    results.append(run_test(
        "Consecutive integers goal=50",
        list(range(1, 21)), 50))
    results.append(run_test(
        "Fibonacci-like set",
        [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144], 100))
    results.append(run_test(
        "Large spread",
        [1, 10, 100, 1000, 10000, 100000], 10101))

    # --- Medium cases (Bitset DP territory) ---
    print("\n--- Medium Cases ---")
    results.append(run_test(
        "50 elements, target=500",
        list(range(1, 51)), 500))
    results.append(run_test(
        "100 elements, target=2550",
        list(range(1, 101)), 2550))
    results.append(run_test(
        "Uniform values (all 7s)",
        [7] * 20, 49))
    results.append(run_test(
        "Mixed small & large",
        [1, 2, 3, 4, 5, 1000, 2000, 3000, 4000, 5000], 6005))

    # --- Edge cases ---
    print("\n--- Edge Cases ---")
    results.append(run_test(
        "Single element = target",
        [42], 42))
    results.append(run_test(
        "Single element != target",
        [42], 10, expect_possible=False))
    results.append(run_test(
        "Duplicate elements",
        [5, 5, 5, 5, 5], 15))
    results.append(run_test(
        "Target = 1, set has 1",
        [1, 100, 200, 300], 1))
    results.append(run_test(
        "Need all-but-one",
        [10, 20, 30, 40, 50], 140))

    # --- Worst-case-like tests ---
    print("\n--- Worst-Case / Hard Tests ---")
    results.append(run_test(
        "Dense mid-range (bridge territory)",
        list(range(100, 200)), 7350))
    results.append(run_test(
        "Arithmetic progression n=80",
        list(range(5, 405, 5)), 2000))
    results.append(run_test(
        "Large n=200, target from middle",
        list(range(1, 201)), 5050))
    results.append(run_test(
        "Random-looking (hard for greedy)",
        [13, 17, 23, 29, 31, 37, 41, 43, 47, 53,
         59, 61, 67, 71, 73, 79, 83, 89, 97, 101], 200))
    results.append(run_test(
        "Impossible hard (close to sum)",
        [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        555, expect_possible=False))
    results.append(run_test(
        "Needs exact 3 mid-elements",
        [1, 2, 3, 100, 200, 300, 10000, 20000, 30000], 60300))
    results.append(run_test(
        "50 elements, structured target",
        list(range(1, 51)), 637))
    results.append(run_test(
        "Uniform n=30 (all 100s)",
        [100] * 30, 1700))

    # --- Random stress tests ---
    print("\n--- Random Stress Tests ---")
    for i in range(8):
        n = random.randint(10, 80)
        nums = sorted(random.sample(range(1, 1000), min(n, 999)))
        subset_size = random.randint(1, min(8, len(nums)))
        subset = random.sample(nums, subset_size)
        target = sum(subset)
        results.append(run_test(
            f"Random n={len(nums)} target={target}",
            nums, target))

    # --- Summary ---
    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 70}")
    print(f"  RESULTS:  {passed}/{total} passed")
    if passed == total:
        print("  ALL TESTS PASSED")
        else:
        print(f"  {total - passed} FAILED")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
