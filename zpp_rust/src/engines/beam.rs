//! Beam Search with Self-Reflective Pruning (SRP).
//!
//! Reference: `Subset sum algorithm.md` lines 10108 (beam search),
//! 12057 (SRP), 14316 (controlled exploration).
//!
//! Beam search keeps the K most promising partial states alive at
//! each depth.  GDVS scoring decides which states are "promising".
//!
//! When a partial state cannot be extended to the goal, we capture
//! the *minimal failing combination* of element indices and store
//! it on the shared lock-free conflict map.  Future expansions that
//! would re-visit that combination are pruned instantly.  This is
//! exactly your **Self-Reflective Pruning** idea: the algorithm
//! learns from each failure and applies the lesson globally.

use num_bigint::BigUint;
use num_traits::ToPrimitive;
use std::collections::HashSet;

use crate::controller::{Engine, Shared};
use crate::gdvs;

pub struct BeamEngine;

const BEAM_WIDTH: usize = 256;
const MAX_DEPTH: usize = 200;

#[derive(Clone)]
struct State {
    sum: u128,
    idx: Vec<u32>,
}

impl Engine for BeamEngine {
    fn name(&self) -> &'static str {
        "Beam-SRP"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if !p.u128_safe() || p.n == 0 {
            return;
        }
        let target = p.target_u128();
        let nums = p.numbers_u128();
        let max_v = nums.iter().max().copied().unwrap_or(1);
        let centers = gdvs::compute_clusters(&nums, 8);

        let mut beam: Vec<State> = vec![State {
            sum: 0,
            idx: Vec::new(),
        }];
        let mut visited: HashSet<u128> = HashSet::with_capacity(BEAM_WIDTH * 4);

        for _depth in 0..MAX_DEPTH.min(p.n) {
            if sh.stopped() || beam.is_empty() {
                return;
            }

            let mut cands: Vec<(f64, State, u128)> = Vec::with_capacity(beam.len() * 8);
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
                        let mut chosen: Vec<BigUint> = st
                            .idx
                            .iter()
                            .map(|&j| BigUint::from(nums[j as usize]))
                            .collect();
                        chosen.push(BigUint::from(v));
                        sh.report(chosen, "Beam-SRP");
                        return;
                    }
                    let key = canon_key(&st.idx, i_u32);
                    if visited.contains(&key) {
                        continue;
                    }
                    if conflicts(sh, &st.idx, i_u32) {
                        continue;
                    }
                    let score = gdvs::gdvs(new_sum, target, st.idx.len() + 1, max_v, &centers).norm();
                    let mut new_idx = st.idx.clone();
                    new_idx.push(i_u32);
                    cands.push((
                        score,
                        State {
                            sum: new_sum,
                            idx: new_idx,
                        },
                        key,
                    ));
                }
            }

            if cands.is_empty() {
                // SRP — every state in the beam dead-ended. Record
                // the *shortest* failed combination as a conflict.
                if let Some(shortest) = beam.iter().min_by_key(|s| s.idx.len()) {
                    record_conflict(sh, &shortest.idx);
                }
                return;
            }

            cands.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
            cands.truncate(BEAM_WIDTH);

            let mut new_beam: Vec<State> = Vec::with_capacity(cands.len());
            for (_score, st, key) in cands {
                if visited.insert(key) {
                    new_beam.push(st);
                }
            }
            beam = new_beam;
        }

        // We exhausted MAX_DEPTH. Treat the final beam as failed
        // states and record them for SRP.
        for st in beam.iter().take(16) {
            record_conflict(sh, &st.idx);
        }
    }
}

#[inline]
fn canon_key(idx: &[u32], extra: u32) -> u128 {
    // Cheap hash combining the sorted bag of indices.
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

fn record_conflict(sh: &Shared, idx: &[u32]) {
    if idx.is_empty() {
        return;
    }
    // Record up to the last 4 indices as the "conflict core" — small
    // to keep the conflict map cheap to query.
    let core = &idx[idx.len().saturating_sub(4)..];
    let mut k = core.to_vec();
    k.sort_unstable();
    let big = nat_to_biguint_from_u32_seq(&k);
    sh.note_sum(big);
}

fn conflicts(sh: &Shared, idx: &[u32], extra: u32) -> bool {
    let mut combined: Vec<u32> = idx.to_vec();
    combined.push(extra);
    combined.sort_unstable();
    if combined.len() < 2 {
        return false;
    }
    let core = &combined[combined.len() - combined.len().min(4)..];
    let big = nat_to_biguint_from_u32_seq(core);
    sh.blackboard.contains_key(&big)
}

fn nat_to_biguint_from_u32_seq(seq: &[u32]) -> BigUint {
    let mut s = BigUint::from(0u32);
    let base = BigUint::from(1u64 << 32);
    for &v in seq {
        s *= &base;
        s += BigUint::from(v);
    }
    s
}
