//! APDE — Adaptive Pattern Discovery Engine.
//!
//! Reference: `Subset sum algorithm.md` line 11990 (your novel idea).
//!
//! Quick offline ML-like models are slow.  Online instance-specific
//! learning is the alternative: APDE samples random subsets, scores
//! each element by how often it appears in subsets whose sum is
//! *close to* the target, and uses those scores as a search-order
//! oracle for a backtracking solver.
//!
//! Steps:
//!   1. Take K=200 random subsets of varying size.
//!   2. For each subset, compute its sum and the fitness
//!      f = 1 - |target - sum| / target  (clamped to [0,1]).
//!   3. Update per-element scores:
//!         score[i] += f if i ∈ subset else -0.05*f
//!   4. After scoring, run a small DFS where elements are ordered
//!      by descending score.

use num_bigint::BigUint;
use num_traits::{ToPrimitive, Zero};

use crate::controller::{Engine, Shared};

pub struct ApdeEngine;

const SAMPLES: usize = 256;
const DFS_DEPTH: usize = 96;

struct Rng(u64);
impl Rng {
    fn new(seed: u64) -> Self {
        Self(if seed == 0 { 0xDEADBEEFCAFEBABE } else { seed })
    }
    fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    fn range(&mut self, n: usize) -> usize {
        if n == 0 { 0 } else { (self.next_u64() as usize) % n }
    }
}

impl Engine for ApdeEngine {
    fn name(&self) -> &'static str {
        "APDE"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if p.n == 0 || !p.u128_safe() {
            // Stay out of BigUint regime — too slow per sample.
            return;
        }
        let target = p.target_u128();
        if target == 0 {
            return;
        }
        let nums = p.numbers_u128();
        let n = nums.len();
        if n > 256 {
            return;
        }

        let mut score = vec![0f64; n];
        let mut rng = Rng::new(0xA9DE);

        for _ in 0..SAMPLES {
            if sh.stopped() {
                return;
            }
            // Sample a random subset by independent coin flips,
            // biased toward target/total density to find decent fits.
            let total: u128 = nums.iter().sum();
            let p_inc = if total > 0 {
                ((target as f64) / (total as f64)).clamp(0.05, 0.95)
            } else {
                0.5
            };
            let mut selected = vec![false; n];
            let mut sum: u128 = 0;
            for i in 0..n {
                let r = (rng.next_u64() as f64) / (u64::MAX as f64);
                if r < p_inc {
                    let cand = sum.saturating_add(nums[i]);
                    if cand <= target.saturating_mul(2) {
                        selected[i] = true;
                        sum = cand;
                    }
                }
            }
            if sum == target {
                let sol: Vec<BigUint> = (0..n)
                    .filter(|&i| selected[i])
                    .map(|i| BigUint::from(nums[i]))
                    .collect();
                sh.report(sol, "APDE");
                return;
            }
            let dist = if sum >= target { sum - target } else { target - sum };
            let fit = 1.0 - (dist as f64 / target as f64).min(1.0);
            for i in 0..n {
                if selected[i] {
                    score[i] += fit;
                } else {
                    score[i] -= 0.05 * fit;
                }
            }
        }

        // Now order elements by descending score and try a bounded
        // DFS (this exploits the "instance-specific heuristic" we
        // just learned).
        let mut order: Vec<usize> = (0..n).collect();
        order.sort_by(|&a, &b| score[b].partial_cmp(&score[a]).unwrap_or(std::cmp::Ordering::Equal));

        let mut path: Vec<usize> = Vec::with_capacity(DFS_DEPTH);
        if dfs(sh, &nums, &order, target, 0, 0, &mut path) {
            let sol: Vec<BigUint> = path.iter().map(|&i| BigUint::from(nums[i])).collect();
            sh.report(sol, "APDE");
        }
    }
}

fn dfs(
    sh: &Shared,
    nums: &[u128],
    order: &[usize],
    target: u128,
    cursor: usize,
    sum: u128,
    path: &mut Vec<usize>,
) -> bool {
    if sum == target {
        return true;
    }
    if sh.stopped() || cursor >= order.len() || path.len() >= DFS_DEPTH {
        return false;
    }
    // Suffix-sum pruning
    let mut max_remaining: u128 = 0;
    for j in cursor..order.len() {
        max_remaining = max_remaining.saturating_add(nums[order[j]]);
    }
    if sum.saturating_add(max_remaining) < target {
        return false;
    }

    let v = nums[order[cursor]];
    if sum.saturating_add(v) <= target {
        path.push(order[cursor]);
        if dfs(sh, nums, order, target, cursor + 1, sum + v, path) {
            return true;
        }
        path.pop();
    }
    dfs(sh, nums, order, target, cursor + 1, sum, path)
}

#[allow(dead_code)]
fn _is_zero(b: &BigUint) -> bool {
    b.is_zero()
}
