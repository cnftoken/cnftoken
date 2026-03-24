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
pub mod vocab_pack;
pub mod cnf_tokenizer;

pub use pipeline::process_text;
pub use cnf_tokenizer::CnfTokenizer;

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
        let encoded = process_text("CNF-Token tokenizer").unwrap();
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
        let out = ultra_compressor::compress_text(&items).unwrap();
        assert!(out.contains(&"<DATE>".to_string()));
        assert!(out.contains(&"<NUM>".to_string()));
        assert!(out.contains(&"<UUID>".to_string()));
    }

    #[test]
    fn stage4_token_id_encode_decode() {
        let enc = token_id::encode_id(300);
        let decoded = token_id::decode_id(&enc).expect("decode should succeed");
        assert_eq!(decoded.0, 300);
        assert_eq!(decoded.1, enc.len());
    }

    #[test]
    fn stage4_token_encoder_batch_cache() {
        let input_tokens = vec!["cnf-token".to_string(), "2025-12-31".to_string(), "42".to_string()];
        let (out, map) = token_encoder::encode_tokens_with_map(&input_tokens).unwrap();
        assert!(!out.is_empty());

        let decoded = detokenizer::detokenize_bytes(&out, &map);
        assert!(decoded.contains("cnf-token") || decoded.contains("<ID:"));

        let mut idx = 0;
        while idx < out.len() {
            let (id, size) = token_id::decode_id(&out[idx..]).unwrap();
            assert!(id >= 1);
            idx += size;
    #[test]
    fn roundtrip_fidelity_test() {
        let test_texts = vec![
            "Hello world",
            "This is a test sentence for roundtrip fidelity.",
            "CNF token compression should maintain high accuracy.",
        ];

        for text in test_texts {
            let encoded = process_text(text).unwrap();
            let map = token_encoder::encode_tokens_with_map(&vec![text.to_string()]).unwrap().1;
            let decoded = detokenizer::detokenize_bytes(&encoded, &map);
            let ilm = metrics::ilm_score(text, &decoded);
            assert!(ilm <= 0.15, "ILM score {} > 0.15 for text: {}", ilm, text);
        }
    }

