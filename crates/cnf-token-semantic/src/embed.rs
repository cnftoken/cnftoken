use std::collections::HashMap;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

pub fn embed_text(text: &str) -> Vec<f32> {
    let mut tf: HashMap<u32, f32> = HashMap::new();
    let words: Vec<&str> = text.split_whitespace().collect();
    let total_words = words.len() as f32;

    for word in words {
        let hash = hash_word(word);
        *tf.entry(hash).or_insert(0.0) += 1.0;
    }

    // Normalize TF
    for count in tf.values_mut() {
        *count /= total_words;
    }

    // Simple IDF approximation (assume common words have lower IDF)
    let mut embedding = vec![0.0; 128];
    for (hash, tf_val) in tf {
        let idx = (hash % 128) as usize;
        let idf = 1.0 / (1.0 + (hash % 10) as f32); // simple approximation
        embedding[idx] += tf_val * idf;
    }

    // Normalize to unit vector
    let norm = (embedding.iter().map(|x| x * x).sum::<f32>()).sqrt();
    if norm > 0.0 {
        for val in &mut embedding {
            *val /= norm;
        }
    }

    embedding
}

fn hash_word(word: &str) -> u32 {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};
    let mut hasher = DefaultHasher::new();
    word.hash(&mut hasher);
    hasher.finish() as u32
}

pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm_a > 0.0 && norm_b > 0.0 {
        dot / (norm_a * norm_b)
    } else {
        0.0
    }
}
