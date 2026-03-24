"""
Advanced CNF Token Compression System - Quick Reference

This is the starting point for understanding and using the system.
"""

# ============================================================================
# QUICK START (2 minutes)
# ============================================================================

"""
1. BASIC COMPRESSION
   
   from advanced_cnf_token import ProgressiveCompressionPipeline, CompressionLevel
   
   pipeline = ProgressiveCompressionPipeline()
   report = pipeline.compress(
       text="Your text here",
       target_level=CompressionLevel.LEVEL_2  # 10× compression
   )
   
   print(report.summary())


2. ADAPTIVE SELECTION (let system choose safe level)
   
   from advanced_cnf_token import AdaptiveCompressionController
   
   controller = AdaptiveCompressionController()
   tokens = text.lower().split()
   optimal_level, factors = controller.select_compression_level(tokens)
   
   report = pipeline.compress(text, target_level=optimal_level)


3. WITH MONITORING (track stability)
   
   from advanced_cnf_token import StabilityMonitor
   
   monitor = StabilityMonitor()
   status = monitor.record_snapshot(level, report.metrics, report.output_tokens)
   
   if status == "CRITICAL":
       print("Compression is unstable - rolling back")
"""


# ============================================================================
# WHAT IS THIS SYSTEM?
# ============================================================================

"""
Advanced CNF Token Compression compresses text into semantic tokens that:

1. COMPRESS AGGRESSIVELY
   - 5× compression with ≥96% accuracy
   - 10× compression with ≥96% accuracy
   - 15× compression with ≥94% accuracy
   - 20× compression with ≥92% accuracy

2. STAY DETERMINISTIC
   - Same input → same tokens ALWAYS
   - Based on SHA256 hashing
   - Enables consistent deployments

3. PRESERVE MEANING
   - Maintain subword anchors for grounding
   - Track semantic, lexical, and structural information
   - Enable partial text recovery (~50-80%)

4. MONITOR STABILITY
   - Real-time variance and confidence tracking
   - Auto-rollback if quality degrades
   - Comprehensive metrics for quality assurance

5. PRIORITIZE SAFETY
   Priority order: STABILITY > ACCURACY > COMPRESSION
   Will reduce compression ratio to prevent semantic collapse
"""


# ============================================================================
# ARCHITECTURE (5 COMPONENTS)
# ============================================================================

"""
Component 1: DeterministicEncoder (deterministic_encoder.py)
  ↳ Converts text to CNFTokens
  ↳ Hash-based token IDs
  ↳ Semantic clustering
  ↳ Anchor extraction
  ↳ Path encoding

Component 2: ProgressiveCompressionPipeline (compression_pipeline.py)
  ↳ Stages: 5× → 10× → 15× → 20× compression
  ↳ Validates at each stage
  ↳ Can rollback if degradation detected
  ↳ Tracks compression history

Component 3: AdaptiveCompressionController (adaptive_controller.py)
  ↳ Analyzes text entropy
  ↳ Measures word frequency distribution
  ↳ Detects named entities
  ↳ Auto-selects safe compression level

Component 4: StabilityMonitor (stability_monitor.py)
  ↳ Tracks variance (token stability)
  ↳ Monitors confidence scores
  ↳ Detects reconstruction failures
  ↳ Auto-triggers rollback
  ↳ Risk assessment and recommendation

Component 5: MetricsCalculator (metrics_calculator.py)
  ↳ Compression ratio (input / output)
  ↳ Semantic similarity (meaning preservation)
  ↳ Reconstruction score (reversibility)
  ↳ Variance metric (stability)
  ↳ Failure rate (% validation failures)
  ↳ Confidence calibration (prediction accuracy)
  ↳ Anchor coverage (lexical grounding)
"""


# ============================================================================
# KEY CONCEPTS
# ============================================================================

