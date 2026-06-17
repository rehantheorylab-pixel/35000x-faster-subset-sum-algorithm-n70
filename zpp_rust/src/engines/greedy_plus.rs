use num_bigint::BigUint;
use num_traits::Zero;

use crate::controller::{Engine, Shared};

/// Multi-strategy greedy engine.
///
/// Runs 4 linear-time greedy strategies in order.  Any one may find
/// a solution — many structured instances (exponential, super-increasing,
/// clustered, etc.) yield to at least one variant.
///
/// Strategies (all O(n log n) sorting + O(n) scan):
///   1. Largest-first  — classic greedy, take if ≤ remaining
///   2. Smallest-first — build up from smallest values
///   3. Reverse        — smallest-first but process in ascending order
///   4. Skip-one       — for each element, try greedy skipping it
pub struct GreedyPlus;

impl Engine for GreedyPlus {
    fn name(&self) -> &'static str {
        "GreedyPlus"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if p.n < 2 || p.target.is_zero() {
            return;
        }

        // Sorted ascending
        let mut sorted: Vec<BigUint> = p.numbers.clone();
        sorted.sort();

        // Strategy 1: Largest-first
        if sh.stopped() { return; }
        if let Some(sol) = greedy_largest_first(&sorted, &p.target) {
            sh.report(sol, "GreedyPlus-LF");
            return;
        }

        // Strategy 2: Smallest-first (take elements from smallest up)
        if sh.stopped() { return; }
        if let Some(sol) = greedy_smallest_first(&sorted, &p.target) {
            sh.report(sol, "GreedyPlus-SF");
            return;
        }

        // Strategy 3: Reverse greedy (ascending but pick from the end of eligibility)
        if sh.stopped() { return; }
        if let Some(sol) = greedy_reverse(&sorted, &p.target) {
            sh.report(sol, "GreedyPlus-RV");
            return;
        }

        // Strategy 4: Skip-one (for each element, skip it, then greedy)
        if p.n <= 32 && !sh.stopped() {
            for skip in 0..sorted.len() {
                if sh.stopped() { return; }
                let filtered: Vec<BigUint> = sorted
                    .iter()
                    .enumerate()
                    .filter(|(i, _)| *i != skip)
                    .map(|(_, v)| v.clone())
                    .collect();
                if let Some(sol) = greedy_largest_first(&filtered, &p.target) {
                    sh.report(sol, "GreedyPlus-Skip");
                    return;
                }
            }
        }
    }
}

fn greedy_largest_first(sorted: &[BigUint], target: &BigUint) -> Option<Vec<BigUint>> {
    let mut remaining = target.clone();
    let mut chosen = Vec::new();
    for x in sorted.iter().rev() {
        if x <= &remaining {
            chosen.push(x.clone());
            remaining -= x;
            if remaining.is_zero() {
                return Some(chosen);
            }
        }
    }
    None
}

fn greedy_smallest_first(sorted: &[BigUint], target: &BigUint) -> Option<Vec<BigUint>> {
    let mut remaining = target.clone();
    let mut chosen = Vec::new();
    for x in sorted.iter() {
        if x <= &remaining {
            chosen.push(x.clone());
            remaining -= x;
            if remaining.is_zero() {
                return Some(chosen);
            }
        }
    }
    None
}

fn greedy_reverse(sorted: &[BigUint], target: &BigUint) -> Option<Vec<BigUint>> {
    // Pick from ascending, but scan from the END of eligibility.
    // For each step, find the largest element ≤ remaining, take it.
    let mut remaining = target.clone();
    let mut chosen: Vec<BigUint> = Vec::new();
    let mut available = sorted.to_vec();

    while !available.is_empty() {
        let mut found = false;
        for j in (0..available.len()).rev() {
            if &available[j] <= &remaining {
                chosen.push(available[j].clone());
                remaining -= &available[j];
                available.swap_remove(j);
                found = true;
                if remaining.is_zero() {
                    return Some(chosen);
                }
                break;
            }
        }
        if !found {
            break;
        }
    }
    None
}
