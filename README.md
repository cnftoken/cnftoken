# CNF-Token

> **Compact · Neural · Flexible Tokenizer**
> Tokenizer ultra-efisien untuk LLM — mendekati batas teoretis minimal kompresi token.

```
Copyright © 2026 Nafal Faturizki. All Rights Reserved.
Bagian dari ekosistem CENTRA-NF DSL.
Implementasi memerlukan lisensi terpisah.
```

---

## Status Implementasi

✅ **Selesai (Stage 1-4 Pipeline)**
- Stage 1: Pre-Processor (normalisasi, deteksi bahasa)
- Stage 2: Mega-Phrase Fusion (trie lookup + ONNX scorer)
- Stage 3: Ultra-Compressor (angka/tanggal/UUID → 1 token)
- Stage 4: TokenId Encoder (varint encoding + batch cache)
- Governance system (policy engine + guard validators)
- Benchmarks (criterion 0.2.11 compat. dengan Rust 1.75)
- Integration tests (Python + Rust)

### Target Performa
| Metrik | Baseline | Target |
|--------|----------|--------|
| Token/50-word text | ~70 token | ≤1 token |
| Throughput (batch 10k) | 500k tok/s | ≥1M tok/s |

---

## Prasyarat

- **Rust 1.80+** (ideal) atau Rust 1.75+ (dengan workaround)
- **Python 3.10+**
- **Cargo**

### ⚠️ Catatan Rust 1.75
Jika Anda gunakan **rustc 1.75**, jalankan tests dengan flag:
```bash
cargo test --workspace --no-default-features
cargo bench --no-default-features
```

Workaround ini diperlukan karena dependency `criterion` memerlukan `rayon-core 1.13.0+` yang butuh Rust 1.80+.
Kami sudah downgrade ke `criterion 0.2.11` + `rayon 1.0.3` untuk kompatibilitas.

---

## Quick Start

### 1. Run Tests
```bash
# Rust tests (dengan workaround 1.75)
cargo test --workspace --no-default-features -- --nocapture

# Python tests
env PYTHONPATH=. pytest -q

# Governance checks
python main.py
```

### 2. Run Benchmarks
```bash
cargo bench --no-default-features -- --quiet
```

### 3. Validate Policy
```bash
python policy/engine.py
```

---

## Struktur Repository

```
cnftoken/
├── crates/                           # Rust multi-crate workspace
│   ├── cnf-token-core/               # Pipeline: stages 1-4
│   │   ├── src/
│   │   │   ├── lib.rs               # Module exports
│   │   │   ├── pipeline.rs          # End-to-end flow
│   │   │   ├── pre_processor.rs     # Stage 1: normalisasi
│   │   │   ├── mega_phrase.rs       # Stage 2: trie + scoring
│   │   │   ├── ultra_compressor.rs  # Stage 3: special tokens
│   │   │   ├── token_id.rs          # Varint encode/decode
│   │   │   ├── token_encoder.rs     # Token ID mapping + batch
│   │   │   ├── detokenizer.rs       # Reverse mapping
│   │   │   ├── onnx_scorer.rs       # ONNX stub (fallback heuristic)
│   │   │   └── tests: stage2_phrase_scan_tokenizer, stage3_ultra_compress_special_tokens, stage4_token_id_encode_decode, stage4_token_encoder_batch_cache, process_text_works
│   │   └── benches/
│   │       ├── bench_throughput.rs  # process_text throughput
│   │       └── bench_compression.rs # scan_phrases compression
│   │
│   ├── cnf-token-trie/               # Trie data structure
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── trie.rs              # Trie implementation
│   │       ├── compact_trie.rs      # Compact variant
│   │       ├── builder.rs           # Trie construction
│   │       └── reverse_map.rs       # Reverse lookup
│   │
│   ├── cnf-token-batch/              # Batch processing
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── batch.rs             # Batch transform
│   │       └── stream.rs            # Stream processing
│   │
│   ├── cnf-token-semantic/           # Semantic analysis
│   │   └── src/
│   │       └── [drift_monitor, context_window modules]
│   │
│   ├── cnf-token-domain/             # Domain-specific tokens
│   │   └── src/
│   │       └── [financial, technical, medical, general modules]
│   │
│   ├── cnf-token-safety/             # Safety & auditing
│   │   └── src/
│   │       └── [audit_log, content_scan modules]
│   │
│   └── cnf-token-ffi/                # Python FFI bindings
│       └── src/
│           └── [python.rs wrapper]
│
├── policy/                           # Governance
│   ├── rules.yaml                   # Policy rules
│   └── engine.py                    # Policy enforcement
│
├── guard/                            # Validators
│   ├── hash_validator.py
│   ├── change_validator.py
│   ├── dual_validator.py
│   └── drift_validator.py
│
├── core/                             # Immutable marker
│   └── __init__.py
│
├── tests/                            # Python integration tests
│   ├── test_policy_engine.py
│   ├── test_guard_system.py
│   ├── integration/
│   │   ├── pipeline_test.py
│   │   ├── roundtrip_test.py
│   │   ├── multilingual_test.py
│   │   └── security_test.py
│   └── ... (other Python tests)
│
├── benches/                          # Top-level Criterion benchmarks
│   ├── bench_throughput.rs
│   └── bench_compression.rs
│
├── main.py                           # Orchestrator
├── Cargo.toml                        # Workspace + dependency pins
└── .github/workflows/ci.yml          # CI/CD configuration

```

