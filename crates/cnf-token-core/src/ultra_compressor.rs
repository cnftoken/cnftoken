use regex::Regex;

fn is_number(token: &str) -> bool {
    let re = Regex::new(r"^\d+(\.\d+)?$").unwrap();
    re.is_match(token)
}

fn is_date(token: &str) -> bool {
    let re_iso = Regex::new(r"^\d{4}-\d{2}-\d{2}$").unwrap();
    let re_slash = Regex::new(r"^\d{2}/\d{2}/\d{4}$").unwrap();
    re_iso.is_match(token) || re_slash.is_match(token)
}

fn is_uuid(token: &str) -> bool {
    let re = Regex::new(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$").unwrap();
    re.is_match(token)
}

pub fn compress_text(input: &[String]) -> String {
    let tokens: Vec<String> = input
        .iter()
        .map(|value| {
            if is_uuid(value) {
                "<UUID>".to_string()
            } else if is_date(value) {
                "<DATE>".to_string()
            } else if is_number(value) {
                "<NUM>".to_string()
            } else {
                value.clone()
            }
        })
        .collect();

    tokens.join("_")
}
