//! # Cascade Digit Filter Array

//! Parallel congruence checks for fastest impossibility detection.

use num_bigint::BigUint;
use crate::controller::{Engine, Shared};

pub struct CascadeEngine;
impl CascadeEngine {
    fn run_cascade(sh: &Shared) {
        let p = &sh.profile;
        let (candidates, cascades_used) = Self::filter_cascade(p);
        if cascades_used == 0 { return; }
        for c in &candidates {
            if sh.stopped() { return; }
            let sum: BigUint = c.iter().sum();
            if sum == p.target { sh.report(c.clone(), "Cascade"); return; }
        }
    }

    fn filter_cascade(p: &crate::profile::Profile) -> (Vec<Vec<BigUint>>, u32) {
        let mut sets = vec![p.numbers.clone()];
        let mut cascades = 0u32;
        for m in [3u64, 5, 7, 11, 13, 17, 19, 23] {
            if sets.is_empty() { break; }
            let t_mod = &p.target % m;
            sets = sets.into_iter().filter(|s| {
                let sm: BigUint = s.iter().sum();
                sm % m == t_mod
            }).collect();
            cascades += 1;
        }
        for k in 1..=4 {
            if sets.is_empty() { break; }
            let m = 1u64 << k;
            let t_mod = &p.target % m;
            sets = sets.into_iter().filter(|s| {
                let sm: BigUint = s.iter().sum();
                sm % m == t_mod
            }).collect();
            cascades += 1;
        }
        (sets, cascades)
    }
}

impl Engine for CascadeEngine {
    fn name(&self) -> &'static str { "CascadeEngine" }
    fn run(&self, sh: &Shared) { Self::run_cascade(sh); }
}
