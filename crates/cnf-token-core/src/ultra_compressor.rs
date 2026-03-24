use regex::Regex;
use std::sync::OnceLock;
use crate::error::CnfError;

static NUMBER_RE: OnceLock<Regex> = OnceLock::new();
static DATE_ISO_RE: OnceLock<Regex> = OnceLock::new();
static DATE_SLASH_RE: OnceLock<Regex> = OnceLock::new();
static UUID_RE: OnceLock<Regex> = OnceLock::new();

fn get_number_re() -> Result<&'static Regex, CnfError> {
    NUMBER_RE.get_or_try_init(|| Regex::new(r"^\d+(\.\d+)?$").map_err(|_| CnfError::RegexCompileError))
}

fn get_date_iso_re() -> Result<&'static Regex, CnfError> {
    DATE_ISO_RE.get_or_try_init(|| Regex::new(r"^\d{4}-\d{2}-\d{2}$").map_err(|_| CnfError::RegexCompileError))
}

fn get_date_slash_re() -> Result<&'static Regex, CnfError> {
    DATE_SLASH_RE.get_or_try_init(|| Regex::new(r"^\d{2}/\d{2}/\d{4}$").map_err(|_| CnfError::RegexCompileError))
}

fn get_uuid_re() -> Result<&'static Regex, CnfError> {
    UUID_RE.get_or_try_init(|| Regex::new(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$").map_err(|_| CnfError::RegexCompileError))
}

fn is_number(token: &str) -> Result<bool, CnfError> {
    Ok(get_number_re()?.is_match(token))
}

fn is_date(token: &str) -> Result<bool, CnfError> {
    Ok(get_date_iso_re()?.is_match(token) || get_date_slash_re()?.is_match(token))
}

fn is_uuid(token: &str) -> Result<bool, CnfError> {
    Ok(get_uuid_re()?.is_match(token))
}

pub fn compress_text(input: &[String]) -> Result<Vec<String>, CnfError> {
    let mut tokens = Vec::new();
    for value in input {
        if is_uuid(value)? {
            tokens.push("<UUID>".to_string());
        } else if is_date(value)? {
            tokens.push("<DATE>".to_string());
        } else if is_number(value)? {
            tokens.push("<NUM>".to_string());
        } else {
            tokens.push(value.clone());
        }
    }
    Ok(tokens)
}
