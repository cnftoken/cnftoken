use tracing::{info, error};
use std::env;

pub fn init_audit_log() {
    let log_path = env::var("CNF_AUDIT_LOG_PATH").unwrap_or_else(|_| "audit.log".to_string());
    // Assume tracing is set up elsewhere
}

pub fn log_event(event: &str) {
    info!("Audit: {}", event);
}

pub fn log_error(err: &str) {
    error!("Audit Error: {}", err);
}
