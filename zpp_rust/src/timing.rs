//! Ultra-precise timing utilities.
//!
//! Wall-clock uses `Instant::now()` which on Windows is backed by
//! `QueryPerformanceCounter` (typically 100 ns or finer resolution).
//! CPU time uses `cpu_time::ProcessTime` which is `GetProcessTimes()`
//! on Windows (~15 ms tick) and `clock_gettime(CLOCK_PROCESS_CPUTIME_ID)`
//! on Linux (nanosecond resolution).
//!
//! We display the measured duration decomposed into seconds, ms, μs,
//! ns, ps, fs, and as.  Only ns or coarser is *physically* meaningful
//! on consumer hardware — everything below ns is shown as a
//! mathematical conversion of the ns value, with the meaningless
//! trailing zeros honestly disclosed.

use std::time::Duration;

pub struct Timing {
    pub wall: Duration,
    pub cpu: Duration,
}

impl Timing {
    /// True if the wall-clock duration is below the platform timer
    /// resolution (we assume ~100 ns conservative bound on Windows).
    pub fn is_sub_resolution(&self) -> bool {
        self.wall.as_nanos() == 0
    }
}

pub fn fmt_duration(d: Duration) -> String {
    let total_ns = d.as_nanos();

    let s = total_ns as f64 / 1_000_000_000.0;
    let ms = total_ns as f64 / 1_000_000.0;
    let us = total_ns as f64 / 1_000.0;
    let ns = total_ns as i128;
    let ps = total_ns as i128 * 1_000;
    let fs = total_ns as i128 * 1_000_000;
    let attos = total_ns as i128 * 1_000_000_000;

    format!(
        "Seconds      : {:.12}\n      \
         Milliseconds : {:.9} ms\n      \
         Microseconds : {:.6} μs\n      \
         Nanoseconds  : {} ns\n      \
         Picoseconds  : {} ps\n      \
         Femtoseconds : {} fs\n      \
         Attoseconds  : {} as",
        s, ms, us, ns, ps, fs, attos
    )
}

pub fn parallelism_ratio(cpu: Duration, wall: Duration) -> f64 {
    let c = cpu.as_nanos() as f64;
    let w = wall.as_nanos() as f64;
    if w <= 0.0 {
        0.0
    } else {
        c / w
    }
}
