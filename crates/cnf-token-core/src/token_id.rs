pub type TokenId = u32;

pub fn encode_id(val: TokenId) -> Vec<u8> {
    // variable-length 7-bit packing for u32
    let mut n = val;
    let mut out = Vec::new();
    while n >= 0x80 {
        out.push(((n & 0x7F) as u8) | 0x80);
        n >>= 7;
    }
    out.push((n & 0x7F) as u8);
    out
}

pub fn decode_id(bytes: &[u8]) -> Option<(TokenId, usize)> {
    let mut value: u32 = 0;
    let mut shift = 0;
    for (i, b) in bytes.iter().enumerate() {
        let part = (b & 0x7F) as u32;
        value |= part << shift;
        if b & 0x80 == 0 {
            return Some((value, i + 1));
        }
        shift += 7;
        if shift >= 32 {
            return None;
        }
    }
    None
}
