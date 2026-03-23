pub struct BatchCache;

impl BatchCache {
    pub fn process(items: &[u8]) -> Vec<u8> {
        items.iter().map(|b| b.wrapping_add(1)).collect()
    }

    pub fn process_bytes(bytes: &[u8]) -> Vec<u8> {
        Self::process(bytes)
    }
}
