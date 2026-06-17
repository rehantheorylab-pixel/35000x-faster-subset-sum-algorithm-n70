use num_bigint::BigUint;
use num_integer::Integer;
use num_traits::{One, Zero};

pub struct Reduced {
    pub numbers: Vec<BigUint>,
    pub target: BigUint,
    pub forced: Vec<BigUint>,
    pub impossible: bool,
}

/// Multi-pass linear-time reduction:
/// 1. Filter elements > target
/// 2. GCD reduction: if all elements & target share factor g>1, divide everything by g
/// 3. Standard forced-inclusion fixpoint: element whose exclusion drops sum below target
/// 4. Prune elements > remaining target
pub fn reduce(numbers: &[BigUint], target: &BigUint) -> Reduced {
    // --- Pass 1: zero & overflow filter ---
    let mut nums: Vec<BigUint> = numbers
        .iter()
        .filter(|x| !x.is_zero() && **x <= *target)
        .cloned()
        .collect();
    let mut tgt = target.clone();
    let mut forced: Vec<BigUint> = Vec::new();

    let s: BigUint = nums.iter().sum();
    if s < tgt {
        return Reduced { numbers: nums, target: tgt, forced, impossible: true };
    }

    // --- GCD reduction ---
    if !nums.is_empty() {
        let mut g = nums[0].clone();
        for x in &nums[1..] {
            g = g.gcd(x);
            if g.is_one() { break; }
        }
        if g > BigUint::from(1u32) {
            let tgt_mod = &tgt % &g;
            if !tgt_mod.is_zero() {
                // GCD doesn't divide target — provably impossible
                return Reduced { numbers: nums, target: tgt, forced, impossible: true };
            }
            // Divide everything by g (problem is equivalent)
            for x in &mut nums {
                *x /= &g;
            }
            tgt /= &g;
        }
    }

    // --- Pass 2+: forced-inclusion fixpoint + prune > target ---
    let mut changed = true;
    while changed {
        changed = false;
        let total: BigUint = nums.iter().sum();
        let mut kept: Vec<BigUint> = Vec::with_capacity(nums.len());
        for x in &nums {
            if &total - x < tgt {
                // Excluding x makes the sum drop below target → x is forced
                if *x > tgt {
                    return Reduced { numbers: nums, target: tgt, forced, impossible: true };
                }
                forced.push(x.clone());
                tgt -= x;
                changed = true;
                if tgt.is_zero() {
                    return Reduced { numbers: kept, target: tgt, forced, impossible: false };
                }
            } else {
                kept.push(x.clone());
            }
        }

        if tgt.is_zero() {
            return Reduced { numbers: kept, target: tgt, forced, impossible: false };
        }

        // Prune elements > remaining target
        let mut tighter: Vec<BigUint> = Vec::with_capacity(kept.len());
        for x in kept {
            if x <= tgt {
                tighter.push(x);
            } else {
                changed = true;
            }
        }
        nums = tighter;

        let new_sum: BigUint = nums.iter().sum();
        if (!nums.is_empty() && new_sum < tgt) || (nums.is_empty() && !tgt.is_zero()) {
            return Reduced { numbers: nums, target: tgt, forced, impossible: true };
        }
    }

    nums.sort();
    Reduced { numbers: nums, target: tgt, forced, impossible: false }
}
