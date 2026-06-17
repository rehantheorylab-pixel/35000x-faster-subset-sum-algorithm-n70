use num_bigint::BigUint;
use num_traits::Zero;
use crate::controller::{Engine, Shared};

pub struct TinyBruteEngine;

impl Engine for TinyBruteEngine {
    fn name(&self) -> &'static str {
        "TinyBrute"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if p.n > 12 { return; }
        if sh.stopped() { return; }

        if p.u128_safe() {
            self.run_u128(sh);
        } else {
            self.run_big(sh);
        }
    }
}

impl TinyBruteEngine {
    fn run_u128(&self, sh: &Shared) {
        let target = sh.profile.target_u128();
        let nums = sh.profile.numbers_u128();
        let n = nums.len();
        let total = 1u64 << n;
        for mask in 0u64..total {
            if (mask & 0xFF) == 0 && sh.stopped() { return; }
            let mut sum = 0u128;
            let mut m = mask;
            while m != 0 {
                let k = m.trailing_zeros() as usize;
                sum = sum.wrapping_add(nums[k]);
                if sum > target { break; }
                m &= m - 1;
            }
            if sum == target {
                let mut sol: Vec<BigUint> = Vec::new();
                let mut mm = mask;
                while mm != 0 {
                    let k = mm.trailing_zeros() as usize;
                    sol.push(BigUint::from(nums[k]));
                    mm &= mm - 1;
                }
                sh.report(sol, "TinyBrute");
                return;
            }
        }
    }

    fn run_big(&self, sh: &Shared) {
        let target = &sh.profile.target;
        let nums = &sh.profile.numbers;
        let n = nums.len();
        let total = 1u64 << n;
        for mask in 0u64..total {
            if (mask & 0xFF) == 0 && sh.stopped() { return; }
            let mut sum = BigUint::zero();
            let mut m = mask;
            while m != 0 {
                let k = m.trailing_zeros() as usize;
                sum += &nums[k];
                if sum > *target { break; }
                m &= m - 1;
            }
            if sum == *target {
                let mut sol: Vec<BigUint> = Vec::new();
                let mut mm = mask;
                while mm != 0 {
                    let k = mm.trailing_zeros() as usize;
                    sol.push(nums[k].clone());
                    mm &= mm - 1;
                }
                sh.report(sol, "TinyBrute");
                return;
            }
        }
    }
}
