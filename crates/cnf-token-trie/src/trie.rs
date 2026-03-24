use std::collections::HashMap;

pub type TokenId = u32;

pub struct TrieNode {
    pub children: HashMap<char, TrieNode>,
    pub end: bool,
    pub token_id: Option<TokenId>,
    pub frequency: u32,
    pub domain_mask: u32,
}

impl TrieNode {
    pub fn new() -> Self {
        Self {
            children: HashMap::new(),
            end: false,
            token_id: None,
            frequency: 0,
            domain_mask: 0,
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

    pub fn longest_match(&self, s: &str) -> Option<(String, TokenId)> {
        let mut node = &self.root;
        let mut last_end = None;
        let mut matched = String::new();
        let mut chars = s.chars().peekable();
        while let Some(c) = chars.next() {
            if let Some(n) = node.children.get(&c) {
                matched.push(c);
                node = n;
                if node.end {
                    if let Some(id) = node.token_id {
                        last_end = Some((matched.clone(), id));
                    }
                }
            } else {
                break;
            }
        }
        last_end
    }
}
