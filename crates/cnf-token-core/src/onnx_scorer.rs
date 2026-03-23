#[cfg(feature = "onnx-scorer")]
pub fn score_phrase(_phrase: &str) -> f64 {
    // stub for ONNX-based scoring; returns high for longer phrase
    _phrase.len() as f64
}

#[cfg(not(feature = "onnx-scorer"))]
pub fn score_phrase(_phrase: &str) -> f64 {
    // fallback local heuristic
    _phrase.len() as f64
}
