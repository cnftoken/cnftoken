pub mod pipeline;
pub mod pre_processor;
pub mod mega_phrase;
pub mod ultra_compressor;
pub mod token_encoder;
pub mod token_id;
pub mod detokenizer;
pub mod input_guard;
pub mod metrics;
pub mod error;
pub mod onnx_scorer;

pub use pipeline::process_text;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stage2_phrase_scan_tokenizer() {
        let trie = mega_phrase::build_trie_from_vocab(&["cnf-token", "tokenizer", "core"]);
        let got = mega_phrase::scan_phrases("cnf-token tokenizer core unknown", &trie);
        assert_eq!(got, vec!["cnf-token".to_string(), "tokenizer".to_string(), "core".to_string(), "unknown".to_string()]);
    }

    #[test]
    fn process_text_works() {
        let encoded = process_text("CNF-Token tokenizer");
        assert!(!encoded.is_empty());

        // Ensure encoded output is re-encoded in token-id varint form
        let mut cursor = 0;
        let mut ids = vec![];
        while cursor < encoded.len() {
            let (id, size) = token_id::decode_id(&encoded[cursor..]).expect("decode should succeed");
            ids.push(id);
            cursor += size;
        }
        assert!(ids.len() >= 2);
    }

    #[test]
    fn stage3_ultra_compress_special_tokens() {
        let items = vec![
            "2025-12-31".to_string(),
            "12/31/2025".to_string(),
            "42".to_string(),
            "123.45".to_string(),
            "550e8400-e29b-41d4-a716-446655440000".to_string(),
            "normal".to_string(),
        ];
        let out = ultra_compressor::compress_text(&items);
        assert!(out.contains("<DATE>"));
        assert!(out.contains("<NUM>"));
        assert!(out.contains("<UUID>"));
    }

    #[test]
    fn stage4_token_id_encode_decode() {
        let enc = token_id::encode_id(300);
        let decoded = token_id::decode_id(&enc).unwrap();
        assert_eq!(decoded.0, 300);
        assert_eq!(decoded.1, enc.len());
    }

    #[test]
    fn stage4_token_encoder_batch_cache() {
        let (out, map) = token_encoder::encode_tokens_with_map("cnf-token_2025-12-31_42");
        assert!(!out.is_empty());

        let decoded = detokenizer::detokenize_bytes(&out, &map);
        assert!(decoded.contains("cnf-token") || decoded.contains("<ID:"));

        let mut idx = 0;
        while idx < out.len() {
            let (id, size) = token_id::decode_id(&out[idx..]).unwrap();
            assert!(id >= 1);
            idx += size;
        }
    }
}

