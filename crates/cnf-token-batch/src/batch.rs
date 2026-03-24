use std::collections::{HashMap, VecDeque};
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;
use std::sync::Mutex;

static CACHE: Mutex<Option<BatchCache>> = Mutex::new(None);

pub struct BatchCache {
    cache: HashMap<u64, Vec<u8>>,
    order: VecDeque<u64>,
    capacity: usize,
}

impl BatchCache {
    fn new(capacity: usize) -> Self {
        Self {
            cache: HashMap::new(),
            order: VecDeque::new(),
            capacity,
        }
    }

    fn hash_input(input: &[u8]) -> u64 {
        let mut hasher = DefaultHasher::new();
        input.hash(&mut hasher);
        hasher.finish()
    }

    fn get_or_init() -> std::sync::MutexGuard<'static, Option<BatchCache>> {
        let mut cache = CACHE.lock().expect("Failed to lock cache");
        if cache.is_none() {
            *cache = Some(BatchCache::new(100)); // default capacity
        }
        cache
    }

    pub fn process(items: &[u8]) -> Vec<u8> {
        let mut cache_opt = Self::get_or_init();
        let cache = cache_opt.as_mut().expect("Cache not initialized");
        let key = Self::hash_input(items);
        if let Some(cached) = cache.cache.get(&key) {
            // Move to front
            if let Some(pos) = cache.order.iter().position(|&k| k == key) {
                cache.order.remove(pos);
            }
            cache.order.push_front(key);
            return cached.clone();
        }
        // Compute (placeholder: still wrapping_add for now, but in cache)
        let result: Vec<u8> = items.iter().map(|b| b.wrapping_add(1)).collect();
        cache.cache.insert(key, result.clone());
        cache.order.push_front(key);
        if cache.cache.len() > cache.capacity {
            if let Some(old_key) = cache.order.pop_back() {
                cache.cache.remove(&old_key);
            }
        }
        result
    }

    pub fn process_bytes(bytes: &[u8]) -> Vec<u8> {
        Self::process(bytes)
    }
}
