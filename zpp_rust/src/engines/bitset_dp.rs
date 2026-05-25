//! Bitset DP engine: exact subset-sum via 64-way packed bitset.
//! Time: O(n * t / 64).  Provably correct: returns IMPOSSIBLE if no
//! subset reaches the target.

use num_bigint::BigUint;
use num_traits::ToPrimitive;
use std::sync::atomic::Ordering;

use crate::bitset::Bitset;
use crate::controller::{Engine, Shared};

pub struct BitsetDpEngine;

const MAX_TARGET_BITS: u64 = 27; // ~134 M bit target = ~16 MiB bitset

impl Engine for BitsetDpEngine {
    fn name(&self) -> &'static str {
        "BitsetDP"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if p.target.bits() > MAX_TARGET_BITS {
            return;
        }
        let target = match p.target.to_usize() {
            Some(t) => t,
            None => return,
        };

        let mut dp = Bitset::new(target + 1);
        dp.set(0);
        let mut history: Vec<Bitset> = Vec::with_capacity(p.n + 1);
        history.push(dp.clone());

        let mut elem_usizes: Vec<usize> = Vec::with_capacity(p.n);
        for x in &p.numbers {
            match x.to_usize() {
                Some(u) => elem_usizes.push(u),
                None => return,
            }
        }

        for (i, &num) in elem_usizes.iter().enumerate() {
            if sh.stopped() {
                return;
            }
            dp.shift_or_inplace(num);
            history.push(dp.clone());
            if dp.get(target) {
                if let Some(sol) = reconstruct(&history, &elem_usizes, target) {
                    let big_sol: Vec<BigUint> =
                        sol.into_iter().map(BigUint::from).collect();
                    sh.report(big_sol, "BitsetDP");
                }
                return;
            }
            // Allow other engines to use CPU cycles too.
            let _ = i;
        }

        if !dp.get(target) {
            sh.proved_impossible.store(true, Ordering::Release);
        }
    }
}

fn reconstruct(history: &[Bitset], nums: &[usize], target: usize) -> Option<Vec<usize>> {
    let mut cur = target;
    let mut sol: Vec<usize> = Vec::new();
    let mx = nums.len().min(history.len() - 1);
    for i in (0..mx).rev() {
        if cur == 0 {
            break;
        }
        let v = nums[i];
        if cur >= v && history[i].get(cur - v) {
            sol.push(v);
            cur -= v;
        }
    }
    if cur == 0 {
        Some(sol)
    } else {
        None
    }
}
