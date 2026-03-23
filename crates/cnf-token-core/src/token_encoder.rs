use std::collections::HashMap;

use crate::token_id::{encode_id, TokenId};

pub struct TokenEncoder {
    dictionary: HashMap<String, TokenId>,
    reverse_dictionary: HashMap<TokenId, String>,
    next_id: TokenId,
}

impl TokenEncoder {
    pub fn new() -> Self {
        Self {
            dictionary: HashMap::new(),
            reverse_dictionary: HashMap::new(),
            next_id: 1,
        }
    }

    fn token_to_id(&mut self, token: &str) -> TokenId {
        if let Some(&id) = self.dictionary.get(token) {
            return id;
        }
        let id = self.next_id;
        self.next_id += 1;
        self.dictionary.insert(token.to_string(), id);
        self.reverse_dictionary.insert(id, token.to_string());
        id
    }

    pub fn encode(&mut self, input: &str) -> Vec<u8> {
        let tokens: Vec<&str> = input.split('_').collect();
        let mut out = Vec::new();
        for tok in tokens {
            let id = self.token_to_id(tok);
            out.extend(encode_id(id));
        }
        out
    }

    pub fn get_reverse_map(&self) -> HashMap<TokenId, String> {
        self.reverse_dictionary.clone()
    }
}

pub fn encode_tokens(input: &str) -> Vec<u8> {
    let mut encoder = TokenEncoder::new();
    let encoded = encoder.encode(input);
    // apply batch cache processor from L4 crate
    cnf_token_batch::BatchCache::process_bytes(&encoded)
}

pub fn encode_tokens_with_map(input: &str) -> (Vec<u8>, HashMap<TokenId, String>) {
    let mut encoder = TokenEncoder::new();
    let encoded = encoder.encode(input);
    let map = encoder.get_reverse_map();
    let result = cnf_token_batch::BatchCache::process_bytes(&encoded);
    (result, map)
}

