//! Input structure detection.
//!
//! Reference: `Subset sum algorithm.md` lines 8495 ("Structure
//! Detection"), 21829 (clusters / gaps / dominance).
//!
//! When the algorithm can recognise that the input has special
//! structure (arithmetic progression, geometric, dense cluster,
//! dominance chain) it can switch to a specialised engine instead
//! of running the heavy general-purpose ones.  This is a real
//! source of practical speedup — the difference between solving
//! `[1, 2, 4, 8, 16, ...]` in O(n) versus O(2^(n/2)) MITM.

use num_bigint::BigUint;
use num_traits::{ToPrimitive, Zero};

#[derive(Debug, Clone)]
pub struct StructureInfo {
    pub is_arithmetic: bool,
    pub arithmetic_diff: Option<BigUint>,
    pub is_geometric: bool,
    pub geometric_ratio: Option<f64>,
    pub clusters: Vec<u128>,
    pub max_gap_ratio: f64,
    pub dominance_chain_len: usize,
    pub all_distinct: bool,
}

impl StructureInfo {
    pub fn detect(numbers: &[BigUint]) -> Self {
        let n = numbers.len();
        if n < 3 {
            return Self::trivial(numbers);
        }

        let mut sorted = numbers.to_vec();
        sorted.sort();

        // Arithmetic progression test
        let (is_arithmetic, ap_diff) = is_arithmetic_progression(&sorted);

        // Geometric (only attempt on u128-safe inputs)
        let (is_geometric, geo_ratio) = is_geometric_progression(&sorted);

        // Clusters (k=8) — uses u128 fast path when safe
        let clusters = cluster_centers(&sorted, 8);

        // Largest relative gap
        let max_gap_ratio = largest_gap_ratio(&sorted);

        // Dominance chain: how long is the longest sequence
        // a_{i+1} > sum(a_0..a_i)?
        let dominance_chain_len = dominance_chain(&sorted);

        // Distinctness
        let mut distinct = true;
        for i in 1..sorted.len() {
            if sorted[i] == sorted[i - 1] {
                distinct = false;
                break;
            }
        }

        Self {
            is_arithmetic,
            arithmetic_diff: ap_diff,
            is_geometric,
            geometric_ratio: geo_ratio,
            clusters,
            max_gap_ratio,
            dominance_chain_len,
            all_distinct: distinct,
        }
    }

    fn trivial(_numbers: &[BigUint]) -> Self {
        Self {
            is_arithmetic: false,
            arithmetic_diff: None,
            is_geometric: false,
            geometric_ratio: None,
            clusters: Vec::new(),
            max_gap_ratio: 0.0,
            dominance_chain_len: 0,
            all_distinct: true,
        }
    }

    /// "super increasing" if every element exceeds the sum of all
    /// smaller elements — implies trivial polynomial-time solving.
    pub fn is_super_increasing(&self, n: usize) -> bool {
        n >= 3 && self.dominance_chain_len == n
    }
}

fn is_arithmetic_progression(sorted: &[BigUint]) -> (bool, Option<BigUint>) {
    if sorted.len() < 3 {
        return (false, None);
    }
    let d = if sorted[1] >= sorted[0] {
        &sorted[1] - &sorted[0]
    } else {
        return (false, None);
    };
    if d.is_zero() {
        return (false, None);
    }
    for i in 2..sorted.len() {
        let cur_d = if sorted[i] >= sorted[i - 1] {
            &sorted[i] - &sorted[i - 1]
        } else {
            return (false, None);
        };
        if cur_d != d {
            return (false, None);
        }
    }
    (true, Some(d))
}

fn is_geometric_progression(sorted: &[BigUint]) -> (bool, Option<f64>) {
    if sorted.len() < 4 {
        return (false, None);
    }
    let a = match sorted[0].to_f64() {
        Some(v) if v > 0.0 => v,
        _ => return (false, None),
    };
    let b = match sorted[1].to_f64() {
        Some(v) if v > 0.0 => v,
        _ => return (false, None),
    };
    let r = b / a;
    if r <= 1.0 || !r.is_finite() {
        return (false, None);
    }
    let mut prev = b;
    for x in &sorted[2..] {
        let v = match x.to_f64() {
            Some(v) if v > 0.0 => v,
            _ => return (false, None),
        };
        let cur_r = v / prev;
        if (cur_r - r).abs() > r * 0.01 {
            return (false, None);
        }
        prev = v;
    }
    (true, Some(r))
}

fn cluster_centers(sorted: &[BigUint], k: usize) -> Vec<u128> {
    if sorted.is_empty() || k == 0 {
        return Vec::new();
    }
    let n = sorted.len();
    let step = (n + k - 1) / k;
    let mut out = Vec::with_capacity(k);
    for i in 0..k {
        let lo = i * step;
        let hi = ((i + 1) * step).min(n);
        if lo >= hi {
            break;
        }
        let chunk: BigUint = sorted[lo..hi].iter().sum::<BigUint>()
            / BigUint::from((hi - lo) as u32);
        if let Some(c) = chunk.to_u128() {
            out.push(c);
        }
    }
    out
}

fn largest_gap_ratio(sorted: &[BigUint]) -> f64 {
    if sorted.len() < 2 {
        return 0.0;
    }
    let total = match sorted.iter().sum::<BigUint>().to_f64() {
        Some(v) if v > 0.0 => v,
        _ => return 0.0,
    };
    let mut max_gap = 0.0;
    for i in 1..sorted.len() {
        if sorted[i] > sorted[i - 1] {
            let gap = (&sorted[i] - &sorted[i - 1]).to_f64().unwrap_or(0.0);
            if gap > max_gap {
                max_gap = gap;
            }
        }
    }
    max_gap / total
}

fn dominance_chain(sorted: &[BigUint]) -> usize {
    if sorted.is_empty() {
        return 0;
    }
    let mut chain = 1usize;
    let mut acc = sorted[0].clone();
    for i in 1..sorted.len() {
        if sorted[i] > acc {
            chain += 1;
            acc += &sorted[i];
        } else {
            break;
        }
    }
    chain
}

/// GCD of all elements; if the target is not divisible by it, the
/// instance is provably impossible.
pub fn gcd_of_all(numbers: &[BigUint]) -> BigUint {
    use num_integer::Integer;
    if numbers.is_empty() {
        return BigUint::from(0u32);
    }
    let mut g = numbers[0].clone();
    for x in &numbers[1..] {
        g = g.gcd(x);
        if g == BigUint::from(1u32) {
            return g;
        }
    }
    g
}
