//! ColumnSAT — SAT-encoded subset sum solver.
//!
//! Reference: `Subset sum algorithm.md` line 16385 and the Python
//! version (`Z_plus_plus_gui.py::ColumnStructureEngine`).
//!
//! Some "world record" benchmark instances of subset sum come from
//! Karp reductions of SAT problems.  These produce numbers with
//! 950+ digits where each "column" of the decimal expansion encodes
//! a SAT variable or clause.  No general subset-sum algorithm can
//! handle the raw size — but the column structure means we can
//! decode it back into a SAT problem and run a tiny DPLL solver
//! on the *original* SAT instance, then reconstruct the subset.
//!
//! This engine detects the column pattern (target digits ∈ {1, 3}
//! at fixed column width) and returns IMMEDIATELY if the pattern
//! is absent.  When present, it can solve 1900-element 1899-digit
//! instances in well under a second.

use num_bigint::BigUint;

use crate::controller::{Engine, Shared};

pub struct ColumnSatEngine;

impl Engine for ColumnSatEngine {
    fn name(&self) -> &'static str {
        "ColumnSAT"
    }

    fn run(&self, sh: &Shared) {
        let p = &sh.profile;
        let target_str = p.target.to_str_radix(10);
        let nd = target_str.len();
        if nd < 10 || p.n < 20 {
            return;
        }

        let (cw, td_vals) = match detect_column_width(&target_str) {
            Some(x) => x,
            None => return,
        };
        let unique_set: std::collections::HashSet<u32> = td_vals.iter().copied().collect();
        if unique_set.len() < 2 || unique_set.len() > 4 {
            return;
        }
        // Smallest non-zero column value = variable column; largest = clause column.
        let var_t = unique_set
            .iter()
            .filter(|&&v| v > 0)
            .min()
            .copied()
            .unwrap_or_else(|| *unique_set.iter().min().unwrap());
        let clause_t = *unique_set.iter().max().unwrap();
        let n_vc = td_vals.iter().filter(|&&v| v == var_t).count();
        let n_cc = td_vals.iter().filter(|&&v| v == clause_t).count();
        if n_vc < 2 || n_cc < 2 {
            return;
        }

        let expected_width = cw * (n_vc + n_cc);
        let mut strs: Vec<String> = p
            .numbers
            .iter()
            .map(|x| {
                let s = x.to_str_radix(10);
                if s.len() < expected_width {
                    "0".repeat(expected_width - s.len()) + &s
                } else {
                    s
                }
            })
            .collect();
        // pad target to common width
        let pad_target = if target_str.len() < expected_width {
            "0".repeat(expected_width - target_str.len()) + &target_str
        } else {
            target_str
        };

        // Identify variable/clause column positions
        let mut var_cols: Vec<(usize, usize, usize, usize)> = Vec::new();
        for (ci, val) in td_vals.iter().enumerate() {
            if *val != var_t {
                continue;
            }
            let cs = ci * cw;
            let pair: Vec<usize> = (0..p.n)
                .filter(|i| {
                    let s: u32 = strs[*i][cs..cs + cw].parse().unwrap_or(0);
                    s == var_t
                })
                .collect();
            if pair.len() == 2 {
                var_cols.push((ci, cs, pair[0], pair[1]));
            }
        }
        if var_cols.len() != n_vc {
            return;
        }
        let clause_col_infos: Vec<(usize, usize)> = (0..td_vals.len())
            .filter(|&ci| td_vals[ci] == clause_t)
            .map(|ci| (ci, ci * cw))
            .collect();

        let mut var_set = std::collections::HashSet::<usize>::new();
        let mut elem_info = std::collections::HashMap::<usize, (i32, bool)>::new();
        for (vi, (_ci, _cs, ea, eb)) in var_cols.iter().enumerate() {
            var_set.insert(*ea);
            var_set.insert(*eb);
            elem_info.insert(*ea, ((vi + 1) as i32, true));
            elem_info.insert(*eb, ((vi + 1) as i32, false));
        }

        // Extract SAT clauses
        let mut sat_clauses: Vec<Vec<i32>> = Vec::new();
        for &(_ci, cs) in &clause_col_infos {
            if sh.stopped() {
                return;
            }
            let mut lits: Vec<i32> = Vec::new();
            for ei in &var_set {
                let v: u32 = strs[*ei][cs..cs + cw].parse().unwrap_or(0);
                if v > 0 {
                    if let Some(&(vid, pos)) = elem_info.get(ei) {
                        lits.push(if pos { vid } else { -vid });
                    }
                }
            }
            if !lits.is_empty() {
                sat_clauses.push(lits);
            }
        }

        let asgn = match dpll(n_vc as i32, &sat_clauses, sh) {
            Some(a) => a,
            None => return,
        };

        // Construct the chosen subset
        let slack_elems: Vec<usize> = (0..p.n).filter(|i| !var_set.contains(i)).collect();
        let mut chosen: std::collections::HashSet<usize> = std::collections::HashSet::new();
        for (vi, (_ci, _cs, ea, eb)) in var_cols.iter().enumerate() {
            chosen.insert(if asgn[vi] { *ea } else { *eb });
        }
        // Fill clause columns with slack elements
        for (_ci, cs) in &clause_col_infos {
            if sh.stopped() {
                return;
            }
            let contrib: u32 = chosen
                .iter()
                .map(|e| {
                    let v: u32 = strs[*e][*cs..cs + cw].parse().unwrap_or(0);
                    v
                })
                .sum();
            if contrib >= clause_t {
                continue;
            }
            let mut need = clause_t - contrib;
            let mut available: Vec<(usize, u32)> = slack_elems
                .iter()
                .filter(|se| !chosen.contains(se))
                .filter_map(|se| {
                    let v: u32 = strs[*se][*cs..cs + cw].parse().unwrap_or(0);
                    if v > 0 { Some((*se, v)) } else { None }
                })
                .collect();
            available.sort_by(|a, b| b.1.cmp(&a.1));
            for (se, sv) in available {
                if need == 0 {
                    break;
                }
                if sv <= need {
                    chosen.insert(se);
                    need -= sv;
                }
            }
        }

        let solution: Vec<BigUint> = chosen.iter().map(|&i| p.numbers[i].clone()).collect();
        let total: BigUint = solution.iter().sum();
        if total == p.target {
            sh.report(solution, "ColumnSAT");
        }

        let _ = pad_target;
        let _ = strs.len();
    }
}

