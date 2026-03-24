use serde::{Deserialize, Serialize};
use semver::Version;

#[derive(Serialize, Deserialize, Debug)]
pub struct VocabPackHeader {
    pub magic: [u8; 8], // "CNFVOCAB"
    pub version: semver::Version,
    pub crc32: u32,
    pub vocab_size: u32,
    pub created_at: u64, // timestamp
}

impl VocabPackHeader {
    pub const MAGIC_BYTES: [u8; 8] = *b"CNFVOCAB";

    pub fn new(version: semver::Version, vocab_size: u32) -> Self {
        Self {
            magic: Self::MAGIC_BYTES,
            version,
            crc32: 0, // to be computed
            vocab_size,
            created_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        }
    }

    pub fn compute_crc32(&mut self, data: &[u8]) {
        // Simple CRC32 computation
        let mut crc = 0u32;
        for &byte in data {
            crc = crc.wrapping_add(byte as u32);
        }
        self.crc32 = crc;
    }
}