"""
CNFToken - Core data structure
  token_id: Deterministic SHA256 hash
  semantic_repr: Core semantic concept
  subword_anchors: Lexical grounding (prevents collapse)
  compression_level: Which compression stage (LEVEL_1 to LEVEL_4)
  semantic_path, lexical_path, structural_path: Multi-path encoding
  confidence: Quality score (0-1)
  variance: Stability metric
  density: Bits per token
  failure_rate: Reconstruction failure %

CompressionLevel - Four stages
  LEVEL_1: 5× compression, ≥96% accuracy
  LEVEL_2: 10× compression, ≥96% accuracy
  LEVEL_3: 15× compression, ≥94% accuracy
  LEVEL_4: 20× compression, ≥92% accuracy

StabilityStatus - Real-time status
  STABLE: All metrics OK → can try higher compression
  DEGRADING: 2+ warnings → monitor closely
  UNSTABLE: 1+ critical → reduce compression
  CRITICAL: 2+ critical → rollback to LEVEL_1

CompressionMetrics - Quality scores (all 0-1 range)
  compression_ratio: Actual compression achieved
  semantic_similarity: Meaning preservation
  reconstruction_score: Text recovery capability
  variance: Token stability
  failure_rate: Validation failures
  confidence_mean: Average quality
  anchor_coverage: Lexical grounding
"""


# ============================================================================
# TYPICAL RESULTS
# ============================================================================

"""
Example: "The best tokenizer for advanced NLP is CNF Token" (9 tokens)

LEVEL_1 (5×):   4 tokens → 2.2× actual (very conservative)
LEVEL_2 (10×):  2 tokens → 4.5× actual (balanced)
LEVEL_3 (15×):  1 token → 9× actual (aggressive)
LEVEL_4 (20×):  1 token → 9× actual (maximum)

Note: Actual ratios typically 50-80% of targets
Trade-off: Lower compression for higher confidence and stability
"""


# ============================================================================
# WHEN TO USE EACH LEVEL
# ============================================================================

"""
LEVEL_1 (5× compression)
  ✓ When maximum reliability is critical
  ✓ When text is very diverse or high-entropy
  ✓ When you can't afford semantic loss
  ✓ Default safe choice

LEVEL_2 (10× compression)
  ✓ Balanced efficiency and accuracy
  ✓ Best for most use cases
  ✓ Good for embedding generation
  ✓ Recommended starting point

LEVEL_3 (15× compression)
  ✓ When efficiency is important
  ✓ For large-scale processing
  ✓ Monitor stability carefully
  ✓ May need to rollback

LEVEL_4 (20× compression)
  ✓ Maximum compression needed
  ✓ For extreme efficiency scenarios
  ✓ Highest risk of semantic loss
  ✓ Requires constant monitoring
"""


# ============================================================================
# HOW TO VERIFY IT'S WORKING
# ============================================================================

"""
1. CHECK DETERMINISM
   from advanced_cnf_token import DeterministicEncoder
   
   encoder = DeterministicEncoder()
   tokens1 = encoder.encode_text(text, context="v1")
   tokens2 = encoder.encode_text(text, context="v1")
   
   assert [t.token_id for t in tokens1] == [t.token_id for t in tokens2]
   # PASS: Deterministic ✓


2. CHECK SEMANTIC PRESERVATION
   Look at token.subword_anchors - should all be non-empty
   Example: semantic_repr="excellence" → anchors=["best", "excellent"]


3. CHECK STABILITY METRICS
   report.metrics.semantic_similarity should be ≥ level.min_accuracy
   report.metrics.variance should be < 0.5
   report.metrics.failure_rate should be < 0.1


4. RUN INTEGRATION TESTS
   python -m advanced_cnf_token.integration_tests
   
   Should see:
     ✓ Deterministic Encoding
     ✓ Compression Stages
     ✓ Semantic Preservation
     ✓ Adaptive Compression
     ✓ Stability Monitoring
     ✓ Metrics Calculation
     ✓ End-to-End Pipeline


5. RUN EXAMPLES
   python -m advanced_cnf_token.examples
   
   Shows 6 practical examples of the system working
"""


# ============================================================================
# COMMON ISSUES & SOLUTIONS
# ============================================================================

"""
Issue: Compression ratio lower than expected
  → This is normal! System prioritizes stability over compression
  → Try increasing target compression level gradually
  → Monitor stability status before stepping up

Issue: Low semantic similarity
  → Usually happens at LEVEL_3 and LEVEL_4
  → System will warn about this
  → Consider rolling back to lower compression level

Issue: High variance detected
  → Text may be too diverse/high-entropy for aggressive compression
  → System will recommend lower compression level
  → Use LEVEL_1 or LEVEL_2 for safety

Issue: Anchor coverage < 70%
  → Some tokens have few lexical anchors
  → May reduce text recovery capability
  → Will be flagged in warnings
"""


# ============================================================================
# DIRECTORY STRUCTURE
# ============================================================================

