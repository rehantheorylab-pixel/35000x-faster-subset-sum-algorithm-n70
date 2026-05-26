// Goal-Driven Element Partitioning (GDEP) Engine
// Rehan's discovery: after picking an element, restrict the pool
// to only elements <= the new remainder. This dynamically shrinks
// both the goal AND the available element set during recursion.
//
// Core innovation: pool restriction creates natural pruning --
// elements larger than the current remainder are automatically
// excluded from deeper recursion levels.

use num_bigint::BigUint;
use num_traits::Zero;

use crate::controller::{Engine, Shared};

pub struct GdepEngine;

impl Engine for GdepEngine {
    fn name(&self) -> &'static str {
        "GDEP"
    }

    fn run(&self, sh: &Shared) {
        let nums = &sh.profile.numbers;
        let target = &sh.profile.target;
        let n = nums.len();

        if n == 0 || target.is_zero() {
            if target.is_zero() {
                sh.report(vec![], "GDEP");
            }
            return;
        }

        // Sort descending for largest-first selection
        let mut desc: Vec<BigUint> = nums.to_vec();
        desc.sort_by(|a, b| b.cmp(a));

        // Build suffix sums for aggressive pruning
        let mut suf: Vec<BigUint> = vec![BigUint::zero(); n + 1];
        for i in (0..n).rev() {
            suf[i] = &suf[i + 1] + &desc[i];
        }

        let mut path: Vec<BigUint> = Vec::new();

        // DFS with pool restriction: each recursion layer only considers
        // elements <= the current remainder target
        fn dfs(
            nums: &[BigUint],
            suf: &[BigUint],
            target: &BigUint,
            start: usize,
            n: usize,
            path: &mut Vec<BigUint>,
            sh: &Shared,
        ) -> bool {
            if target.is_zero() {
                return true;
            }
            if sh.stopped() || start >= n {
                return false;
            }

            let remaining = target;

            for i in start..n {
                let v = &nums[i];
                if v > remaining {
                    continue; // GDEP pool restriction: skip elements > remainder
                }
                if suf[i] < *target {
                    return false; // can't reach target with remaining elements
                }
                if v == remaining {
                    path.push(v.clone());
                    return true;
                }

                let new_target = remaining - v;
                if suf[i + 1] >= new_target {
                    path.push(v.clone());
                    if dfs(nums, suf, &new_target, i + 1, n, path, sh) {
                        return true;
                    }
                    path.pop();
                }
            }
            false
        }

        if dfs(&desc, &suf, target, 0, n, &mut path, sh) {
            sh.report(path, "GDEP");
        }
    }
}
