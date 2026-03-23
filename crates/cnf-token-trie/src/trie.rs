use std::collections::HashMap;

pub struct TrieNode {
    pub children: HashMap<char, TrieNode>,
    pub end: bool,
}

impl TrieNode {
    pub fn new() -> Self {
        Self {
            children: HashMap::new(),
            end: false,
        }
    }
}

pub struct Trie {
    root: TrieNode,
}

impl Trie {
    pub fn new() -> Self {
        Self { root: TrieNode::new() }
    }

    pub fn insert(&mut self, s: &str) {
        let mut node = &mut self.root;
        for c in s.chars() {
            node = node.children.entry(c).or_insert_with(TrieNode::new);
        }
        node.end = true;
    }

    pub fn contains(&self, s: &str) -> bool {
        let mut node = &self.root;
        for c in s.chars() {
            if let Some(n) = node.children.get(&c) {
                node = n;
            } else {
                return false;
            }
        }
        node.end
    }
}
