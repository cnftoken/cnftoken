use criterion::{black_box, criterion_group, criterion_main, Criterion};
use cnf_token_core::mega_phrase::scan_phrases;
use cnf_token_core::mega_phrase::build_trie_from_vocab;

pub fn bench_compression(c: &mut Criterion) {
    let sample = "cnf-token tokenizer core fast tokenization performance".repeat(50);
    let trie = build_trie_from_vocab(&["cnf-token", "tokenizer", "core", "performance"]);

    c.bench_function("scan_phrases", |b| {
        b.iter(|| {
            let phrases = scan_phrases(black_box(&sample), &trie);
            black_box(phrases);
        })
    });
}

criterion_group!(benches, bench_compression);
criterion_main!(benches);
