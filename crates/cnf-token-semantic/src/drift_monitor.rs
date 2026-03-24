use super::embed::{embed_text, cosine_similarity};

pub struct DriftReport {
    pub drift_score: f64,
}

pub struct DriftMonitor {
    baseline_embedding: Vec<f32>,
}

impl DriftMonitor {
    pub fn new(baseline_text: &str) -> Self {
        let baseline_embedding = embed_text(baseline_text);
        Self { baseline_embedding }
    }

    pub fn report(&self, current_text: &str) -> DriftReport {
        let current_embedding = embed_text(current_text);
        let similarity = cosine_similarity(&self.baseline_embedding, &current_embedding);
        let drift_score = 1.0 - similarity as f64; // higher drift = lower similarity
        DriftReport { drift_score }
    }
}
