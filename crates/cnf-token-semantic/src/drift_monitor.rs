pub struct DriftReport {
    pub drift_score: f64,
}

pub struct DriftMonitor;

impl DriftMonitor {
    pub fn new() -> Self { Self }
    pub fn report(&self, _score: f64) -> DriftReport { DriftReport { drift_score: _score } }
}
