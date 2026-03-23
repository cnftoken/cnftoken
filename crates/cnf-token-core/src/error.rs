use thiserror::Error;

#[derive(Error, Debug)]
pub enum CnfError {
    #[error("CNF-E001: invalid input")]
    InvalidInput,
}
