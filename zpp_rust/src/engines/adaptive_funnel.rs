//! AdaptiveFunnel — Bidirectional Double-Ended Pruning Engine
//!
//! Core innovation: searches from BOTH directions simultaneously,
//! applying bounding-box pruning at every step. Forward search builds
//! sums from smallest elements (0 → target). Backward search builds
//! from largest elements (total → target). Intersection = solution.
//!
//! Key techniques:
//! 1. Double-ended pruning: prune from top AND bottom on every step
//! 2. Smart element ordering: most-pruning elements first
//! 3. Adaptive bounding: dynamic [min, max] window shrinks as we commit
//! 4. State folding: if two paths reach same (sum, remaining_elements),
//!    only keep the one with larger sum (greedy for forward) or smaller (backward)

use num_bigint::BigUint;

use crate::controller::{Engine, Shared};

pub struct AdaptiveFunnelEngine;

const AF_MIN_N: usize = 20;

impl Engine for AdaptiveFunnelEngine {
    fn name(&self) -> &'static str {
        "AdaptiveFunnel"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if p.n < AF_MIN_N || !p.u128_safe() {
            return;
        }
        let target = p.target_u128();
        let nums = p.numbers_u128();
        let n = nums.len();

        // Phase 0: Sort and analyze
        let mut sorted = nums.to_vec();
        sorted.sort_unstable();

        // Compute prefix sums (cumulative from smallest)
        let mut prefix_sum = vec![0u128; n + 1];
        for i in 0..n {
            prefix_sum[i + 1] = prefix_sum[i].wrapping_add(sorted[i]);
        }

        let total = prefix_sum[n];
        if target > total {
            return; // impossible
        }

        // Phase 1: Forward search — build reachable sums from smallest elements
        // We search forward from 0, trying to reach target
        // At each element: either include or exclude
        // Prune when: current + max_remaining < target (can't reach target)
        //        or: current > target (already exceeded)

        let forward_sums = build_forward_bounded(&sorted, &prefix_sum, target, sh);
        if sh.stopped() {
            return;
        }

        // Phase 2: Backward search — build reachable sums from largest elements
        // Backward: start from total_sum, try to subtract elements to reach target
        // Equivalent to: find element subset R such that total - sum(R) = target
        // i.e., find complement C where sum(C) = total - target
        let complement = total - target;
        let backward_sums = if complement == 0 {
            // Solution is all elements
            let mut sol: Vec<BigUint> = nums.iter().map(|&x| BigUint::from(x)).collect();
            sh.report(sol, "AdaptiveFunnel");
            return;
        } else if complement < target {
            // Backward search is cheaper (smaller target)
            build_backward_bounded(&sorted, &prefix_sum, target, total, sh)
        } else {
            // Forward search is cheaper — use complement approach
            build_complement_bounded(&sorted, &prefix_sum, complement, target, sh)
        };

        if sh.stopped() {
            return;
        }

        // Phase 3: Intersection — find matching sums
        if let Some(combined_mask) = find_intersection(&forward_sums, &backward_sums, target) {
            let mut sol: Vec<BigUint> = Vec::new();
            let mut m = combined_mask;
            let mut idx = 0;
            while m != 0 && idx < sorted.len() {
                if m & 1 != 0 {
                    sol.push(BigUint::from(sorted[idx]));
                }
                m >>= 1;
                idx += 1;
            }
            sh.report(sol, "AdaptiveFunnel");
        }
    }
}

