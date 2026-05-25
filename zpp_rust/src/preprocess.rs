//! Preprocessor: filters out elements that exceed the target and
//! detects must-include elements (elements without which the rest
//! of the set cannot reach the target).

use num_bigint::BigUint;
use num_traits::Zero;

pub struct Reduced {
    pub numbers: Vec<BigUint>,
    pub target: BigUint,
    pub forced: Vec<BigUint>,
    pub impossible: bool,
}

pub fn reduce(numbers: &[BigUint], target: &BigUint) -> Reduced {
    let mut nums: Vec<BigUint> = numbers
        .iter()
        .filter(|x| !x.is_zero() && **x <= *target)
        .cloned()
        .collect();
    let mut tgt = target.clone();
    let mut forced: Vec<BigUint> = Vec::new();

    let s: BigUint = nums.iter().sum();
    if s < tgt {
        return Reduced {
            numbers: nums,
            target: tgt,
            forced,
            impossible: true,
        };
    }

    let mut changed = true;
    while changed {
        changed = false;
        let total: BigUint = nums.iter().sum();
        let mut kept: Vec<BigUint> = Vec::with_capacity(nums.len());
        for x in &nums {
            if &total - x < tgt {
                forced.push(x.clone());
                tgt -= x;
                changed = true;
            } else {
                kept.push(x.clone());
            }
        }
        nums = kept;

        if tgt.is_zero() {
            return Reduced {
                numbers: nums,
                target: tgt,
                forced,
                impossible: false,
            };
        }
        let new_sum: BigUint = nums.iter().sum();
        if (!nums.is_empty() && new_sum < tgt) || (nums.is_empty() && !tgt.is_zero()) {
            return Reduced {
                numbers: nums,
                target: tgt,
                forced,
                impossible: true,
            };
        }
    }

    nums.sort();
    Reduced {
        numbers: nums,
        target: tgt,
        forced,
        impossible: false,
    }
}
