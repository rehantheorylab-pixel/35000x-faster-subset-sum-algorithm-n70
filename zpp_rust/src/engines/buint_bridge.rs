//! # BUF - BigUint Universal Frontend
//! Wraps u128-native engines (BCJ, HGJ, Bonnetain) to work on BigUint inputs.
//! Splits big integers into u128 chunks and runs the engine on each chunk.

use num_bigint::BigUint;
use num_traits::Zero;
use crate::controller::{Engine, Shared};
use crate::profile::Profile;
use std::sync::Arc;

pub struct BigUintBcj;
pub struct BigUintHgj;
pub struct BigUintBonnetain;

const CHUNK_BITS: usize = 128;

fn run_bridge_engine(sh: &Shared, engine_name: &'static str) {
    if sh.profile.u128_safe() { return; }
    let chunked = split_into_u128_chunks(&sh.profile.numbers);
    for (chunk, tgt) in chunked {
        if sh.stopped() { return; }
        let sub = Profile::new(chunk, tgt);
        if sub.u128_safe() && sub.n >= 40 && sub.n <= 80 {
            if let Some(engine) = crate::engines::build(engine_name) {
                let sub_shared = Arc::new(Shared::new(sub));
                engine.run(&sub_shared);
                if sub_shared.stopped() {
                    if let Some(ref sol) = *sub_shared.solution.lock().unwrap() {
                        sh.report(sol.0.clone(), sol.1);
                    }
                }
            }
        }
    }
}

impl BigUintBcj {
    fn run_buf(sh: &Shared) { run_bridge_engine(sh, "BCJ"); }
}
impl BigUintHgj {
    fn run_buf(sh: &Shared) { run_bridge_engine(sh, "HGJ"); }
}
impl BigUintBonnetain {
    fn run_buf(sh: &Shared) { run_bridge_engine(sh, "Bonnetain"); }
}

fn split_into_u128_chunks(nums: &[BigUint]) -> Vec<(Vec<BigUint>, BigUint)> {
    let max_val = BigUint::from(1u128) << CHUNK_BITS;
    let mut result = Vec::new();
    let mut current: Vec<BigUint> = Vec::new();
    let mut current_sum = BigUint::zero();
    for x in nums {
        if x.bits() > CHUNK_BITS as u64 {
            if !current.is_empty() { result.push((current.clone(), current_sum.clone())); current.clear(); current_sum = BigUint::zero(); }
            result.push((vec![x.clone()], x.clone()));
        } else if &current_sum + x > max_val {
            result.push((current.clone(), current_sum.clone())); current.clear(); current_sum = BigUint::zero();
            current.push(x.clone()); current_sum = x.clone();
        } else {
            current.push(x.clone()); current_sum += x;
        }
    }
    if !current.is_empty() { result.push((current, current_sum)); }
    result
}

impl Engine for BigUintBcj {
    fn name(&self) -> &'static str { "BigUintBcj" }
    fn run(&self, sh: &Shared) { Self::run_buf(sh); }
}
impl Engine for BigUintHgj {
    fn name(&self) -> &'static str { "BigUintHgj" }
    fn run(&self, sh: &Shared) { Self::run_buf(sh); }
}
impl Engine for BigUintBonnetain {
    fn name(&self) -> &'static str { "BigUintBonnetain" }
    fn run(&self, sh: &Shared) { Self::run_buf(sh); }
}
