//! Cross-run learning: remember which engines win on which problem shapes.

use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

use crate::profile::Profile;

const STORE_NAME: &str = "engine_wins.txt";

pub struct LearningStore {
    path: PathBuf,
    wins: HashMap<String, HashMap<String, u32>>,
}

impl LearningStore {
    pub fn load() -> Self {
        let path = store_path();
        let wins = fs::read_to_string(&path).map(|s| parse_store(&s)).unwrap_or_default();
        Self { path, wins }
    }

    pub fn record_win(&mut self, profile: &Profile, engine: &str) {
        let key = feature_key(profile);
        let entry = self.wins.entry(key).or_default();
        *entry.entry(engine.to_string()).or_insert(0) += 1;
        let _ = fs::create_dir_all(self.path.parent().unwrap_or(&self.path));
        let _ = fs::write(&self.path, serialize_store(&self.wins));
    }

    pub fn bias_order(&self, profile: &Profile, mut names: Vec<&'static str>) -> Vec<&'static str> {
        let key = feature_key(profile);
        let Some(counts) = self.wins.get(&key) else {
            return names;
        };
        names.sort_by(|a, b| {
            let ca = counts.get(*a).copied().unwrap_or(0);
            let cb = counts.get(*b).copied().unwrap_or(0);
            cb.cmp(&ca)
        });
        names
    }
}

fn store_path() -> PathBuf {
    let base = std::env::var("LOCALAPPDATA")
        .or_else(|_| std::env::var("HOME"))
        .unwrap_or_else(|_| ".".into());
    PathBuf::from(base).join("zpp").join(STORE_NAME)
}

fn feature_key(p: &Profile) -> String {
    format!(
        "n={}|td={}|u128={}|si={}|dens={:.3}",
        p.n,
        p.target_digits(),
        p.u128_safe(),
        p.is_super_increasing,
        p.density
    )
}

fn parse_store(s: &str) -> HashMap<String, HashMap<String, u32>> {
    let mut out: HashMap<String, HashMap<String, u32>> = HashMap::new();
    for line in s.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let Some((key, rest)) = line.split_once('\t') else {
            continue;
        };
        let mut eng: HashMap<String, u32> = HashMap::new();
        for part in rest.split(',') {
            if let Some((name, cnt)) = part.split_once('=') {
                if let Ok(n) = cnt.parse::<u32>() {
                    eng.insert(name.to_string(), n);
                }
            }
        }
        if !eng.is_empty() {
            out.insert(key.to_string(), eng);
        }
    }
    out
}

fn serialize_store(wins: &HashMap<String, HashMap<String, u32>>) -> String {
    let mut lines: Vec<String> = Vec::new();
    for (key, counts) in wins {
        let parts: Vec<String> = counts
            .iter()
            .map(|(e, c)| format!("{e}={c}"))
            .collect();
        lines.push(format!("{key}\t{}", parts.join(",")));
    }
    lines.join("\n")
}
