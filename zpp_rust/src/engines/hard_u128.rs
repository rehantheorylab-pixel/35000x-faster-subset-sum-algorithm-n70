//! Hard-U128 fast path — Schroeppel–Shamir only, no heuristic noise.
//!
//! For n ∈ [44, 72] with u128 elements, runs the optimal 4-way
//! meet-in-the-middle (O(2^(n/4)) space) before other engines can
//! waste CPU on exponential BigUint heuristics.

use num_bigint::BigUint;

use crate::controller::{Engine, Shared};
use crate::knapsack::schroeppel_shamir_u128;

pub struct HardU128Engine;

const MIN_N: usize = 44;
const MAX_N: usize = 80;

impl Engine for HardU128Engine {
    fn name(&self) -> &'static str {
        "Hard-U128"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if p.n < MIN_N || p.n > MAX_N || !p.u128_safe() {
            return;
        }

        let target = p.target_u128();
        let nums = p.numbers_u128();
        let n = nums.len();
        let q = n / 4;
        if q == 0 || q > 20 {
            return;
        }

        let qa = &nums[0..q];
        let qb = &nums[q..2 * q];
        let qc = &nums[2 * q..3 * q];
        let qd = &nums[3 * q..];

        if sh.stopped() {
            return;
        }

        if let Some(sol) = schroeppel_shamir_u128(qa, qb, qc, qd, target) {
            let big: Vec<BigUint> = sol.into_iter().map(BigUint::from).collect();
            sh.report(big, "Hard-U128");
        }
    }
}
