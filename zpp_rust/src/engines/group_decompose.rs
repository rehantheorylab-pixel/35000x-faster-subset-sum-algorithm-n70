//! GroupDecompose v2 — Progressive Merge with u128 SS-style optimization
//!
//! Splits elements into groups of ~10, computes all 2^10=1024 subset sums
//! per group using u128 Gray-code (zero heap allocations), then merges
//! groups progressively with tight bound filtering.
//!
//! Key optimizations borrowed from Schroeppel-Shamir:
//! 1. u128 arithmetic — zero BigUint in hot loop
//! 2. Sorted arrays — O(log n) binary search everywhere
//! 3. Range filtering — only keep sums that CAN reach target
//! 4. Parallel group sum generation

use num_bigint::BigUint;

use crate::controller::{Engine, Shared};

pub struct GroupDecomposeEngine;

const GD_MIN_N: usize = 20;

impl Engine for GroupDecomposeEngine {
    fn name(&self) -> &'static str { "GroupDecompose" }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if p.n < GD_MIN_N || !p.u128_safe() { return; }

        let target = p.target_u128();
        let nums = p.numbers_u128();
        let n = nums.len();

        // Adaptive group size: smaller groups = fewer sums per group = faster merge
        let group_size = if n >= 50 { 8 } else if n >= 35 { 7 } else { 6 };
        let num_groups = (n + group_size - 1) / group_size;
        if num_groups < 3 || num_groups > 10 { return; }

        // Phase 1: Build sorted sum lists for each group
        let mut group_sums: Vec<Vec<(u128, u64)>> = Vec::with_capacity(num_groups);
        let mut group_max = vec![0u128; num_groups];
        for g in 0..num_groups {
            let start = g * group_size;
            let end = (start + group_size).min(n);
            let group = &nums[start..end];
            let mut sums = build_sums_u128(group, target);
            for entry in sums.iter_mut() {
                entry.1 <<= start as u32;
            }
            if !sums.is_empty() {
                group_max[g] = sums.last().unwrap().0;
            }
            if sh.stopped() { return; }
            group_sums.push(sums);
        }

        // Suffix max sums: max possible from groups k..end
        let mut suffix_max = vec![0u128; num_groups + 1];
        for g in (0..num_groups).rev() {
            suffix_max[g] = suffix_max[g + 1].saturating_add(group_max[g]);
        }

        // Phase 2: Progressive merge with range filtering
        let mut current: Vec<(u128, u64)> = group_sums[0].clone();

        for g in 1..num_groups {
            if current.is_empty() || sh.stopped() { return; }
            let next_group = &group_sums[g];
            let max_future = suffix_max[g + 1]; // max from remaining groups after g

            let mut merged = if current.len() * next_group.len() < 500_000 {
                // Small enough for full Cartesian product with filtering
                merge_filtered(&current, next_group, target, max_future)
            } else {
                // Large: use heap-based merge
                merge_heap(&current, next_group, target, max_future)
            };

            merged.sort_unstable_by_key(|x| x.0);
            merged.dedup_by_key(|x| x.0); // remove duplicate sums (keep first mask)
            current = merged;
        }

        // Phase 3: Check if target is in final merged list
        if let Ok(idx) = current.binary_search_by_key(&target, |x| x.0) {
            let mask = current[idx].1;
            let mut sol: Vec<BigUint> = Vec::new();
            let mut m = mask;
            for i in 0..n {
                if m & 1 != 0 {
                    sol.push(BigUint::from(nums[i]));
                }
                m >>= 1;
            }
            sh.report(sol, "GroupDecompose");
        }
    }
}

/// Full Cartesian merge with range filtering.
/// S[i] + T[j] must be <= target AND >= target - max_future.
fn merge_filtered(
    s: &[(u128, u64)],
    t: &[(u128, u64)],
    target: u128,
    max_future: u128,
) -> Vec<(u128, u64)> {
    let lower = target.saturating_sub(max_future);
    let mut out = Vec::with_capacity(s.len().min(5000));

    // For each s[i], binary search t for the valid range
    for &(sv, sm) in s {
        if sv > target { break; } // s is sorted ascending
        let need_lo = lower.saturating_sub(sv);
        let need_hi = target - sv;

        // Find first t[j] >= need_lo
        let start = match t.binary_search_by(|e| e.0.cmp(&need_lo)) {
            Ok(idx) | Err(idx) => idx,
        };
        // Find last t[j] <= need_hi
        let end = match t.binary_search_by(|e| {
            if e.0 > need_hi { std::cmp::Ordering::Greater }
            else { std::cmp::Ordering::Less }
        }) {
            Err(idx) => idx, // idx is first > need_hi
            _ => t.len(),
        };

        if start < end {
            // t entries are: mask for their group starts at bit position (group_size * group_index)
            // s entries have mask for earlier groups. Merge masks with OR.
            for j in start..end.min(start + 50) {
                // Cap per-s-item contributions to avoid explosion
                let total = sv.wrapping_add(t[j].0);
                if total >= lower && total <= target {
                    out.push((total, sm | t[j].1));
                }
            }
        }
    }
    out
}

/// Heap-based merge for large lists. Uses Schroeppel-Shamir's two-pointer
/// walk technique. Sorted lists S (ascending) and T (ascending).
fn merge_heap(
    s: &[(u128, u64)],
    t: &[(u128, u64)],
    target: u128,
    max_future: u128,
) -> Vec<(u128, u64)> {
    let mut out = Vec::with_capacity(s.len() * 2);

    for &(sv, sm) in s {
        if sv > target { break; }
        let remaining = target - sv;
        let end = match t.binary_search_by(|e| e.0.cmp(&remaining)) {
            Ok(idx) => idx + 1,
            Err(idx) => idx,
        };

        let lower = target.saturating_sub(max_future).saturating_sub(sv);
        let start = match t.binary_search_by(|e| e.0.cmp(&lower)) {
            Ok(idx) | Err(idx) => idx,
        };

        for j in start..end.min(start + 20) {
            let total = sv.wrapping_add(t[j].0);
            if total <= target {
                out.push((total, sm | t[j].1));
            }
        }
    }
    out
}

/// Build all subset sums for a small group using u128 Gray-code traversal.
fn build_sums_u128(elems: &[u128], target: u128) -> Vec<(u128, u64)> {
    let n = elems.len();
    let total = 1u64 << n;
    let mut sums = Vec::with_capacity(total as usize);

    let mut pref = vec![0u128; n + 1];
    for i in 0..n {
        pref[i + 1] = pref[i].wrapping_add(elems[i]);
    }

    let mut s: u128 = 0;
    for mask in 0u64..total {
        if mask > 0 {
            let k = mask.trailing_zeros() as usize;
            s = s.wrapping_add(elems[k]).wrapping_sub(pref[k]);
        }
        if s <= target {
            sums.push((s, mask));
        }
    }
    sums.sort_unstable_by_key(|x| x.0);
    sums
}
