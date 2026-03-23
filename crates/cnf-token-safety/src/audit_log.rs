use std::fs::OpenOptions;
use std::io::Write;

pub fn log_event(event: &str) -> std::io::Result<()> {
    let mut file = OpenOptions::new().create(true).append(true).open("audit.log")?;
    writeln!(file, "{}", event)
}
