//! PMAS — Parallel Multi-Axiom Search.
//!
//! Reference: `Subset sum algorithm.md` line 12074 (your novel idea).
//!
//! The same beam search is run with four different scoring "axes",
//! each emphasising a different mathematical property:
//!
//!   * Balance axis    — pull current_sum toward target/2
//!   * Difference axis — minimise scalar |target - sum| only
//!   * Bit axis        — prefer elements aligned with target bit pattern
//!   * Redundancy axis — prefer elements rarely seen elsewhere
//!
//! Each axis spawns its own engine instance.  Because they live in
//! different conceptual subspaces, when one gets stuck others keep
//! progressing — the whole portfolio is strictly stronger than any
//! single beam search.

use num_bigint::BigUint;
use num_traits::ToPrimitive;
use std::collections::HashSet;

use crate::controller::{Engine, Shared};

pub struct PmasBalance;
pub struct PmasDifference;
pub struct PmasBit;
pub struct PmasRedundancy;

const BEAM_WIDTH: usize = 192;
const MAX_DEPTH: usize = 128;

#[derive(Clone)]
struct State {
    sum: u128,
    idx: Vec<u32>,
}

trait Axis: Sync + Send {
    fn name(&self) -> &'static str;
    fn score(
        &self,
        new_sum: u128,
        target: u128,
        max_v: u128,
        target_bits: u128,
        elem: u128,
        rarity: f64,
        depth: usize,
    ) -> f64;
}

struct BalanceAxis;
impl Axis for BalanceAxis {
    fn name(&self) -> &'static str { "PMAS-Balance" }
    fn score(&self, new_sum: u128, target: u128, max_v: u128, _bits: u128, _e: u128, _r: f64, depth: usize) -> f64 {
        let half = target / 2;
        let dist = if new_sum > half { new_sum - half } else { half - new_sum };
        // Prefer states near target/2 in early search; later, prefer
        // states near target.
        let weight = if depth < 8 { 1.0 } else { 0.4 };
        weight * (dist as f64 / max_v.max(1) as f64)
            + 0.6 * (target.saturating_sub(new_sum) as f64 / max_v.max(1) as f64)
    }
}

struct DifferenceAxis;
impl Axis for DifferenceAxis {
    fn name(&self) -> &'static str { "PMAS-Difference" }
    fn score(&self, new_sum: u128, target: u128, max_v: u128, _b: u128, _e: u128, _r: f64, _d: usize) -> f64 {
        let diff = if new_sum > target { new_sum - target } else { target - new_sum };
        diff as f64 / max_v.max(1) as f64
    }
}

struct BitAxis;
impl Axis for BitAxis {
    fn name(&self) -> &'static str { "PMAS-Bit" }
    fn score(&self, new_sum: u128, target: u128, max_v: u128, target_bits: u128, _e: u128, _r: f64, _d: usize) -> f64 {
        // Hamming distance from current sum's bit pattern to the
        // target's bit pattern. Lower is better.
        let xor = new_sum ^ target;
        let hd = xor.count_ones() as f64;
        let scalar = (target.saturating_sub(new_sum)) as f64 / max_v.max(1) as f64;
        // Combine bit alignment (cheap) with scalar distance.
        let _ = target_bits;
        0.6 * scalar + 0.4 * (hd / 128.0)
    }
}

struct RedundancyAxis;
impl Axis for RedundancyAxis {
    fn name(&self) -> &'static str { "PMAS-Redundancy" }
    fn score(&self, new_sum: u128, target: u128, max_v: u128, _b: u128, _e: u128, rarity: f64, _d: usize) -> f64 {
        let scalar = target.saturating_sub(new_sum) as f64 / max_v.max(1) as f64;
        // Lower score = better.  Rarity ∈ [0,1]: 0 means common,
        // 1 means unique element.  Rare elements get bonus.
        scalar - 0.25 * rarity
    }
}

fn run_axis(sh: &Shared, axis: &dyn Axis) {
    let p = &sh.profile;
    if !p.u128_safe() || p.n == 0 {
        return;
    }
    let target = p.target_u128();
    let nums = p.numbers_u128();
    let max_v = nums.iter().copied().max().unwrap_or(1);
    let target_bits = target.count_ones() as u128;

    // Element rarity: 1.0 if value appears once; lower otherwise.
    let mut counts = std::collections::HashMap::<u128, u32>::new();
    for &v in &nums {
        *counts.entry(v).or_insert(0) += 1;
    }
    let max_count = counts.values().copied().max().unwrap_or(1) as f64;
    let rarity: Vec<f64> = nums
        .iter()
        .map(|v| 1.0 - (*counts.get(v).unwrap_or(&1) as f64 - 1.0) / max_count)
        .collect();

    let mut beam: Vec<State> = vec![State { sum: 0, idx: Vec::new() }];
    let mut visited: HashSet<u128> = HashSet::with_capacity(BEAM_WIDTH * 4);

    for depth in 0..MAX_DEPTH.min(p.n) {
        if sh.stopped() || beam.is_empty() {
            return;
        }
        let mut cands: Vec<(f64, State, u128)> = Vec::with_capacity(beam.len() * 6);
        for st in &beam {
            if sh.stopped() {
                return;
            }
            let used: HashSet<u32> = st.idx.iter().copied().collect();
            let rem = target.saturating_sub(st.sum);
            if rem == 0 {
                continue;
            }
            for i in 0..nums.len() {
                let i_u32 = i as u32;
                if used.contains(&i_u32) {
                    continue;
                }
                let v = nums[i];
                if v > rem {
                    continue;
                }
                let new_sum = st.sum + v;
                if new_sum == target {
                    let mut sol: Vec<BigUint> = st
                        .idx
                        .iter()
                        .map(|&j| BigUint::from(nums[j as usize]))
                        .collect();
                    sol.push(BigUint::from(v));
                    sh.report(sol, axis.name());
                    return;
                }
                let key = canon_key(&st.idx, i_u32);
                if visited.contains(&key) {
                    continue;
                }
                let s = axis.score(new_sum, target, max_v, target_bits, v, rarity[i], depth);
                let mut new_idx = st.idx.clone();
                new_idx.push(i_u32);
                cands.push((s, State { sum: new_sum, idx: new_idx }, key));
            }
        }
        if cands.is_empty() {
            return;
        }
        cands.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
        cands.truncate(BEAM_WIDTH);
        let mut new_beam = Vec::with_capacity(cands.len());
        for (_s, st, k) in cands {
            if visited.insert(k) {
                new_beam.push(st);
            }
        }
        beam = new_beam;
    }
}

fn canon_key(idx: &[u32], extra: u32) -> u128 {
    let mut joined: Vec<u32> = idx.to_vec();
    joined.push(extra);
    joined.sort_unstable();
    let mut h: u128 = 0xcbf29ce484222325;
    for v in joined {
        h ^= v as u128;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

impl Engine for PmasBalance {
    fn name(&self) -> &'static str { "PMAS-Balance" }
    fn run(&self, sh: &Shared) { run_axis(sh, &BalanceAxis); }
}
impl Engine for PmasDifference {
    fn name(&self) -> &'static str { "PMAS-Difference" }
    fn run(&self, sh: &Shared) { run_axis(sh, &DifferenceAxis); }
}
impl Engine for PmasBit {
    fn name(&self) -> &'static str { "PMAS-Bit" }
    fn run(&self, sh: &Shared) { run_axis(sh, &BitAxis); }
}
impl Engine for PmasRedundancy {
    fn name(&self) -> &'static str { "PMAS-Redundancy" }
    fn run(&self, sh: &Shared) { run_axis(sh, &RedundancyAxis); }
}