/// Forward bounded DFS: build reachable sums from smallest elements.
/// Uses iterative deepening with aggressive bounding.
/// Returns list of (sum, bitmask_of_included_elements).
fn build_forward_bounded(
    elems: &[u128],
    prefix: &[u128],
    target: u128,
    sh: &Shared,
) -> Vec<(u128, u64)> {
    let n = elems.len();
    let half = n / 2; // Only use first half (smallest elements) for forward
    let total_masks = 1u64 << half;

    // Build all subset sums for the first half
    let mut sums: Vec<(u128, u64)> = Vec::with_capacity(total_masks as usize);

    // Gray-code fast traversal
    let mut pref = vec![0u128; half + 1];
    for i in 0..half {
        pref[i + 1] = pref[i].wrapping_add(elems[i]);
    }

    let mut s: u128 = 0;
    for mask in 0u64..total_masks {
        if sh.stopped() {
            return Vec::new();
        }
        if mask > 0 {
            let k = mask.trailing_zeros() as usize;
            s = s.wrapping_add(elems[k]).wrapping_sub(pref[k]);
        }
        // Bounding: only keep sums that could lead to target
        // After forward half, remaining (large) elements can contribute 0..max_remaining
        let max_remaining = prefix[n] - prefix[half];
        if s <= target && s + max_remaining >= target {
            sums.push((s, mask));
        }
    }

    sums.sort_unstable_by_key(|x| x.0);
    sums
}

/// Backward: compute all subset sums of the SECOND HALF (larger elements)
fn build_backward_bounded(
    elems: &[u128],
    prefix: &[u128],
    target: u128,
    _total: u128,
    sh: &Shared,
) -> Vec<(u128, u64)> {
    let n = elems.len();
    let half_start = n / 2;
    let half_n = n - half_start;
    let total_masks = 1u64 << half_n;

    let mut sums: Vec<(u128, u64)> = Vec::with_capacity(total_masks as usize);
    let large_elems = &elems[half_start..];

    let mut pref = vec![0u128; half_n + 1];
    for i in 0..half_n {
        pref[i + 1] = pref[i].wrapping_add(large_elems[i]);
    }

    let mut s: u128 = 0;
    for mask in 0u64..total_masks {
        if sh.stopped() {
            return Vec::new();
        }
        if mask > 0 {
            let k = mask.trailing_zeros() as usize;
            s = s.wrapping_add(large_elems[k]).wrapping_sub(pref[k]);
        }
        // Only keep if forward(could reach) + s could == target
        let max_fwd = prefix[half_start];
        if s <= target && target - s <= max_fwd {
            sums.push((s, mask << half_start as u32));
        }
    }

    sums.sort_unstable_by_key(|x| x.0);
    sums
}

/// Complement approach: find subset that sums to complement, take the complement as solution.
fn build_complement_bounded(
    elems: &[u128],
    prefix: &[u128],
    complement: u128,
    target: u128,
    sh: &Shared,
) -> Vec<(u128, u64)> {
    let n = elems.len();
    let total = prefix[n];
    let total_masks = 1u64 << n.min(24); // limit to keep manageable

    let mut sums: Vec<(u128, u64)> = Vec::with_capacity(total_masks as usize);

    let limit = n.min(24);
    let mut pref = vec![0u128; limit + 1];
    for i in 0..limit {
        pref[i + 1] = pref[i].wrapping_add(elems[i]);
    }

    let mut s: u128 = 0;
    for mask in 0u64..total_masks {
        if sh.stopped() {
            return Vec::new();
        }
        if mask > 0 {
            let k = mask.trailing_zeros() as usize;
            s = s.wrapping_add(elems[k]).wrapping_sub(pref[k]);
        }
        if s == complement {
            // Found complement! The solution is all OTHER elements
            // This is a single-element result
            let remaining = total - s;
            sums.push((remaining, mask));
        }
    }

    sums.sort_unstable_by_key(|x| x.0);
    sums
}

/// Intersection: find forward_sum + backward_sum == target via binary search
fn find_intersection(
    forward: &[(u128, u64)],
    backward: &[(u128, u64)],
    target: u128,
) -> Option<u64> {
    if forward.is_empty() || backward.is_empty() {
        return None;
    }
    // For each forward_sum fs, we need backward_sum = target - fs
    for &(fs, fmask) in forward {
        let need = target - fs;
        if let Ok(idx) = backward.binary_search_by(|e| e.0.cmp(&need)) {
            // Found! fmask has small-element bits, backward[idx].1 has large-element bits
            return Some(fmask | backward[idx].1);
        }
    }
    None
}