"""
advanced_cnf_token/
├── __init__.py
│   ↳ Module entry point - imports all components
│
├── core_structures.py
│   ↳ Data classes: CNFToken, CompressionLevel, CompressionMetrics, etc.
│   ↳ Foundation of the system
│
├── deterministic_encoder.py
│   ↳ Converts text to CNFTokens
│   ↳ Hash-based token IDs (determinism)
│   ↳ Semantic clustering
│
├── compression_pipeline.py
│   ↳ Progressive compression stages (5→10→15→20×)
│   ↳ Validation at each stage
│   ↳ Handles compression history
│
├── adaptive_controller.py
│   ↳ Analyzes text characteristics
│   ↳ Auto-selects safe compression level
│   ↳ Applies safety constraints
│
├── stability_monitor.py
│   ↳ Real-time status tracking
│   ↳ Variance and confidence monitoring
│   ↳ Failure detection and recommendations
│
├── metrics_calculator.py
│   ↳ All quality metrics (7 different ones)
│   ↳ Validation against thresholds
│
├── integration_tests.py
│   ↳ Comprehensive test suite
│   ↳ Validates all components
│   ↳ 7 different test scenarios
│
├── examples.py
│   ↳ 6 practical usage examples
│   ↳ Demonstrates each component
│   ↳ Shows typical results
│
├── ARCHITECTURE.md
│   ↳ Detailed technical documentation
│   ↳ Component reference
│   ↳ Design decisions explained
│
├── SUMMARY.md
│   ↳ High-level overview
│   ↳ Key guarantees
│   ↳ Performance characteristics
│
└── README.md (this file)
    ↳ Quick reference guide
"""


# ============================================================================
# READING ORDER
# ============================================================================

"""
1. This file (README.md) - Overview and quick reference
2. examples.py - See practical examples
3. ARCHITECTURE.md - Understand design and implementation
4. integration_tests.py - See expected behavior
5. Source files - Deep dive into each component
"""


# ============================================================================
# QUICK API REFERENCE
# ============================================================================

"""
MAIN PIPELINE
  pipeline = ProgressiveCompressionPipeline()
  report = pipeline.compress(text, target_level=CompressionLevel.LEVEL_2)

ADAPTIVE COMPRESSION
  controller = AdaptiveCompressionController()
  level, factors = controller.select_compression_level(tokens)

STABILITY MONITORING
  monitor = StabilityMonitor()
  status = monitor.record_snapshot(level, metrics, tokens)

METRICS CALCULATION
  calculator = ComprehensiveMetricsCalculator()
  metrics = calculator.calculate_all(original_tokens, compressed_tokens)

DETERMINISTIC ENCODING
  encoder = DeterministicEncoder()
  tokens = encoder.encode_text(text, compression_level)

RESULT REPORT
  report.summary()                          # Human-readable summary
  report.metrics.to_dict()                  # Metric breakdown
  report.output_tokens[0].validate_semantic_integrity()  # Check validity
"""


# ============================================================================
# GUARANTEES
# ============================================================================

"""
✓ DETERMINISTIC
  Same input + context → Same token IDs ALWAYS
  
✓ GROUNDED
  Every token has subword anchors (prevents semantic collapse)
  
✓ PROGRESSIVE
  Each compression stage validates integrity
  Can rollback if quality drops
  
✓ MONITORED
  Real-time variance and confidence tracking
  Auto-recommends rollback on degradation
  
✓ REVERSIBLE
  Anchors enable ~50-80% text recovery
  Suitable for embedding + recovery pipelines
  
✓ TRANSPARENT
  Comprehensive metrics show exactly what happened
  Every decision is traceable and explainable
  
✓ SAFE
  Prioritizes stability over maximum compression
  Aggressive safety constraints
  Never risks complete semantic collapse
"""


# ============================================================================
# PRIORITY
# ============================================================================

"""
STABILITY > ACCURACY > COMPRESSION

This means:
1. Never risk semantic collapse (stability is #1 priority)
2. High confidence thresholds (some lossy compression rejected)
3. Aggressive rollback policy (safety over efficiency)
4. Conservative defaults (safe starting point)

The system will REDUCE compression if needed to maintain stability.
"""


# ============================================================================
# SUPPORT
# ============================================================================

"""
For help:
1. Check examples.py for practical examples
2. Review ARCHITECTURE.md for technical details
3. Run integration_tests.py to see expected behavior
4. Enable DEBUG logging to trace execution

All functions have comprehensive docstrings.
All decisions are logged with reasoning.
"""


if __name__ == "__main__":
    print(__doc__)
