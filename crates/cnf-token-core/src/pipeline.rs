use crate::pre_processor::normalize_text;
use crate::mega_phrase::{scan_phrases, build_trie_from_vocab};
use crate::ultra_compressor::compress_text;
use crate::token_encoder::encode_tokens;

pub fn process_text(input: &str) -> Vec<u8> {
    let normalized = normalize_text(input);
    let vocab = vec!["the", "token", "tokenizer", "cnf", "cnf-token"];
    let trie = build_trie_from_vocab(&vocab);
    let phrases = scan_phrases(&normalized, &trie);
    let compressed = compress_text(&phrases);
    encode_tokens(&compressed)
}
