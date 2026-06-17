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

/// Value distribution category — guides engine selection.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ValDist {
    Uniform,
    Spread,
    Clustered,
    Exponential,
    Bimodal,
    DenseSmall,
}

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
    pub val_dist: ValDist,
    pub redundancy_ratio: f64,
    pub log_range: f64,
    pub median_bitlen: f64,
    /// True when gap-based decomposition is possible
    pub has_gap_split: bool,
    /// 0.0–1.0 — how likely linear-time engines (greedy, pruner) will solve it
    pub linear_favorable: f64,
}

impl StructureInfo {
    pub fn detect(numbers: &[BigUint]) -> Self {
        let n = numbers.len();
        if n < 3 {
            return Self::trivial(numbers);
        }

        let mut sorted = numbers.to_vec();
        sorted.sort();

        let (is_arithmetic, ap_diff) = is_arithmetic_progression(&sorted);
        let (is_geometric, geo_ratio) = is_geometric_progression(&sorted);
        let clusters = cluster_centers(&sorted, 8);
        let max_gap_ratio = largest_gap_ratio(&sorted);
        let dominance_chain_len = dominance_chain(&sorted);
        let has_gap_split = detect_gap_split(&sorted, max_gap_ratio);

        let mut distinct = true;
        let mut dups = 0usize;
        for i in 1..sorted.len() {
            if sorted[i] == sorted[i - 1] {
                distinct = false;
                dups += 1;
            }
        }
        let redundancy_ratio = if n > 1 { dups as f64 / n as f64 } else { 0.0 };

        let bitlens: Vec<f64> = sorted.iter().map(|x| x.bits() as f64).collect();
        let median_bitlen = median(&bitlens);
        let min_bl = bitlens.first().copied().unwrap_or(0.0);
        let max_bl = bitlens.last().copied().unwrap_or(0.0);
        let log_range = if min_bl > 0.0 { max_bl / min_bl } else { 1.0 };

        let val_dist = classify_distribution(&sorted, &bitlens, max_gap_ratio, dominance_chain_len, n);
        let linear_favorable = compute_linear_favorable(
            val_dist, has_gap_split, dominance_chain_len, max_gap_ratio, n, redundancy_ratio,
        );

        Self {
            is_arithmetic,
            arithmetic_diff: ap_diff,
            is_geometric,
            geometric_ratio: geo_ratio,
            clusters,
            max_gap_ratio,
            dominance_chain_len,
            all_distinct: distinct,
            val_dist,
            redundancy_ratio,
            log_range,
            median_bitlen,
            has_gap_split,
            linear_favorable,
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
            val_dist: ValDist::Uniform,
            redundancy_ratio: 0.0,
            log_range: 1.0,
            median_bitlen: 0.0,
            has_gap_split: false,
            linear_favorable: 0.0,
        }
    }

    pub fn is_super_increasing(&self, n: usize) -> bool {
        n >= 3 && self.dominance_chain_len == n
    }
}

fn median(v: &[f64]) -> f64 {
    if v.is_empty() { return 0.0; }
    let mid = v.len() / 2;
    if v.len() % 2 == 0 { (v[mid - 1] + v[mid]) / 2.0 } else { v[mid] }
}

fn classify_distribution(
    sorted: &[BigUint], bitlens: &[f64],
    max_gap_ratio: f64, dominance_chain_len: usize, n: usize,
) -> ValDist {
    if n >= 3 && dominance_chain_len == n {
        return ValDist::Exponential;
    }
    if max_gap_ratio > 0.4 {
        return ValDist::Spread;
    }
    if !sorted.is_empty() {
        let total_bits = bitlens.iter().sum::<f64>();
        let avg = total_bits / n as f64;
        if avg <= 12.0 && n >= 20 {
            return ValDist::DenseSmall;
        }
    }
    if is_bimodal(sorted) {
        return ValDist::Bimodal;
    }
    if has_clusters(sorted, 8) {
        return ValDist::Clustered;
    }
    ValDist::Uniform
}

fn is_bimodal(sorted: &[BigUint]) -> bool {
    if sorted.len() < 8 { return false; }
    let halves = sorted.len() / 2;
    let first_half: BigUint = sorted[..halves].iter().sum();
    let second_half: BigUint = sorted[halves..].iter().sum();
    if first_half.is_zero() || second_half.is_zero() { return false; }
    let ratio = second_half.to_f64().unwrap_or(0.0) / first_half.to_f64().unwrap_or(1.0);
    ratio > 8.0
}

fn has_clusters(sorted: &[BigUint], k: usize) -> bool {
    if sorted.len() < k * 2 { return false; }
    let step = sorted.len() / k;
    let mut gaps_big = 0usize;
    for i in 1..k {
        let idx = i * step;
        if idx < sorted.len() {
            let gap = &sorted[idx] - &sorted[idx - 1];
            if let Some(g) = gap.to_f64() {
                let avg = sorted.iter().map(|x| x.to_f64().unwrap_or(0.0)).sum::<f64>() / sorted.len() as f64;
                if avg > 0.0 && g > avg * 2.0 {
                    gaps_big += 1;
                }
            }
        }
    }
    gaps_big >= k / 2
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

/// Detect if gap-based decomposition is possible (SplitSolver candidate).
fn detect_gap_split(sorted: &[BigUint], _max_gap_ratio: f64) -> bool {
    if sorted.len() < 4 {
        return false;
    }
    // A gap exists if any adjacent pair sums to less than the total
    // This is a coarse detection — the actual split is target-dependent
    // which happens at runtime. Here we just check if the values span
    // a wide enough range to make splits likely.
    let total: f64 = sorted.iter()
        .filter_map(|x| x.to_f64())
        .sum();
    if total <= 0.0 { return false; }
    let mut gaps = 0usize;
    for i in 0..sorted.len() - 1 {
        let diff = (&sorted[i+1] - &sorted[i]).to_f64().unwrap_or(0.0);
        if diff > 0.0 && diff / total > 0.05 {
            gaps += 1;
        }
    }
    gaps >= 2
}

/// Compute how "linear-friendly" the instance is (0.0 = not, 1.0 = very).
fn compute_linear_favorable(
    dist: ValDist, has_gap_split: bool, dominance_len: usize,
    max_gap_ratio: f64, n: usize, redundancy: f64,
) -> f64 {
    let mut score: f64 = 0.0;

    // Exponential distribution: greedy works very well
    if matches!(dist, ValDist::Exponential) {
        score += 0.35;
    }

    // Gap splits: linear decomposition possible
    if has_gap_split {
        score += 0.25;
    }

    // Long dominance chain: greedy descending works
    if n >= 3 {
        let dom_ratio = dominance_len as f64 / n as f64;
        if dom_ratio > 0.7 {
            score += 0.20;
        } else if dom_ratio > 0.4 {
            score += 0.10;
        }
    }

    // Wide gaps between clusters
    if max_gap_ratio > 0.3 {
        score += 0.15;
    }

    // High redundancy: greedy variants are more likely to find solution
    if redundancy > 0.2 {
        score += 0.10;
    }

    // Dense-small: greedy first then BitsetDP
    if matches!(dist, ValDist::DenseSmall) {
        score += 0.05;
    }

    score.min(1.0)
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
