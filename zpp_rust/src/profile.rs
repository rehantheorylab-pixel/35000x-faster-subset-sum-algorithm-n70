//! Problem profile: statistics + classification used by the controller
//! to choose the best engine mix for a given input.

use num_bigint::BigUint;
use num_traits::Zero;
use std::collections::HashMap;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProblemClass {
    Trivial,
    Tiny,
    Small,
    Medium,
    Large,
}

#[derive(Clone)]
pub struct Profile {
    pub numbers: Vec<BigUint>,
    pub target: BigUint,
    pub n: usize,
    pub total_sum: BigUint,
    pub freq: HashMap<BigUint, u32>,
    pub min_val: BigUint,
    pub max_val: BigUint,
    pub class: ProblemClass,
    /// n / log2(target+1) — high means dense / hard.
    pub density: f64,
    pub is_super_increasing: bool,
    pub entropy_score: f64,
}

impl Profile {
    pub fn new(mut numbers: Vec<BigUint>, target: BigUint) -> Self {
        numbers.sort();
        let n = numbers.len();
        let total_sum: BigUint = numbers.iter().sum();

        let mut freq = HashMap::new();
        for x in &numbers {
            *freq.entry(x.clone()).or_insert(0u32) += 1;
        }

        let (min_val, max_val) = if n == 0 {
            (BigUint::zero(), BigUint::zero())
        } else {
            (numbers[0].clone(), numbers[n - 1].clone())
        };

        let target_bits = target.bits();
        let density = if target_bits > 0 {
            n as f64 / target_bits as f64
        } else {
            0.0
        };
        let is_super_increasing = check_super_increasing(&numbers);
        let entropy_score = coefficient_of_variation(&numbers);

        let class = if n <= 5 {
            ProblemClass::Trivial
        } else if n <= 20 {
            ProblemClass::Tiny
        } else if n <= 40 {
            ProblemClass::Small
        } else if target_bits <= 24 {
            ProblemClass::Medium
        } else {
            ProblemClass::Large
        };

        Self {
            numbers,
            target,
            n,
            total_sum,
            freq,
            min_val,
            max_val,
            class,
            density,
            is_super_increasing,
            entropy_score,
        }
    }

    pub fn target_digits(&self) -> usize {
        self.target.to_str_radix(10).len()
    }

    /// True iff every element AND the target fit inside u128
    /// AND the total sum also fits — enables the u128 native fast
    /// path (no BigUint allocations on the inner loop).
    pub fn u128_safe(&self) -> bool {
        if self.target.bits() > 128 {
            return false;
        }
        if self.total_sum.bits() > 128 {
            return false;
        }
        self.numbers.iter().all(|x| x.bits() <= 128)
    }

    /// Convert numbers to a u128 vector (call only after u128_safe()).
    pub fn numbers_u128(&self) -> Vec<u128> {
        use num_traits::ToPrimitive;
        self.numbers
            .iter()
            .map(|x| x.to_u128().unwrap_or(0))
            .collect()
    }

    pub fn target_u128(&self) -> u128 {
        use num_traits::ToPrimitive;
        self.target.to_u128().unwrap_or(0)
    }

    pub fn looks_sat_encoded(&self) -> bool {
        self.target_digits() > 100 && self.n >= 100
    }
}

fn check_super_increasing(nums: &[BigUint]) -> bool {
    if nums.len() < 2 {
        return false;
    }
    let mut partial = BigUint::zero();
    for (i, x) in nums.iter().enumerate() {
        if i > 0 && x <= &partial {
            return false;
        }
        partial += x;
    }
    true
}

fn coefficient_of_variation(nums: &[BigUint]) -> f64 {
    if nums.is_empty() {
        return 0.0;
    }
    // Use bit-length distribution as a lossless entropy proxy.
    // For any BigUint, bits() returns the exact number of bits.
    // CV of bit lengths is well-defined even for 10000-digit numbers.
    let bitlens: Vec<f64> = nums.iter().map(|x| x.bits() as f64).collect();
    let mean = bitlens.iter().sum::<f64>() / bitlens.len() as f64;
    if mean.abs() < 1e-12 {
        return 1.0;
    }
    let var = bitlens.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / bitlens.len() as f64;
    var.sqrt() / mean
}
