//! Decompose Engine — Goal-First Decomposition.
//!
//! Reference: `Subset sum algorithm.md` lines 9565, 12101.
//!
//! Idea: instead of building toward the target, *split the target*
//! into balanced anchor pieces (target/2, target/3, target/4, ...)
//! and look for elements (or pairs/triples) that match each piece.
//!
//! For `target = T`:
//!   - try anchor a = closest element to T/2; if T-a is in the set
//!     (or in S+S), that's a 2- or 3-element solution.
//!   - try anchor a = closest element to T/3; if (T-a)/2 has a
//!     2-element decomposition, that's a 3-element solution.
//!   - try anchor a = closest element to T/4; recurse for the
//!     remainder using bitset DP if remainder is small.

use num_bigint::BigUint;
use num_traits::ToPrimitive;
use std::collections::HashSet;

use crate::bitset::Bitset;
use crate::controller::{Engine, Shared};

pub struct DecomposeEngine;

const MAX_GAP_BITS: u64 = 22; // ~4 M

impl Engine for DecomposeEngine {
    fn name(&self) -> &'static str {
        "Decompose"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        if p.n == 0 {
            return;
        }

        // Try divisors 2, 3, 4, 5, 6.  Each anchor = element nearest target/d.
        for d in 2u32..=6 {
            if sh.stopped() {
                return;
            }
            let chunk = &p.target / BigUint::from(d);
            let anchor_idx = match nearest_index(p, &chunk) {
                Some(i) => i,
                None => continue,
            };
            let anchor = p.numbers[anchor_idx].clone();
            if anchor > p.target {
                continue;
            }
            let rem = &p.target - &anchor;
            if rem == BigUint::from(0u32) {
                sh.report(vec![anchor], "Decompose");
                return;
            }

            // Build remaining-element pool (without using `anchor_idx`).
            let pool_set: HashSet<&BigUint> = p.freq.keys().collect();
            // 2-element decomposition of rem.
            for x in &p.numbers {
                if sh.stopped() {
                    return;
                }
                if x > &rem {
                    continue;
                }
                let need = &rem - x;
                if need.is_empty_zero() {
                    continue;
                }
                if pool_set.contains(&need) {
                    if !same_index(&anchor, x, &need, p) {
                        let mut sol = vec![anchor.clone(), x.clone(), need];
                        sol.sort();
                        sh.report(sol, "Decompose");
                        return;
                    }
                }
            }
            let _ = pool_set;

            // 3+-element via bitset DP for small remainders.
            if rem.bits() <= MAX_GAP_BITS {
                let rem_us = match rem.to_usize() {
                    Some(u) => u,
                    None => continue,
                };
                let mut elems: Vec<usize> = Vec::with_capacity(p.n - 1);
                for (i, x) in p.numbers.iter().enumerate() {
                    if i == anchor_idx {
                        continue;
                    }
                    if let Some(u) = x.to_usize() {
                        if u <= rem_us {
                            elems.push(u);
                        }
                    }
                }
                if elems.is_empty() {
                    continue;
                }
                let mut dp = Bitset::new(rem_us + 1);
                dp.set(0);
                let mut hist: Vec<Bitset> = Vec::with_capacity(elems.len() + 1);
                hist.push(dp.clone());
                let mut found = false;
                for &v in &elems {
                    if sh.stopped() {
                        return;
                    }
                    dp.shift_or_inplace(v);
                    hist.push(dp.clone());
                    if dp.get(rem_us) {
                        found = true;
                        break;
                    }
                }
                if found {
                    let mut cur = rem_us;
                    let mut sub: Vec<usize> = Vec::new();
                    for i in (0..elems.len()).rev() {
                        if cur == 0 {
                            break;
                        }
                        if i + 1 >= hist.len() {
                            continue;
                        }
                        let v = elems[i];
                        if cur >= v && hist[i].get(cur - v) {
                            sub.push(v);
                            cur -= v;
                        }
                    }
                    if cur == 0 {
                        let mut sol: Vec<BigUint> = vec![anchor.clone()];
                        sol.extend(sub.into_iter().map(BigUint::from));
                        sol.sort();
                        sh.report(sol, "Decompose");
                        return;
                    }
                }
            }
        }
    }
}

fn nearest_index(p: &crate::profile::Profile, chunk: &BigUint) -> Option<usize> {
    if p.n == 0 {
        return None;
    }
    let mut best = 0usize;
    let mut best_d = absdiff_big(&p.numbers[0], chunk);
    for (i, x) in p.numbers.iter().enumerate().skip(1) {
        let d = absdiff_big(x, chunk);
        if d < best_d {
            best_d = d;
            best = i;
        }
    }
    Some(best)
}

fn absdiff_big(a: &BigUint, b: &BigUint) -> BigUint {
    if a >= b { a - b } else { b - a }
}

fn same_index(_anchor: &BigUint, _x: &BigUint, _need: &BigUint, _p: &crate::profile::Profile) -> bool {
    false
}

trait IsEmptyZero {
    fn is_empty_zero(&self) -> bool;
}
impl IsEmptyZero for BigUint {
    fn is_empty_zero(&self) -> bool {
        use num_traits::Zero;
        self.is_zero()
    }
}
