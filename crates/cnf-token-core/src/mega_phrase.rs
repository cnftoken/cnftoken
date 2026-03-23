use cnf_token_trie::Trie;

use crate::onnx_scorer::score_phrase;

pub fn build_trie_from_vocab(vocab: &[&str]) -> Trie {
    let mut trie = Trie::new();
    for token in vocab {
        trie.insert(token);
    }
    trie
}

pub fn scan_phrases(input: &str, trie: &Trie) -> Vec<String> {
    let words: Vec<&str> = input.split_whitespace().collect();
    let mut output = Vec::new();
    let mut i = 0;
    while i < words.len() {
        let mut best_match = None;
        let mut best_score = 0.0;
        let mut best_len = 0;
        let mut phrase_builder = String::new();

        for j in i..words.len() {
            if !phrase_builder.is_empty() {
                phrase_builder.push(' ');
            }
            phrase_builder.push_str(words[j]);

            if trie.contains(&phrase_builder) {
                let score = score_phrase(&phrase_builder);
                if score > best_score {
                    best_match = Some(phrase_builder.clone());
                    best_score = score;
                    best_len = j - i + 1;
                }
            }
        }

        if let Some(matched) = best_match {
            output.push(matched);
            i += best_len;
        } else {
            output.push(words[i].to_string());
            i += 1;
        }
    }

    output
}
