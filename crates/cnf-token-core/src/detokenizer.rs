use std::collections::HashMap;

use crate::token_id::decode_id;

pub fn detokenize_bytes(bytes: &[u8], reverse_map: &HashMap<u32, String>) -> String {
    let mut idx = 0;
    let mut output = Vec::new();
    while idx < bytes.len() {
        if let Some((id, used)) = decode_id(&bytes[idx..]) {
            if let Some(tok) = reverse_map.get(&id) {
                output.push(tok.clone());
            } else {
                output.push(format!("<ID:{}>", id));
            }
            idx += used;
        } else {
            break;
        }
    }
    output.join(" ")
}

pub fn detokenize(data: &[u8]) -> String {
    String::from_utf8_lossy(data).into_owned().replace("_", " ")
}
