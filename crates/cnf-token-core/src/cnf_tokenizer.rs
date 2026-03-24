use std::fs::File;
use std::io::Read;
use std::path::Path;
use crate::vocab_pack::VocabPackHeader;
use cnf_token_trie::Trie;
use crate::error::CnfError;

#[derive(Debug)]
pub struct CnfTokenizerConfig {
    pub vocab_path: String,
    pub max_vocab_size: usize,
}

#[derive(Debug)]
pub struct CnfTokenizer {
    pub vocab: Trie,
    pub config: CnfTokenizerConfig,
}

impl CnfTokenizer {
    pub fn new(config: CnfTokenizerConfig) -> Result<Self, CnfError> {
        let vocab = Self::load_vocab(&config.vocab_path)?;
        Ok(Self { vocab, config })
    }

    fn load_vocab(path: &str) -> Result<Trie, CnfError> {
        let mut file = File::open(path).map_err(CnfError::IoError)?;
        let mut buffer = Vec::new();
        file.read_to_end(&mut buffer).map_err(CnfError::IoError)?;

        // Parse header
        let header_size = std::mem::size_of::<VocabPackHeader>();
        if buffer.len() < header_size {
            return Err(CnfError::InvalidInput);
        }
        let header: VocabPackHeader = bincode::deserialize(&buffer[..header_size])
            .map_err(|_| CnfError::InvalidInput)?;

        if header.magic != VocabPackHeader::MAGIC_BYTES {
            return Err(CnfError::InvalidInput);
        }

        // Load vocab words
        let vocab_data = &buffer[header_size..];
        let vocab_words: Vec<String> = bincode::deserialize(vocab_data)
            .map_err(|_| CnfError::InvalidInput)?;

        let mut trie = Trie::new();
        for word in vocab_words {
            trie.insert(&word);
        }

        Ok(trie)
    }
}