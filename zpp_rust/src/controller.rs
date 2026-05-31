//! Z++ Meta-Brain controller.
//! Spawns engines on real OS threads; first to find an exact match
//! signals all others to stop via an atomic flag.  Rust has no GIL,
//! so threads run truly in parallel.

use dashmap::DashMap;
use num_bigint::BigUint;
use num_traits::Zero;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use crate::profile::{ProblemClass, Profile};

/// Shared state across engine threads.
///
/// `blackboard` is a lock-free concurrent hash-map (DashMap) of subset
/// sums that engines have proven reachable.  Engines may consult the
/// blackboard to skip work that another engine has already done.  Use
/// `discovered_count` for cheap statistics without taking a lock.
pub struct Shared {
    pub profile: Profile,
    pub stop: AtomicBool,
    pub solution: Mutex<Option<(Vec<BigUint>, &'static str)>>,
    pub proved_impossible: AtomicBool,
    pub blackboard: DashMap<BigUint, ()>,
    pub discovered_count: AtomicU64,
}

impl Shared {
    pub fn new(profile: Profile) -> Self {
        Self {
            profile,
            stop: AtomicBool::new(false),
            solution: Mutex::new(None),
            proved_impossible: AtomicBool::new(false),
            blackboard: DashMap::with_capacity(1024),
            discovered_count: AtomicU64::new(0),
        }
    }

    /// Record that a subset sum is reachable.  Cheap; lock-free.
    #[inline]
    pub fn note_sum(&self, sum: BigUint) {
        if self.blackboard.insert(sum, ()).is_none() {
            self.discovered_count.fetch_add(1, Ordering::Relaxed);
        }
    }

    pub fn stopped(&self) -> bool {
        self.stop.load(Ordering::Relaxed)
    }

    pub fn report(&self, sol: Vec<BigUint>, name: &'static str) {
        if self.stop.load(Ordering::Relaxed) {
            return;
        }
        let s: BigUint = sol.iter().sum();
        if s != self.profile.target {
            return;
        }
        let mut guard = self.solution.lock().unwrap();
        if guard.is_none() {
            *guard = Some((sol, name));
            self.stop.store(true, Ordering::Release);
        }
    }
}

pub trait Engine: Send + Sync {
    fn name(&self) -> &'static str;
    fn run(&self, sh: &Shared);
}

pub struct Outcome {
    pub solution: Option<Vec<BigUint>>,
    pub winner: &'static str,
    pub proved_impossible: bool,
    pub wall: Duration,
}

pub fn race(profile: Profile, engines: Vec<Box<dyn Engine>>, max_time: Duration) -> Outcome {
    let shared = Arc::new(Shared::new(profile));
    let start = Instant::now();

    let mut handles = Vec::with_capacity(engines.len());
    for engine in engines {
        let sh = Arc::clone(&shared);
        handles.push(thread::spawn(move || {
            engine.run(&sh);
        }));
    }

    while start.elapsed() < max_time && !shared.stopped() {
        thread::sleep(Duration::from_micros(100));
    }
    shared.stop.store(true, Ordering::Release);

    for h in handles {
        let _ = h.join();
    }

    let wall = start.elapsed();
    let guard = shared.solution.lock().unwrap();
    let proved_impossible = shared.proved_impossible.load(Ordering::Relaxed);
    let (solution, winner) = match guard.clone() {
        Some((sol, name)) => (Some(sol), name),
        None => (None, if proved_impossible { "IMPOSSIBLE" } else { "Timeout" }),
    };

    Outcome {
        solution,
        winner,
        proved_impossible,
        wall,
    }
}

pub fn pick_engines(p: &Profile) -> Vec<&'static str> {
    let core_proof = ["Residue", "DigitFilter", "Dominance", "ColumnSAT"];
    // Hard-u128 engines — fast parallel search for large random instances
    let hard_u128_pack = [
        "Hard-U128",
        "Schroeppel-Shamir",
        "BCJ",
        "HGJ",
        "Residue",
        "Dominance",
    ];

    let common_heuristics = [
        "KSum",
        "Estimate",
        "Decompose",
        "DualCollapse",
        "Beam-SRP",
        "APDE",
        "PMAS-Balance",
        "PMAS-Difference",
        "PMAS-Bit",
        "PMAS-Redundancy",
    ];

    let mut v: Vec<&'static str> = Vec::new();
    v.extend(core_proof.iter().copied());

    if p.is_super_increasing {
        v.extend(["Greedy", "Dominance", "Backward"]);
    }

    if p.looks_sat_encoded() {
        return vec!["ColumnSAT", "Residue", "Dominance"];
    }

    if p.u128_safe() && p.n >= 44 && p.n <= 72 {
        // Always include Hard-U128 pack for fast specialized solving
        v.extend(hard_u128_pack.iter().copied());
    }

    match p.class {
        ProblemClass::Trivial | ProblemClass::Tiny => {
            v.extend(["BitsetDP", "MITM", "Schroeppel-Shamir", "Greedy"]);
        }
        ProblemClass::Small => {
            v.extend([
                "Schroeppel-Shamir",
                "BCJ",
                "Bonnetain",
                "MITM",
                "HGJ",
                "BitsetDP",
                "Greedy",
                "Backward",
            ]);
        }
        ProblemClass::Medium => {
            v.extend([
                "Schroeppel-Shamir",
                "BCJ",
                "Bonnetain",
                "HGJ",
                "BitsetDP",
                "Greedy",
                "Backward",
                "Bridge",
            ]);
        }
        ProblemClass::Large => {
            v.extend([
                "Schroeppel-Shamir",
                "BCJ",
                "HGJ",
                "Greedy",
                "Backward",
                "Bridge",
                "Randomized",
            ]);
        }
    }
    v.extend(common_heuristics.iter().copied());
    v
}

#[allow(dead_code)]
pub fn _supress_zero_warning(_b: &BigUint) {
    let _ = BigUint::zero();
}
