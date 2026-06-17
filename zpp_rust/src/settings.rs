use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

const CONFIG_PATH: &str = "algorithm_config.json";

#[derive(Clone, Serialize, Deserialize)]
pub struct EngineSettings {
    pub enabled: HashMap<String, bool>,
    pub priority: HashMap<String, f64>,
    pub timeout_secs: u64,
    pub max_engines: usize,
}

impl Default for EngineSettings {
    fn default() -> Self {
        let mut enabled = HashMap::new();
        let mut priority = HashMap::new();
        let all = crate::scheduler::all_engine_names();
        for e in all {
            enabled.insert(e.to_string(), true);
            priority.insert(e.to_string(), 50.0);
        }
        Self { enabled, priority, timeout_secs: 300, max_engines: 20 }
    }
}

impl EngineSettings {
    pub fn load() -> Self {
        let path = Self::path();
        if path.exists() {
            fs::read_to_string(&path)
                .ok()
                .and_then(|s| serde_json::from_str(&s).ok())
                .unwrap_or_default()
        } else {
            Self::default()
        }
    }

    pub fn save(&self) {
        if let Ok(json) = serde_json::to_string_pretty(self) {
            let _ = fs::write(Self::path(), &json);
        }
    }

    fn path() -> PathBuf {
        let home = std::env::var("USERPROFILE")
            .or_else(|_| std::env::var("HOME"))
            .unwrap_or_else(|_| ".".to_string());
        PathBuf::from(home).join(CONFIG_PATH)
    }
}
