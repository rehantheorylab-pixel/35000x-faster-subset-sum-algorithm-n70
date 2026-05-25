//! Residue Engine — multi-prime impossibility filter.
//! Runs all 10 primes; if any prime says the target is unreachable
//! modulo p, the instance is provably impossible and we set the
//! shared flag so other engines can stop early.

use num_bigint::BigUint;
use std::sync::atomic::Ordering;

use crate::controller::{Engine, Shared};

pub struct ResidueEngine;

const PRIMES: &[u32] = &[2, 3, 5, 7, 11, 13, 17, 19, 23, 29];

impl Engine for ResidueEngine {
    fn name(&self) -> &'static str {
        "Residue"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        for &prime in PRIMES {
            if sh.stopped() {
                return;
            }
            let p_big = BigUint::from(prime);
            let target_r =
                u32::try_from(&p.target % &p_big).unwrap_or(0);
            let mask: u64 = (1u64 << prime) - 1;
            let mut reach: u64 = 1;
            for x in &p.numbers {
                let r = u32::try_from(x % &p_big).unwrap_or(0);
                let shifted = reach << r;
                reach = (reach | shifted | (shifted >> prime)) & mask;
            }
            if (reach & (1u64 << target_r)) == 0 {
                sh.proved_impossible.store(true, Ordering::Release);
                sh.stop.store(true, Ordering::Release);
                return;
            }
        }
    }
}
