//! Adaptive Residue Engine — multi-prime impossibility filter.
//! Selects moduli based on instance size: more primes for larger n.
//! If any prime says the target is unreachable modulo p, the instance
//! is provably impossible and we set the shared flag so other engines
//! can stop early.

use num_bigint::BigUint;
use std::sync::atomic::Ordering;

use crate::controller::{Engine, Shared};

pub struct ResidueEngine;

// All primes <= 61: they fit in a u64 bitmask.
const SMALL_PRIMES: &[u32] = &[
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
    31, 37, 41, 43, 47, 53, 59, 61,
];
const SMALL_COUNT: usize = 10; // Always run at least 10.

impl Engine for ResidueEngine {
    fn name(&self) -> &'static str {
        "Residue"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;

        // Adaptive prime count: more primes for larger inputs.
        let count = if p.n >= 60 {
            SMALL_PRIMES.len()
        } else if p.n >= 40 {
            14
        } else {
            SMALL_COUNT
        };
        let primes = &SMALL_PRIMES[..count];

        for &prime in primes {
            if sh.stopped() {
                return;
            }
            let p_big = BigUint::from(prime);
            let target_r = u32::try_from(&p.target % &p_big).unwrap_or(0);
            let mask: u64 = (1u64 << prime) - 1;
            let mut reach: u64 = 1; // Bit 0 = sum 0 is reachable.
            for x in &p.numbers {
                let r = u32::try_from(x % &p_big).unwrap_or(0) % prime;
                // DP: reachable sums shift by r then OR with existing.
                let shifted = reach << r;
                reach = (reach | shifted | (shifted >> prime)) & mask;
                // Early stop: if target_r is reachable, keep going;
                // if not, we'll catch it after the loop.
            }
            if (reach & (1u64 << target_r)) == 0 {
                sh.proved_impossible.store(true, Ordering::Release);
                sh.stop.store(true, Ordering::Release);
                return;
            }
        }
    }
}
