use std::collections::HashMap;

pub fn reverse_map(tokens: &[(&str, u32)]) -> HashMap<u32, String> {
    tokens.iter().map(|(s, id)| (*id, s.to_string())).collect()
}

pub fn lookup(token_id: u32, map: &HashMap<u32, String>) -> Option<&String> {
    map.get(&token_id)
}
