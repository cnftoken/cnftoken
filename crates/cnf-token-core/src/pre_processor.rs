use unicode_normalization::UnicodeNormalization;

pub fn normalize_text(input: &str) -> String {
    input.trim().to_lowercase().nfc().collect()
}
