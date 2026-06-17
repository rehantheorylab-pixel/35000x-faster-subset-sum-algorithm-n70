use std::alloc::{GlobalAlloc, Layout};
use std::io::{self, BufRead, Write};
use std::time::{Duration, Instant};

use num_bigint::BigUint;
use num_traits::Zero;

#[cfg(windows)]
pub struct WinHeapAllocator;

#[cfg(windows)]
unsafe impl GlobalAlloc for WinHeapAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        extern "system" {
            fn GetProcessHeap() -> *mut std::ffi::c_void;
            fn HeapAlloc(hHeap: *mut std::ffi::c_void, dwFlags: u32, dwBytes: usize) -> *mut std::ffi::c_void;
        }
        let heap = GetProcessHeap();
        HeapAlloc(heap, 0, layout.size().max(1)) as *mut u8
    }
    unsafe fn dealloc(&self, ptr: *mut u8, _layout: Layout) {
        extern "system" {
            fn GetProcessHeap() -> *mut std::ffi::c_void;
            fn HeapFree(hHeap: *mut std::ffi::c_void, dwFlags: u32, lpMem: *mut std::ffi::c_void) -> i32;
        }
        let heap = GetProcessHeap();
        HeapFree(heap, 0, ptr as *mut std::ffi::c_void);
    }
}

#[cfg(windows)]
#[global_allocator]
static ALLOCATOR: WinHeapAllocator = WinHeapAllocator;

fn main() {
    let arg = std::env::args().nth(1).unwrap_or_default();
    if arg == "gui" {
        let port = std::env::args()
            .nth(2)
            .and_then(|a| a.parse::<u16>().ok())
            .unwrap_or(8080);
        zpp::gui::serve(port);
        return;
    }

    println!();
    println!("  Z++ Ultimate Engine — Rust Edition (v1.1)");
    println!();
    println!("  [1] Headless Mode  (enter numbers + target via stdin)");
    println!("  [2] GUI Mode       (web interface at http://127.0.0.1:8080)");
    println!();
    print!("  Choose [1-2]: ");
    let _ = io::stdout().flush();

    let mut line = String::new();
    io::stdin().lock().read_line(&mut line).ok();

    match line.trim() {
        "2" => { zpp::gui::serve(8080); }
        _ => run_headless(),
    }
}

fn run_headless() {
    println!();
    println!("{}", "=".repeat(56));
    println!("   Z++ HEADLESS MODE");
    println!("{}", "=".repeat(56));
    println!();
    println!("  Enter elements (comma-separated):");
    print!("  ");
    let _ = io::stdout().flush();

    let stdin = io::stdin();
    let mut elem_line = String::new();
    stdin.lock().read_line(&mut elem_line).ok();
    let nums: Vec<BigUint> = elem_line
        .split(|c: char| c == ',' || c.is_whitespace())
        .map(|s| s.trim())
        .filter(|s| !s.is_empty())
        .filter_map(|s| BigUint::parse_bytes(s.as_bytes(), 10))
        .collect();

    print!("\n  Enter target: ");
    let _ = io::stdout().flush();
    let mut tgt_line = String::new();
    stdin.lock().read_line(&mut tgt_line).ok();
    let target = BigUint::parse_bytes(tgt_line.trim().as_bytes(), 10)
        .unwrap_or_else(BigUint::zero);

    if nums.is_empty() {
        println!("  (no elements provided)");
        return;
    }

    println!();
    println!("{}", "=".repeat(56));
    println!("   RUNNING Z++ ENGINE...");
    println!("{}", "=".repeat(56));
    println!("   Elements : {}", nums.len());
    let td = target.to_str_radix(10).len();
    if td <= 40 {
        println!("   Target   : {}", target);
    } else {
        println!("   Target   : {}-digit number", td);
    }
    println!("{}", "=".repeat(56));
    println!();

    let wall_start = Instant::now();
    let outcome = zpp::solve(nums.clone(), target.clone(), Duration::from_secs(600));
    let wall = wall_start.elapsed();

    let exact = match outcome.solution.as_ref() {
        Some(sol) => sol.iter().sum::<BigUint>() == target,
        None => false,
    };

    println!();
    println!("{}", "=".repeat(56));
    println!("   Z++ PERFORMANCE REPORT");
    println!("{}", "=".repeat(56));
    println!("   Match Found     : {}", exact);
    if outcome.proved_impossible {
        println!("   PROVED IMPOSSIBLE");
    }
    println!("   Engine Winner   : {}", outcome.winner);
    println!("   Input size      : {} elements", nums.len());
    if let Some(sol) = outcome.solution.as_ref() {
        println!("   Solution Size   : {} elements", sol.len());
        if td <= 40 {
            let s_str: Vec<String> = sol.iter().map(|x| x.to_string()).collect();
            println!("   Solution        : [{}]", s_str.join(", "));
            let total: BigUint = sol.iter().sum();
            println!("   Sum             : {}", total);
        }
    }
    println!();
    println!("   Wall-clock time: {:.3} ms", wall.as_secs_f64() * 1000.0);
    println!("{}", "=".repeat(56));
    println!();
}
