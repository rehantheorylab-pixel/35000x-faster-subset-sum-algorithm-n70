use num_bigint::BigUint;
use num_traits::{ToPrimitive, Zero};
use std::sync::atomic::Ordering;
use crate::controller::{Engine, Shared};

pub struct DigitFilterEngine;

impl DigitFilterEngine {
    fn last_digit_reachable(nums: &[BigUint], target_ld: u32) -> bool {
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

    fn first_digit_feasible(nums: &[BigUint], target: &BigUint) -> bool {
        if nums.is_empty() { return target.is_zero(); }
        let t_fd = Self::first_digit(target);
        let t_mag = Self::magnitude(target);
        let mut min_sum = BigUint::zero();
        let mut max_sum = BigUint::zero();
        for x in nums {
            if x <= target {
                min_sum = Self::min_if_summed(&min_sum, x, target);
            }
            max_sum += x;
        }
        let max_fd = Self::first_digit(&max_sum);
        let max_mag = Self::magnitude(&max_sum);
        if max_mag < t_mag || (max_mag == t_mag && max_fd < t_fd) {
            return false;
        }
        if !min_sum.is_zero() {
            let min_fd = Self::first_digit(&min_sum);
            let min_mag = Self::magnitude(&min_sum);
            if min_mag > t_mag || (min_mag == t_mag && min_fd > t_fd) {
                return false;
            }
        }
        true
    }

    fn min_if_summed(a: &BigUint, b: &BigUint, target: &BigUint) -> BigUint {
        let s = a + b;
        if s > *target { BigUint::zero() } else { s }
    }
}

impl Engine for DigitFilterEngine {
    fn name(&self) -> &'static str { "DigitFilter" }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if p.n == 0 || p.target.is_zero() { return; }

        let target_ld = (&p.target % 10u32).to_u32().unwrap_or(0);
        if !Self::last_digit_reachable(&p.numbers, target_ld) {
            sh.proved_impossible.store(true, Ordering::Release);
            sh.stop.store(true, Ordering::Release);
            return;
        }

        if !Self::first_digit_feasible(&p.numbers, &p.target) {
            sh.proved_impossible.store(true, Ordering::Release);
            sh.stop.store(true, Ordering::Release);
        }
    }
}
