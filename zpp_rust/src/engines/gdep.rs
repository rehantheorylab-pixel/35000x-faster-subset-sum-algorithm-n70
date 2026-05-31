use num_bigint::BigUint;
use num_traits::{ToPrimitive, Zero};
use crate::controller::{Engine, Shared};

pub struct GdepEngine;

impl GdepEngine {
    fn last_digit_reachable(nums: &[BigUint], target: &BigUint, current_sum: &BigUint) -> bool {
        let total_needed = if current_sum.is_zero() {
            target.clone()
        } else {
            target - current_sum
        };
        if total_needed.is_zero() { return true; }
        let target_ld = (&total_needed % 10u32).to_u32().unwrap_or(0);
        let mut reach: u16 = 1;
        for x in nums {
            let r = (x % 10u32).to_u32().unwrap_or(0) as u16;
            let shifted = (reach as u32) << r;
            let wrapped = ((shifted | (shifted >> 10)) & 0x3FF) as u16;
            reach = reach | wrapped;
        }
        (reach >> target_ld) & 1 == 1
    }

    fn magnitude(n: &BigUint) -> u32 {
        if n.is_zero() { return 0; }
        n.to_str_radix(10).len() as u32 - 1
    }

    fn first_digit(n: &BigUint) -> u32 {
        if n.is_zero() { return 0; }
        let s = n.to_str_radix(10);
        s.chars().next().unwrap_or('0').to_digit(10).unwrap_or(0)
    }
}

impl Engine for GdepEngine {
    fn name(&self) -> &'static str { "GDEP" }

    fn run(&self, sh: &Shared) {
        let nums = &sh.profile.numbers;
        let target = &sh.profile.target;
        let n = nums.len();
        if n == 0 || target.is_zero() {
            if target.is_zero() { sh.report(vec![], "GDEP"); }
            return;
        }

        let mut desc: Vec<BigUint> = nums.to_vec();
        desc.sort_by(|a, b| b.cmp(a));
        let mut suf: Vec<BigUint> = vec![BigUint::zero(); n + 1];
        for i in (0..n).rev() {
            suf[i] = &suf[i + 1] + &desc[i];
        }
        let mut path: Vec<BigUint> = Vec::new();

        fn dfs(
            nums: &[BigUint],
            suf: &[BigUint],
            target: &BigUint,
            start: usize,
            n: usize,
            path: &mut Vec<BigUint>,
            current_sum: &BigUint,
            sh: &Shared,
        ) -> bool {
            if target.is_zero() { return true; }
            if sh.stopped() || start >= n { return false; }

            let remaining = target;

            if !GdepEngine::last_digit_reachable(&nums[start..], remaining, current_sum) {
                return false;
            }

            for i in start..n {
                let v = &nums[i];
                if v > remaining { continue; }
                if suf[i] < *remaining { return false; }

                let t_mag = GdepEngine::magnitude(remaining);
                let v_mag = GdepEngine::magnitude(v);
                if v_mag > t_mag + 1 { continue; }

                if v == remaining {
                    path.push(v.clone());
                    return true;
                }

                let new_target = remaining - v;
                let new_sum = current_sum + v;
                if suf[i + 1] >= new_target {
                    path.push(v.clone());
                    if dfs(nums, suf, &new_target, i + 1, n, path, &new_sum, sh) {
                        return true;
                    }
                    path.pop();
                }
            }
            false
        }

        let zero = BigUint::zero();
        if dfs(&desc, &suf, target, 0, n, &mut path, &zero, sh) {
            sh.report(path, "GDEP");
        }
    }
}