fn detect_column_width(target: &str) -> Option<(usize, Vec<u32>)> {
    for cw in [2usize, 3, 1] {
        let pad = (cw - target.len() % cw) % cw;
        let padded = "0".repeat(pad) + target;
        if padded.len() % cw != 0 {
            continue;
        }
        let mut cols: Vec<u32> = Vec::with_capacity(padded.len() / cw);
        let mut ok = true;
        for chunk in padded.as_bytes().chunks(cw) {
            let s = std::str::from_utf8(chunk).ok()?;
            let v: u32 = s.parse().ok()?;
            if v > 99 {
                ok = false;
                break;
            }
            cols.push(v);
        }
        if !ok {
            continue;
        }
        let unique: std::collections::HashSet<u32> = cols.iter().copied().collect();
        if unique.len() == 2 {
            return Some((cw, cols));
        }
    }
    None
}

fn dpll(n: i32, clauses: &[Vec<i32>], sh: &Shared) -> Option<Vec<bool>> {
    let mut a: Vec<i32> = vec![0; n as usize + 1];
    let mut pos_in: Vec<Vec<usize>> = vec![Vec::new(); n as usize + 1];
    let mut neg_in: Vec<Vec<usize>> = vec![Vec::new(); n as usize + 1];
    for (ci, cl) in clauses.iter().enumerate() {
        for &l in cl {
            let v = l.unsigned_abs() as usize;
            if (v as i32) <= n {
                if l > 0 {
                    pos_in[v].push(ci);
                } else {
                    neg_in[v].push(ci);
                }
            }
        }
    }

    fn propagate(
        a: &mut [i32],
        clauses: &[Vec<i32>],
        pos_in: &[Vec<usize>],
        neg_in: &[Vec<usize>],
        trail: &mut Vec<i32>,
    ) -> bool {
        let mut qi = 0;
        while qi < trail.len() {
            let var = trail[qi].unsigned_abs() as usize;
            qi += 1;
            let val = a[var];
            let aff: &Vec<usize> = if val == 1 { &neg_in[var] } else { &pos_in[var] };
            for &ci in aff {
                let cl = &clauses[ci];
                let mut ul: i32 = 0;
                let mut uc = 0i32;
                let mut sat = false;
                for &l in cl {
                    let v = l.unsigned_abs() as usize;
                    let av = a[v];
                    if av == 0 {
                        uc += 1;
                        ul = l;
                        if uc > 1 {
                            break;
                        }
                    } else if (l > 0 && av == 1) || (l < 0 && av == -1) {
                        sat = true;
                        break;
                    }
                }
                if sat {
                    continue;
                }
                if uc == 0 {
                    return false;
                }
                if uc == 1 {
                    let v = ul.unsigned_abs() as usize;
                    a[v] = if ul > 0 { 1 } else { -1 };
                    trail.push(ul);
                }
            }
        }
        true
    }

    let mut trail: Vec<i32> = Vec::new();
    for cl in clauses {
        if cl.len() == 1 {
            let v = cl[0].unsigned_abs() as usize;
            if a[v] == 0 {
                a[v] = if cl[0] > 0 { 1 } else { -1 };
                trail.push(cl[0]);
            }
        }
    }
    if !propagate(&mut a, clauses, &pos_in, &neg_in, &mut trail) {
        return None;
    }

    let mut stack: Vec<(i32, bool, usize)> = Vec::new();
    loop {
        if sh.stopped() {
            return None;
        }
        let mut bv = 0i32;
        let mut bs: i32 = -1;
        for v in 1..=n {
            if a[v as usize] != 0 {
                continue;
            }
            let mut sc = 0i32;
            for &ci in pos_in[v as usize].iter().chain(neg_in[v as usize].iter()) {
                let cl = &clauses[ci];
                let satisfied = cl.iter().any(|&l| {
                    let av = a[l.unsigned_abs() as usize];
                    (l > 0 && av == 1) || (l < 0 && av == -1)
                });
                if !satisfied {
                    sc += 1;
                }
            }
            if sc > bs {
                bs = sc;
                bv = v;
            }
        }
        if bv == 0 {
            break;
        }
        let mk = trail.len();
        stack.push((bv, true, mk));
        a[bv as usize] = 1;
        trail.push(bv);
        if !propagate(&mut a, clauses, &pos_in, &neg_in, &mut trail) {
            // backtrack
            let mut found = false;
            while let Some((dv, dval, m)) = stack.pop() {
                while trail.len() > m {
                    let l = trail.pop().unwrap();
                    a[l.unsigned_abs() as usize] = 0;
                }
                if dval {
                    stack.push((dv, false, m));
                    a[dv as usize] = -1;
                    trail.push(-dv);
                    if propagate(&mut a, clauses, &pos_in, &neg_in, &mut trail) {
                        found = true;
                        break;
                    }
                }
            }
            if !found {
                return None;
            }
        }
    }
    let mut out = vec![false; n as usize];
    for v in 1..=n {
        out[v as usize - 1] = a[v as usize] != -1;
    }
    Some(out)
}
