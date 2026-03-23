#[cfg(feature = "python-binding")]
pub fn init_python_binding() -> &'static str {
    "python-binding initialized"
}

#[cfg(not(feature = "python-binding"))]
pub fn init_python_binding() -> &'static str {
    "python-binding disabled"
}
