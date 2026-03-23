use std::collections::HashMap;

pub struct ClusterRegistry {
    clusters: HashMap<String, Vec<String>>,
}

impl ClusterRegistry {
    pub fn new() -> Self {
        Self { clusters: HashMap::new() }
    }

    pub fn register(&mut self, key: &str, values: Vec<&str>) {
        self.clusters.insert(key.to_string(), values.iter().map(|v| v.to_string()).collect());
    }
}
