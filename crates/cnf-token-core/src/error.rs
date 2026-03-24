use thiserror::Error;

#[derive(Error, Debug)]
pub enum CnfError {
    #[error("CNF-E001: invalid input")]
    InvalidInput,
    #[error("CNF-E002: invalid token ID")]
    InvalidTokenId,
    #[error("CNF-E003: regex compilation failed")]
    RegexCompileError,
    #[error("CNF-E004: decode error")]
    DecodeError,
    #[error("CNF-E005: token not found")]
    TokenNotFound,
    #[error("CNF-E006: invalid UTF-8")]
    InvalidUtf8,
    #[error("CNF-E007: normalization failed")]
    NormalizationError,
    #[error("CNF-E008: trie operation failed")]
    TrieError,
    #[error("CNF-E009: batch processing error")]
    BatchError,
    #[error("CNF-E010: I/O error")]
    IoError(#[from] std::io::Error),
}
