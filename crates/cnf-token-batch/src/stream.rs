pub struct StreamConfig {
    pub batch_size: usize,
}

impl StreamConfig {
    pub fn new(batch_size: usize) -> Self { Self { batch_size } }
}
