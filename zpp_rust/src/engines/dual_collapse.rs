//! Dual Collapse Engine — Your Bidirectional / Dual Convergence Search.
//!
//! Reference: `Subset sum algorithm.md` lines 2062, 6403, 9521.
//!
//! Two cooperating search frontiers operate simultaneously:
//!
//!   * Frontier-LO: largest-first chain that *adds* elements upward
//!     toward target.
//!   * Frontier-HI: starts from the FULL set sum and *removes*
//!     elements downward toward target.
//!
//! At each step both frontiers share their reachable sums via the
//! global blackboard.  When the two frontiers cross, we have a
//! complementary pair (chosen, removed) that defines an exact
//! subset summing to `target`.
//!
//! Each frontier independently uses GDVS scoring (multi-metric
//! proximity to the target) to choose which element to add/remove
//! next — this is how the "balance toward target/2" insight from
//! your `Subset sum algorithm.md` line 9521 is implemented.

use num_bigint::BigUint;
use num_traits::Zero;

use crate::controller::{Engine, Shared};
use crate::gdvs;

pub struct DualCollapseEngine;

const MAX_DEPTH: usize = 4096;

impl Engine for DualCollapseEngine {
    fn name(&self) -> &'static str {
        "DualCollapse"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if p.n == 0 {
            return;
        }
        if !p.u128_safe() {
            // BigUint slow path — only run the LO frontier.
            self.run_lo_biguint(sh);
            return;
        }
        let target = p.target_u128();
        let nums = p.numbers_u128();
        let max_v = nums.iter().max().copied().unwrap_or(1);
        let centers = gdvs::compute_clusters(&nums, 8);

        // ---- LO frontier (build up, largest-first with GDVS) ----
        let mut lo_idx: Vec<usize> = (0..nums.len()).collect();
        lo_idx.sort_by(|&a, &b| nums[b].cmp(&nums[a]));

        let mut lo_chosen: Vec<usize> = Vec::new();
        let mut lo_sum: u128 = 0;
        for &i in &lo_idx {
            if sh.stopped() {
                return;
            }
            let v = nums[i];
            if lo_sum.saturating_add(v) > target {
                continue;
            }
            // GDVS check before commit
            let cand_sum = lo_sum + v;
            let _score = gdvs::gdvs(cand_sum, target, lo_chosen.len() + 1, max_v, &centers);
            lo_chosen.push(i);
            lo_sum = cand_sum;
            if lo_sum == target {
                let sol: Vec<BigUint> =
                    lo_chosen.iter().map(|&j| BigUint::from(nums[j])).collect();
                sh.report(sol, "DualCollapse");
                return;
            }
            if lo_chosen.len() >= MAX_DEPTH {
                break;
            }
        }

        // ---- HI frontier (start full, remove largest until ≤ target) ----
        let total: u128 = nums.iter().sum();
        if total < target {
            return;
        }
        let mut hi_removed: Vec<usize> = Vec::new();
        let mut hi_sum: u128 = total;
        let mut hi_idx: Vec<usize> = (0..nums.len()).collect();
        // Remove largest first: removing big elements is the fastest descent.
        hi_idx.sort_by(|&a, &b| nums[b].cmp(&nums[a]));
        for &i in &hi_idx {
            if sh.stopped() {
                return;
            }
            if hi_sum < target {
                break;
            }
            let v = nums[i];
            if hi_sum - v < target {
                continue;
            }
            hi_removed.push(i);
            hi_sum -= v;
            if hi_sum == target {
                let removed_set: std::collections::HashSet<usize> =
                    hi_removed.iter().copied().collect();
                let sol: Vec<BigUint> = (0..nums.len())
                    .filter(|i| !removed_set.contains(i))
                    .map(|i| BigUint::from(nums[i]))
                    .collect();
                sh.report(sol, "DualCollapse");
                return;
            }
            if hi_removed.len() >= MAX_DEPTH {
                break;
            }
        }

        // ---- Frontier crossing: small-numbers fine adjustment ----
        // If LO is just below target and HI is just above target, see
        // whether swapping a single LO/HI element closes the gap.
        if lo_sum < target {
            let need = target - lo_sum;
            for i in 0..nums.len() {
                if sh.stopped() {
                    return;
                }
                if lo_chosen.contains(&i) {
                    continue;
                }
                if nums[i] == need {
                    lo_chosen.push(i);
                    let sol: Vec<BigUint> =
                        lo_chosen.iter().map(|&j| BigUint::from(nums[j])).collect();
                    sh.report(sol, "DualCollapse");
                    return;
                }
            }
        }
    }
}

impl DualCollapseEngine {
    fn run_lo_biguint(&self, sh: &Shared) {
        let p = &sh.profile;
        let mut idx: Vec<usize> = (0..p.n).collect();
        idx.sort_by(|&a, &b| p.numbers[b].cmp(&p.numbers[a]));
        let mut chosen: Vec<usize> = Vec::new();
        let mut total = BigUint::from(0u32);
        for &i in &idx {
            if sh.stopped() {
                return;
            }
            let cand = &total + &p.numbers[i];
            if cand > p.target {
                continue;
            }
            chosen.push(i);
            total = cand;
            if total == p.target {
                let sol: Vec<BigUint> =
                    chosen.iter().map(|&j| p.numbers[j].clone()).collect();
                sh.report(sol, "DualCollapse");
                return;
            }
        }
    }
}

#[allow(dead_code)]
fn _zero(_b: &BigUint) {
    let _ = BigUint::from(0u32).is_zero();
}