---

## Modul Rust Utama

### cnf-token-core
- **pipeline::process_text(text: &str) → Vec<u8>**: End-to-end tokenization
- **mega_phrase::scan_phrases(text: &str, trie: &Trie) → Vec<String>**
- **ultra_compressor::compress_text(items: &[String]) → String**
- **token_id::{encode_id, decode_id}**: Varint encoding/decoding
- **token_encoder::encode_tokens_with_map(text: &str) → (Vec<u8>, Map)**
- **detokenizer::detokenize_bytes(bytes: &[u8], map: &Map) → String**

### cnf-token-trie
- **Trie::new() / insert() / contains()**
- **reverse_map::ReverseMap** untuk lookups balik

### cnf-token-batch
- **BatchTransform::apply()**: Transform dataset batch

---

## Testing

### Unit Tests (Rust)
```bash
cargo test -p cnf-token-core --no-default-features
```
**Result**: 5 passed (stage2, stage3, stage4, process_text)

### Integration Tests (Python)
```bash
env PYTHONPATH=. pytest -v
```
**Result**: 10 passed, 3 skipped

### Governance Checks (Python)
```bash
python main.py
```
Validates:
- Policy compliance (rules.yaml)
- Guard validators (hash, change, dual, drift)
- Core immutability

---

## Benchmarks (Rust)

```bash
cargo bench --no-default-features
```

### Available Benches
- `bench_throughput`: process_text throughput performance
- `bench_compression`: scan_phrases compression ratio

**Note**: Menggunakan criterion 0.2.11 (Rust 1.75 compat.) — hasilnya "basic" tanpa fitur plot.
Untuk full features, upgrade ke Rust 1.80+ dan gunakan `criterion 0.3`+.

---

## CI/CD

### GitHub Actions (.github/workflows/ci.yml)
1. Python tests (pytest)
2. Governance checks (main.py)
3. Cargo tests with `--no-default-features` (Rust 1.75 safe)
4. Benchmarks
5. Formatting checks (pre-commit)

**Trigger**: Push ke `main` atau PR targeting `main`

---

## Pengembangan Lanjutan

### Menjalankan Dengan Rust 1.80+ (Ideal)
```bash
rustup default stable  # Switch ke latest stable
cargo test --workspace
cargo bench
```
Ini akan menggunakan `criterion 0.3+` dengan fitur penuh.

### Menambah Domain Baru (cnf-token-domain)
```rust
// crates/cnf-token-domain/src/lib.rs
pub mod mydomain;

// crates/cnf-token-domain/src/mydomain.rs
pub fn tokenize_mydomain(text: &str) -> Vec<u8> {
    // Custom logic
}
```

### Enablement ONNX Scorer (Feature Gate)
```bash
cargo test --workspace --no-default-features --features onnx-scorer
```

---

## Troubleshooting

### "rayon-core requires rustc 1.80+"
→ Gunakan `cargo test --workspace --no-default-features`
→ atau upgrade ke Rust 1.80+ dengan `rustup default stable`

### "criterion not found in benches"
→ File Cargo.toml sudah punya `criterion = "0.2.11"` di `[dev-dependencies]`
→ Run: `cargo build --benches` dahulu

### Python import error "ModuleNotFoundError: core"
→ Run with: `env PYTHONPATH=. pytest`

### Pre-commit hooks gagal
→ Run: `pre-commit run --all-files`

---

## Lisensi

© 2026 Nafal Faturizki. Eksklusif; lisensi terpisah diperlukan.

---

## Referensi

- [Rust Edition 2021](https://doc.rust-lang.org/edition-guide/rust-2021/index.html)
- [Criterion.rs Docs](https://bheisler.github.io/criterion.rs/book/)
- [Python Policy Engine](./policy/engine.py)
- [README.md - Stage Details](./README.md)
