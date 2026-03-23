use criterion::{black_box, criterion_group, criterion_main, Criterion};
use cnf_token_core::process_text;

pub fn bench_throughput(c: &mut Criterion) {
    let sample = "cnf-token tokenizer core 2025-12-31 42".repeat(1000);

    c.bench_function("process_text_throughput", move |b| {
        b.iter(|| {
            let out = process_text(black_box(&sample));
            black_box(out);
        })
    });
}

criterion_group!(benches, bench_throughput);
criterion_main!(benches);
