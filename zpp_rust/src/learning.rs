//! Cross-run learning: remember which engines win on which problem shapes.
//! Writes to disk lazily (on Drop) to avoid I/O on every win.

use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

use crate::profile::Profile;

const STORE_NAME: &str = "engine_wins.txt";

pub struct LearningStore {
    path: PathBuf,
    wins: HashMap<String, HashMap<String, u32>>,
    dirty: bool,
}

impl LearningStore {
    pub fn load() -> Self {
        let path = store_path();
        let wins = fs::read_to_string(&path).ok().map(|s| parse_store(&s)).unwrap_or_default();
        Self { path, wins, dirty: false }
    }

    pub fn record_win(&mut self, profile: &Profile, engine: &str) {
        let key = feature_key(profile);
        let entry = self.wins.entry(key).or_default();
        *entry.entry(engine.to_string()).or_insert(0) += 1;
        self.dirty = true;
    }

    pub fn flush(&mut self) {
        if !self.dirty { return; }
        let _ = fs::create_dir_all(self.path.parent().unwrap_or(&self.path));
        let _ = fs::write(&self.path, serialize_store(&self.wins));
        self.dirty = false;
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

    /// Return a score boost (0.0–50.0) for each engine based on past wins.
    /// Used by the scheduler to reorder engines adaptively.
    pub fn score_boost(&self, profile: &Profile, engine: &str) -> f64 {
        let key = feature_key(profile);
        let Some(counts) = self.wins.get(&key) else {
            return 0.0;
        };
        let count = counts.get(engine).copied().unwrap_or(0);
        if count == 0 {
            return 0.0;
        }
        // Scale: 1 win = +5.0, 5+ wins = +50.0 (enough to jump to top).
        (count as f64).min(10.0) * 5.0
    }
}

impl Drop for LearningStore {
    fn drop(&mut self) {
        self.flush();
    }
}

fn store_path() -> PathBuf {
    let base = std::env::var("LOCALAPPDATA")
        .or_else(|_| std::env::var("HOME"))
        .unwrap_or_else(|_| ".".into());
    PathBuf::from(base).join("zpp").join(STORE_NAME)
}

fn feature_key(profile: &Profile) -> String {
    format!("n={},bits={},dense={:.2}", profile.n, profile.target.bits(), profile.density)
}

fn parse_store(s: &str) -> HashMap<String, HashMap<String, u32>> {
    let mut map: HashMap<String, HashMap<String, u32>> = HashMap::new();
    for line in s.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if let Some(eq) = line.find('=') {
            let key = line[..eq].trim().to_string();
            let val = line[eq + 1..].trim();
            if let Some(pipe) = key.rfind('|') {
                let feat = key[..pipe].to_string();
                let ename = key[pipe + 1..].to_string();
                let count: u32 = val.parse().unwrap_or(0);
                map.entry(feat).or_default().insert(ename, count);
            }
        }
    }
    map
}

fn serialize_store(wins: &HashMap<String, HashMap<String, u32>>) -> String {
    let mut lines: Vec<String> = Vec::new();
    lines.push("# Z++ LearningStore: feature|engine=count".to_string());
    let mut pairs: Vec<(String, String, u32)> = Vec::new();
    for (feat, engs) in wins {
        for (eng, cnt) in engs {
            pairs.push((feat.clone(), eng.clone(), *cnt));
        }
    }
    pairs.sort_by(|a, b| b.2.cmp(&a.2));
    for (feat, eng, cnt) in pairs {
        lines.push(format!("{}|{}={}", feat, eng, cnt));
    }
    lines.join("\n")
}
