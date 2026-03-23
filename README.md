# CNF-Token

> **Compact · Neural · Flexible Tokenizer**
> Tokenizer ultra-efisien untuk LLM — mendekati batas teoretis minimal kompresi token.

```
Copyright © 2026 Nafal Faturizki. All Rights Reserved.
Bagian dari ekosistem CENTRA-NF DSL.
Implementasi memerlukan lisensi terpisah.
```

---

## Daftar Isi

1. [Gambaran Umum](#1-gambaran-umum)
2. [Prasyarat & Lingkungan](#2-prasyarat--lingkungan)
3. [Struktur Repositori](#3-struktur-repositori)
4. [Stack Teknologi](#4-stack-teknologi)
5. [Memulai dari Nol](#5-memulai-dari-nol)
   - 5.1 [Clone & Setup Workspace](#51-clone--setup-workspace)
   - 5.2 [Membangun cnf-token-core](#52-membangun-cnf-token-core)
   - 5.3 [Membangun cnf-token-trie](#53-membangun-cnf-token-trie)
   - 5.4 [Membangun cnf-token-semantic](#54-membangun-cnf-token-semantic)
   - 5.5 [Membangun cnf-token-batch](#55-membangun-cnf-token-batch)
   - 5.6 [Membangun cnf-token-domain](#56-membangun-cnf-token-domain)
   - 5.7 [Membangun cnf-token-safety](#57-membangun-cnf-token-safety)
   - 5.8 [Membangun cnf-token-ffi](#58-membangun-cnf-token-ffi)
6. [Training Pipeline (Membangun Vocabulary)](#6-training-pipeline-membangun-vocabulary)
7. [Penggunaan API](#7-penggunaan-api)
8. [De-tokenization](#8-de-tokenization)
9. [Konfigurasi Lanjutan](#9-konfigurasi-lanjutan)
10. [Benchmark & Testing](#10-benchmark--testing)
11. [CI/CD](#11-cicd)
12. [Integrasi Ekosistem CENTRA-NF](#12-integrasi-ekosistem-centra-nf)
13. [Troubleshooting](#13-troubleshooting)
14. [Lisensi](#14-lisensi)

---

## 1. Gambaran Umum

CNF-Token adalah tokenizer generasi berikutnya yang dirancang untuk menekan konsumsi token LLM hingga mendekati batas kompresi teoretis minimal.

**Target performa:**

| Metrik | Baseline (tiktoken) | Target CNF-Token |
|--------|---------------------|------------------|
| Token / teks 50 kata | ~70 token | 0,33 token |
| Biaya / 1 juta kalimat | ~$650 | ≤ $10 |
| Throughput batch 10k | ~500k tok/s | ≥ 1M tok/s |
| Memori per 10k batch | ~50 MB | < 5 MB |

**Cara kerja singkat:**

```
Raw Text
  → [Stage 1] Pre-Processor       (normalisasi, deteksi bahasa)
  → [Stage 2] Mega-Phrase Fusion  (trie lookup + ONNX scorer)
  → [Stage 3] Ultra-Compressor    (angka/tanggal/UUID → 1 token)
  → [Stage 4] TokenId Encoder     (bit-packing + batch cache)
  → TokenId Stream
```

---

## 2. Prasyarat & Lingkungan

### Wajib

```
Rust         1.77+ (stable)      https://rustup.rs
cargo        bawaan rustup
Node.js      18+                 (untuk tools & docs saja)
Python       3.10+               (untuk training pipeline)
```

### Opsional (aktifkan fitur tertentu)

```
ONNX Runtime  1.17+   (fitur: onnx-scorer, semantic)
maturin       1.x     (fitur: python-binding)
cbindgen      0.26+   (fitur: c-binding)
```

### Instalasi Rust (jika belum ada)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustup toolchain install stable
rustup component add clippy rustfmt
```

### Verifikasi lingkungan

```bash
rustc --version   # rustc 1.77.x (atau lebih baru)
cargo --version   # cargo 1.77.x
```

---

## 3. Struktur Repositori

```
cnf-token/
├── Cargo.toml                    # workspace manifest
├── Cargo.lock
├── README.md                     # dokumen ini
├── LICENSE                       # Copyright © 2026 Nafal Faturizki
├── CHANGELOG.md
├── SPEC.md                       # ringkasan spesifikasi
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                # cargo test + clippy + bench
│   │   └── release.yml           # tag v* → crates.io publish
│   └── CODEOWNERS
│
├── crates/
│   ├── cnf-token-core/           # L1: engine inti tokenizer
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs            # public API, re-export
│   │       ├── pipeline.rs       # orkestrasi Stage 1–4
│   │       ├── pre_processor.rs  # Stage 1: normalisasi, lang detect
│   │       ├── mega_phrase.rs    # Stage 2: trie + predictive merge
│   │       ├── ultra_compressor.rs  # Stage 3: angka/tanggal/UUID
│   │       ├── token_encoder.rs  # Stage 4: bit-packing, cache
│   │       ├── token_id.rs       # TokenId type + variable-length enc
│   │       ├── detokenizer.rs    # De-tokenization (Exact/Semantic/Approx)
│   │       ├── input_guard.rs    # sanitasi input adversarial
│   │       ├── metrics.rs        # ILM, drift score, counters
│   │       └── error.rs          # CnfError enum (CNF-E001..E008)
│   │
│   ├── cnf-token-trie/           # L2: struktur data trie frekuensi
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── trie.rs           # TrieNode + lookup
│   │       ├── compact_trie.rs   # LOUDS-compressed (fitur: compact-trie)
│   │       ├── builder.rs        # ingesti corpus → trie build
│   │       └── reverse_map.rs    # HashMap<TokenId, String> untuk detokenize
│   │
│   ├── cnf-token-semantic/       # L3: semantic cluster + embedding
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── cluster.rs        # ClusterRegistry
│   │       ├── embed.rs          # 128-dim embedding via ONNX
│   │       ├── multilingual.rs   # cross-lingual cluster alignment
│   │       ├── drift_monitor.rs  # DriftMonitor + DriftReport
│   │       └── context_window.rs # long-context dependency buffer
│   │
│   ├── cnf-token-batch/          # L4: batch & streaming engine
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── batch.rs          # BatchCache + parallel (Rayon)
│   │       └── stream.rs         # async streaming + StreamConfig
│   │
│   ├── cnf-token-domain/         # L5: domain vocabulary packs
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── general.rs        # general-en, general-id
│   │       ├── technical.rs
│   │       ├── financial.rs
│   │       └── medical.rs
│   │
│   ├── cnf-token-safety/         # L6: keamanan & abuse prevention
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── content_scan.rs   # token content safety scanner
│   │       └── audit_log.rs      # structured audit trail
│   │
│   └── cnf-token-ffi/            # L7: C/Python FFI bindings
│       └── src/
│           ├── lib.rs
│           └── python.rs         # PyO3 bindings
│
├── benches/
│   ├── bench_compression.rs      # token count vs. tiktoken
│   ├── bench_throughput.rs       # tok/s, peak memory
│   ├── bench_semantic.rs         # cluster accuracy (XSTS-3)
│   └── bench_detokenize.rs       # throughput detokenisasi
│
├── tests/
│   ├── integration/
│   │   ├── pipeline_test.rs
│   │   ├── multilingual_test.rs
│   │   ├── roundtrip_test.rs     # fidelity ≥ 0.97 CI gate
│   │   └── security_test.rs      # adversarial input suite
│   └── fixtures/                 # sample corpus untuk test
│
├── tools/
│   ├── corpus-builder/           # CLI: trie dari corpus
│   ├── vocab-inspector/          # CLI: inspeksi vocab & cluster
│   └── cnf-llm-eval/             # CLI: LLM quality benchmark
│
└── docs/
    ├── spec/                     # spesifikasi teknis
    ├── architecture/
    └── api/                      # rustdoc hasil generate
```

---

## 4. Stack Teknologi

### Core Rust Crates

| Crate | Versi | Fungsi |
|-------|-------|--------|
| `tokio` | 1.x | async runtime untuk streaming tokenizer |
| `rayon` | 1.x | data-parallel batch processing |
| `ort` (onnxruntime-rs) | 2.x | ONNX inference untuk mini-LM scorer |
| `serde` + `bincode` | 1.x | serialisasi vocabulary pack |
| `ahash` + `xxhash` | latest | hashing ultra-cepat untuk BatchCache |
| `tracing` | 0.1 | structured logging & span context |
| `thiserror` | 1.x | derive macro untuk CnfError |

### Model & Data

| Komponen | Ukuran | Deskripsi |
|----------|--------|-----------|
| CLD3-lite (embedded) | < 1 MB | deteksi 50+ bahasa, tanpa network |
| MiniLM-L3 (ONNX) | < 5 MB | 128-dim semantic embedding |
| DistilBERT-tiny (ONNX) | < 8 MB | predictive merge scorer |
| Stopword lists | < 500 KB | 50+ bahasa, compiled ke binary |

### Feature Flags

```toml
# Cargo.toml (workspace level)
[features]
default     = ["trie-full", "lang-detect"]
onnx-scorer = ["ort"]             # aktifkan ONNX scorer (tambah ~13MB)
compact-trie = []                 # LOUDS-compressed trie (hemat RAM 10–20x)
context-aware = []                # long context dependency buffer
safety-scan = ["cnf-token-safety"] # content scan untuk API publik
debug-trace = []                  # trace step-by-step per stage (non-release)
python-binding = ["pyo3"]         # PyO3 Python wheel
c-binding = []                    # cbindgen C header
metrics = ["prometheus-client"]   # Prometheus-compatible metrics endpoint
no-onnx = []                      # mode tanpa ONNX untuk embedded device
```

---

## 5. Memulai dari Nol

### 5.1 Clone & Setup Workspace

```bash
# Clone repositori
git clone https://github.com/nafal-faturizki/cnf-token.git
cd cnf-token

# Verifikasi semua crate terdeteksi
cargo metadata --no-deps --format-version 1 | \
  python3 -c "import json,sys; [print(p['name']) for p in json.load(sys.stdin)['packages']]"

# Output yang diharapkan:
# cnf-token-core
# cnf-token-trie
# cnf-token-semantic
# cnf-token-batch
# cnf-token-domain
# cnf-token-safety
# cnf-token-ffi
```

**Isi `Cargo.toml` workspace:**

```toml
[workspace]
resolver = "2"
members = [
    "crates/cnf-token-core",
    "crates/cnf-token-trie",
    "crates/cnf-token-semantic",
    "crates/cnf-token-batch",
    "crates/cnf-token-domain",
    "crates/cnf-token-safety",
    "crates/cnf-token-ffi",
    "tools/corpus-builder",
    "tools/vocab-inspector",
    "tools/cnf-llm-eval",
]

[workspace.dependencies]
serde       = { version = "1", features = ["derive"] }
bincode     = "1"
ahash       = "0.8"
tracing     = "0.1"
thiserror   = "1"
tokio       = { version = "1", features = ["full"] }
rayon       = "1"
```

### 5.2 Membangun cnf-token-core

Ini adalah crate pertama yang harus dibangun. Semua crate lain bergantung padanya.

**Buat `crates/cnf-token-core/Cargo.toml`:**

```toml
[package]
name        = "cnf-token-core"
version     = "0.1.0"
edition     = "2021"
authors     = ["Nafal Faturizki"]
license     = "LicenseRef-CNF"
description = "CNF-Token core tokenizer engine"

[dependencies]
serde        = { workspace = true }
bincode      = { workspace = true }
ahash        = { workspace = true }
tracing      = { workspace = true }
thiserror    = { workspace = true }
unicode-normalization = "0.1"

[features]
default      = []
debug-trace  = []
safety-scan  = ["dep:cnf-token-safety"]

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
```

**Buat `crates/cnf-token-core/src/error.rs`:**

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum CnfError {
    #[error("[CNF-E001] Vocab not found: token '{0}' tidak ada di trie dan subword fallback gagal")]
    VocabNotFound(String),

    #[error("[CNF-E002] Semantic drift terdeteksi: cosine similarity {0:.3} < threshold {1:.3}")]
    SemanticDrift(f32, f32),

    #[error("[CNF-E003] Encoding overflow: TokenId {0} melebihi 4-byte range")]
    EncodingOverflow(u64),

    #[error("[CNF-E004] Language detection gagal: confidence {0:.2} < 0.40, fallback ke 'en'")]
    LangDetectFail(f32),

    #[error("[CNF-E005] Vocab file corrupt: CRC32 tidak cocok (expected={0:#010x}, got={1:#010x})")]
    TrieCorrupt(u32, u32),

    #[error("[CNF-E006] ONNX model inference gagal: {0}")]
    ModelInferFail(String),

    #[error("[CNF-E007] BatchCache poisoned: hash collision terdeteksi pada key {0:#016x}")]
    BatchCachePoison(u64),

    #[error("[CNF-E008] Roundtrip fidelity gagal: {0:.3} < 0.90")]
    RoundtripFail(f64),

    #[error("[CNF-E009] Input terlalu besar: {bytes} bytes (max: {max} bytes)")]
    InputTooLarge { bytes: usize, max: usize },

    #[error("[CNF-E010] IO error: {0}")]
    Io(#[from] std::io::Error),
}
```

**Buat `crates/cnf-token-core/src/token_id.rs`:**

```rust
/// TokenId menggunakan variable-length encoding (mirip UTF-8):
///
/// 1-byte  (0xxxxxxx):         ID 0–127           → top 128 mega-phrases
/// 2-byte  (10xxxxxx xxxxxxxx): ID 128–16_511      → common tokens
/// 3-byte  (110xxxxx ...):      ID 16_512–2_113_663 → domain tokens
/// 4-byte  (111xxxxx ...):      ID 2_113_664+       → rare / subword
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct TokenId(pub u32);

impl TokenId {
    pub const STOP_TOKEN: TokenId = TokenId(0);
    pub const UNKNOWN:    TokenId = TokenId(1);

    pub fn encode(&self) -> Vec<u8> {
        let id = self.0;
        if id < 128 {
            vec![id as u8]
        } else if id < 16_512 {
            let id = id - 128;
            vec![0b10_000000 | (id >> 8) as u8, (id & 0xFF) as u8]
        } else if id < 2_113_664 {
            let id = id - 16_512;
            vec![
                0b110_00000 | (id >> 16) as u8,
                ((id >> 8) & 0xFF) as u8,
                (id & 0xFF) as u8,
            ]
        } else {
            let id = id - 2_113_664;
            vec![
                0b111_00000 | (id >> 24) as u8,
                ((id >> 16) & 0xFF) as u8,
                ((id >> 8) & 0xFF) as u8,
                (id & 0xFF) as u8,
            ]
        }
    }

    pub fn byte_len(&self) -> usize {
        self.encode().len()
    }

    pub fn decode(bytes: &[u8]) -> Option<(TokenId, usize)> {
        let first = *bytes.first()?;
        if first & 0b1000_0000 == 0 {
            Some((TokenId(first as u32), 1))
        } else if first & 0b0100_0000 == 0 && bytes.len() >= 2 {
            let id = (((first & 0b0011_1111) as u32) << 8) | bytes[1] as u32;
            Some((TokenId(id + 128), 2))
        } else if first & 0b0010_0000 == 0 && bytes.len() >= 3 {
            let id = (((first & 0b0001_1111) as u32) << 16)
                | ((bytes[1] as u32) << 8)
                | bytes[2] as u32;
            Some((TokenId(id + 16_512), 3))
        } else if bytes.len() >= 4 {
            let id = (((first & 0b0001_1111) as u32) << 24)
                | ((bytes[1] as u32) << 16)
                | ((bytes[2] as u32) << 8)
                | bytes[3] as u32;
            Some((TokenId(id + 2_113_664), 4))
        } else {
            None
        }
    }
}
```

**Buat `crates/cnf-token-core/src/input_guard.rs`:**

```rust
use crate::error::CnfError;

pub struct InputGuard {
    pub max_bytes:      usize,  // default: 1_048_576 (1 MB)
    pub max_codepoints: usize,  // default: 100_000
    pub max_tokens_out: usize,  // default: 10_000
}

impl Default for InputGuard {
    fn default() -> Self {
        Self {
            max_bytes:      1_048_576,
            max_codepoints: 100_000,
            max_tokens_out: 10_000,
        }
    }
}

impl InputGuard {
    pub fn sanitize<'a>(&self, input: &'a str) -> Result<&'a str, CnfError> {
        // 1. Byte length
        if input.len() > self.max_bytes {
            return Err(CnfError::InputTooLarge {
                bytes: input.len(),
                max:   self.max_bytes,
            });
        }
        // 2. Codepoint count
        if input.chars().count() > self.max_codepoints {
            return Err(CnfError::InputTooLarge {
                bytes: input.chars().count(),
                max:   self.max_codepoints,
            });
        }
        // 3. Null byte / kontrol char berbahaya
        if input.bytes().any(|b| b == 0 || b == 0x1B) {
            return Err(CnfError::VocabNotFound("null/control char in input".into()));
        }
        Ok(input)
    }
}
```

**Build dan test core:**

```bash
cargo build -p cnf-token-core
cargo test  -p cnf-token-core
```

### 5.3 Membangun cnf-token-trie

**Buat `crates/cnf-token-trie/Cargo.toml`:**

```toml
[package]
name    = "cnf-token-trie"
version = "0.1.0"
edition = "2021"

[dependencies]
cnf-token-core = { path = "../cnf-token-core" }
serde          = { workspace = true }
bincode        = { workspace = true }
ahash          = { workspace = true }
crc32fast      = "1"

[features]
compact-trie = []
```

**Buat `crates/cnf-token-trie/src/trie.rs`:**

```rust
use ahash::HashMap;
use crate::cnf_token_core::token_id::TokenId;

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct TrieNode {
    /// char (Unicode scalar) → child node index
    pub children:    HashMap<u32, usize>,
    /// Some jika node ini adalah terminal (phrase dikenal)
    pub token_id:    Option<TokenId>,
    pub frequency:   u64,
    /// bitmask domain aktif (bit 0 = general, 1 = technical, 2 = financial, 3 = medical)
    pub domain_mask: u16,
}

pub struct PhraseTrie {
    nodes: Vec<TrieNode>,
}

impl PhraseTrie {
    pub fn new() -> Self {
        Self { nodes: vec![TrieNode {
            children: HashMap::default(),
            token_id: None,
            frequency: 0,
            domain_mask: 0,
        }]}
    }

    /// Mencari phrase terpanjang yang cocok di awal `chars`.
    /// Mengembalikan (TokenId, panjang_match_dalam_chars).
    pub fn longest_match(&self, chars: &[u32]) -> Option<(TokenId, usize)> {
        let mut node_idx = 0usize;
        let mut last_match: Option<(TokenId, usize)> = None;

        for (i, &ch) in chars.iter().enumerate() {
            match self.nodes[node_idx].children.get(&ch) {
                Some(&next) => {
                    node_idx = next;
                    if let Some(tid) = self.nodes[node_idx].token_id {
                        last_match = Some((tid, i + 1));
                    }
                }
                None => break,
            }
        }
        last_match
    }
}
```

**Build trie:**

```bash
cargo build -p cnf-token-trie
cargo test  -p cnf-token-trie
```

### 5.4 Membangun cnf-token-semantic

**Buat `crates/cnf-token-semantic/Cargo.toml`:**

```toml
[package]
name    = "cnf-token-semantic"
version = "0.1.0"
edition = "2021"

[dependencies]
cnf-token-core = { path = "../cnf-token-core" }
serde          = { workspace = true }
bincode        = { workspace = true }

# ONNX runtime (opsional — aktifkan dengan fitur onnx-scorer)
[features]
onnx-scorer = ["dep:ort"]
[dependencies.ort]
version  = "2"
optional = true
```

**Buat `crates/cnf-token-semantic/src/cluster.rs`:**

```rust
use cnf_token_core::token_id::TokenId;

/// Registry semantic cluster.
/// Setiap cluster menyimpan centroid embedding 128-dimensi.
#[derive(serde::Serialize, serde::Deserialize)]
pub struct ClusterRegistry {
    /// centroid embedding untuk setiap cluster [cluster_id][dim]
    pub embeddings:  Vec<[f32; 128]>,
    pub token_ids:   Vec<TokenId>,
    /// lang_code → list of cluster_id yang aktif untuk bahasa tersebut
    pub lang_map:    std::collections::HashMap<String, Vec<usize>>,
    pub cluster_count: usize,
}

impl ClusterRegistry {
    /// Mencari cluster_id terdekat untuk embedding input.
    /// Menggunakan cosine similarity (dot product dengan normalized vectors).
    pub fn nearest(&self, embedding: &[f32; 128]) -> (usize, f32) {
        let mut best_id    = 0usize;
        let mut best_score = f32::NEG_INFINITY;

        for (id, centroid) in self.embeddings.iter().enumerate() {
            let score = dot(embedding, centroid);
            if score > best_score {
                best_score = score;
                best_id    = id;
            }
        }
        (best_id, best_score)
    }
}

fn dot(a: &[f32; 128], b: &[f32; 128]) -> f32 {
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}
```

**Buat `crates/cnf-token-semantic/src/drift_monitor.rs`:**

```rust
use std::sync::atomic::{AtomicU64, Ordering};

pub enum DriftReport {
    Ok    { drift_score: f32 },
    Alert { drift_score: f32, recommendation: DriftAction },
}

pub enum DriftAction { Recluster, ReduceThreshold, LogOnly }

pub struct DriftMonitor {
    baseline_mean: [f32; 128],
    drift_threshold: f32,         // default 0.18
    pub alert_count: AtomicU64,
}

impl DriftMonitor {
    pub fn new(baseline_mean: [f32; 128]) -> Self {
        Self {
            baseline_mean,
            drift_threshold: 0.18,
            alert_count: AtomicU64::new(0),
        }
    }

    /// Dipanggil setiap 10_000 tokenisasi oleh pipeline.
    pub fn
