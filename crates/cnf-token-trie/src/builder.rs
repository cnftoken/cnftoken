use crate::trie::Trie;

pub fn build_trie(tokens: &[&str]) -> Trie {
    let mut trie = Trie::new();
    for t in tokens {
        trie.insert(t);
    }
    trie
}
