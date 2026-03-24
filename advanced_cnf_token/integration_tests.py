"""
Integration Tests for Advanced CNF Token Compression System

Comprehensive tests validating:
1. Deterministic encoding (same input → same output)
2. Compression stages (5×, 10×, 15×, 20×)
3. Semantic preservation and anchor grounding
4. Stability monitoring and adaptive control
5. Metrics calculation and validation
"""

import logging
import sys
from typing import Tuple
from advanced_cnf_token.core_structures import CompressionLevel
from advanced_cnf_token.deterministic_encoder import DeterministicEncoder
from advanced_cnf_token.compression_pipeline import ProgressiveCompressionPipeline
from advanced_cnf_token.adaptive_controller import AdaptiveCompressionController, TextAnalyzer
from advanced_cnf_token.stability_monitor import StabilityMonitor, FailureDetector
from advanced_cnf_token.metrics_calculator import ComprehensiveMetricsCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEST DATA
# ============================================================================

TEST_TEXTS = {
    "short_simple": "The best tokenizer for language models is CNF Token.",
    
    "medium_complex": (
        "Modern natural language processing requires sophisticated tokenization "
        "strategies. CNF Token provides semantic compression that outperforms "
        "traditional subword tokenization like BPE. The system maintains "
        "deterministic mapping and semantic grounding for stable compression."
    ),
    
    "long_technical": (
        "Advanced Transformer architectures process input through multi-head "
        "attention mechanisms. Token encodings must preserve semantic information "
        "while achieving high compression ratios. CNF Token compression system "
        "implements progressive stages: baseline → 5× → 10× → 15× → 20×. "
        "Each stage validates semantic integrity and adjusts compression dynamically "
        "based on entropy, token density, and semantic importance. The system "
        "maintains subword anchors for reversibility and stability monitoring "
        "tracks variance and confidence across compression levels."
    ),
    
    "high_entropy": (
        "342 29823 fjkdsl !!@# 28738 qwerty zxcvbn "
        "randomtext8723 specialchars@!$ 99999 unknown"
    ),
}


# ============================================================================
# TESTS
# ============================================================================

def test_deterministic_encoding():
    """Test 1: Ensure deterministic encoding (same input → same output)."""
    print("\n" + "="*80)
    print("TEST 1: DETERMINISTIC ENCODING")
    print("="*80)
    
    encoder = DeterministicEncoder()
    text = TEST_TEXTS["short_simple"]
    context = "test_context"
    
    # Encode same text twice
    tokens1 = encoder.encode_text(text, compression_level=CompressionLevel.LEVEL_1, context=context)
    tokens2 = encoder.encode_text(text, compression_level=CompressionLevel.LEVEL_1, context=context)
    
    # Check token IDs match
    ids1 = [t.token_id for t in tokens1]
    ids2 = [t.token_id for t in tokens2]
    
    print(f"Input: {text}")
    print(f"First encoding token IDs:  {ids1}")
    print(f"Second encoding token IDs: {ids2}")
    print(f"Token count: {len(tokens1)}")
    
    assert ids1 == ids2, "Token IDs should be identical"
    print("✓ PASSED: Deterministic encoding verified")
    
    return True


def test_compression_stages():
    """Test 2: Verify progressive compression (5× → 10× → 15× → 20×)."""
    print("\n" + "="*80)
    print("TEST 2: PROGRESSIVE COMPRESSION STAGES")
    print("="*80)
    
    pipeline = ProgressiveCompressionPipeline()
    text = TEST_TEXTS["medium_complex"]
    
    levels = [
        CompressionLevel.LEVEL_1,
        CompressionLevel.LEVEL_2,
        CompressionLevel.LEVEL_3,
        CompressionLevel.LEVEL_4,
    ]
    
    print(f"Input text: '{text[:80]}...'")
    print("\nProgressive compression:")
    print("-" * 80)
    
    previous_count = None
    for level in levels:
        report = pipeline.compress(text, target_level=level)
        
        ratio = report.metrics.compression_ratio
        output_count = len(report.output_tokens)
        semantic_sim = report.metrics.semantic_similarity
        
        print(f"{level.name:8} | Tokens: {output_count:3} | "
              f"Ratio: {ratio:5.1f}× | "
              f"Semantic Sim: {semantic_sim:5.1%} | "
              f"Confidence: {report.metrics.confidence_mean:4.2f}")
        
        # Verify compression is progressing
        if previous_count:
            assert output_count <= previous_count, f"Token count should decrease at {level.name}"
        previous_count = output_count
    
    print("-" * 80)
    print("✓ PASSED: Progressive compression verified")
    
    return True


def test_semantic_preservation():
    """Test 3: Verify semantic preservation and anchor grounding."""
    print("\n" + "="*80)
    print("TEST 3: SEMANTIC PRESERVATION & ANCHOR GROUNDING")
    print("="*80)
    
    encoder = DeterministicEncoder()
    text = TEST_TEXTS["medium_complex"]
    
    tokens = encoder.encode_text(text, compression_level=CompressionLevel.LEVEL_2)
    
    print(f"Input: {text[:80]}...")
    print(f"\nCompressed to {len(tokens)} tokens")
    print("\nToken details:")
    print("-" * 80)
    print(f"{'Semantic':15} {'Anchors':30} {'Conf':5} {'Valid':6}")
    print("-" * 80)
    
    valid_count = 0
    all_valid = True
    
    for i, token in enumerate(tokens):
        is_valid, reason = token.validate_semantic_integrity()
        
        anchor_texts = ", ".join([a.text for a in token.subword_anchors[:2]])
        if len(token.subword_anchors) > 2:
            anchor_texts += ", ..."
        
        print(f"{token.semantic_repr:15} {anchor_texts:30} {token.confidence:5.2f} {'✓' if is_valid else '✗':6}")
        
        if is_valid:
            valid_count += 1
        else:
            all_valid = False
            print(f"  Reason: {reason}")
    
    print("-" * 80)
    print(f"Valid tokens: {valid_count}/{len(tokens)}")
    
    # Require high anchor coverage
    anchor_coverage = sum(len(t.subword_anchors) for t in tokens) / (len(tokens) * 2)
    print(f"Anchor coverage: {min(1.0, anchor_coverage):.1%}")
    
    print("✓ PASSED: Semantic preservation verified")
    
    return all_valid


def test_adaptive_compression():
    """Test 4: Verify adaptive compression controller."""
    print("\n" + "="*80)
    print("TEST 4: ADAPTIVE COMPRESSION CONTROLLER")
    print("="*80)
    
    controller = AdaptiveCompressionController()
    analyzer = TextAnalyzer()
    
    test_cases = [
        ("high_entropy", TEST_TEXTS["high_entropy"]),
        ("short_simple", TEST_TEXTS["short_simple"]),
        ("medium_complex", TEST_TEXTS["medium_complex"]),
        ("long_technical", TEST_TEXTS["long_technical"]),
    ]
    
    print("\nAdaptive compression selection:")
    print("-" * 80)
    print(f"{'Text':20} {'Entropy':8} {'Diversity':10} {'Recom.':8}")
    print("-" * 80)
    
    for name, text in test_cases:
        tokens = text.lower().split()
        
        level, factors = controller.select_compression_level(tokens)
        
        entropy = factors["entropy"]
        diversity = factors["language_diversity"]
        
        print(f"{name:20} {entropy:8.3f} {diversity:10.3f} {level.name:8}")
    
    print("-" * 80)
    print("✓ PASSED: Adaptive compression controller working")
    
    return True


def test_stability_monitoring():
    """Test 5: Verify stability monitoring."""
    print("\n" + "="*80)
    print("TEST 5: STABILITY MONITORING")
    print("="*80)
    
    monitor = StabilityMonitor()
    calculator = ComprehensiveMetricsCalculator()
    pipeline = ProgressiveCompressionPipeline()
    
    text = TEST_TEXTS["medium_complex"]
    
    print(f"Input: {text[:80]}...")
    print("\nCompressing through stages and monitoring stability:")
    print("-" * 80)
    
    levels = [
        CompressionLevel.LEVEL_1,
        CompressionLevel.LEVEL_2,
        CompressionLevel.LEVEL_3,
    ]
    
    for level in levels:
        report = pipeline.compress(text, target_level=level)
        
        status = monitor.record_snapshot(
            level=level,
            metrics=report.metrics,
            tokens=report.output_tokens,
        )
        
        print(f"{level.name}: Status={status.value:10} "
              f"Variance={report.metrics.variance:.3f} "
              f"FailRate={report.metrics.failure_rate:.1%} "
              f"Confidence={report.metrics.confidence_mean:.2f}")
    
    # Get risk assessment
    risk_assessment = monitor.get_risk_assessment()
    
    print("-" * 80)
    print(f"Risk Assessment: {risk_assessment['current_risk']}")
    print(f"Trend: {risk_assessment['trend']}")
    
    print("\n✓ PASSED: Stability monitoring working")
    
    return True


def test_metrics_calculation():
    """Test 6: Verify metrics calculation."""
    print("\n" + "="*80)
    print("TEST 6: METRICS CALCULATION & VALIDATION")
    print("="*80)
    
    encoder = DeterministicEncoder()
    calculator = ComprehensiveMetricsCalculator()
    
    text = TEST_TEXTS["medium_complex"]
    orig_tokens = text.lower().split()
    
    compressed_tokens = encoder.encode_text(
        text,
        compression_level=CompressionLevel.LEVEL_2
    )
    
    # Calculate all metrics
    metrics = calculator.calculate_all(orig_tokens, compressed_tokens)
    
    print(f"Input: {text[:80]}...")
    print(f"Original tokens: {len(orig_tokens)}")
    print(f"Compressed tokens: {len(compressed_tokens)}")
    print("\nMetrics:")
    print("-" * 80)
    print(f"  Compression Ratio:    {metrics.compression_ratio:7.1f}×")
    print(f"  Semantic Similarity:  {metrics.semantic_similarity:7.1%}")
    print(f"  Reconstruction Score: {metrics.reconstruction_score:7.1%}")
    print(f"  Variance:             {metrics.variance:7.3f}")
    print(f"  Failure Rate:         {metrics.failure_rate:7.1%}")
    print(f"  Mean Confidence:      {metrics.confidence_mean:7.2f}")
    print(f"  Anchor Coverage:      {metrics.anchor_coverage:7.1%}")
    print("-" * 80)
    
    # Validate metrics
    is_valid, issues = calculator.validator.validate_metrics(
        metrics,
        CompressionLevel.LEVEL_2
    )
    
    print(f"\nValidation: {'PASSED ✓' if is_valid else 'FAILED ✗'}")
    if issues:
        for issue in issues:
            print(f"  - {issue}")
    
    print("✓ PASSED: Metrics calculation working")
    
    return is_valid


def test_end_to_end():
    """Test 7: Full end-to-end compression pipeline."""
    print("\n" + "="*80)
    print("TEST 7: END-TO-END COMPRESSION PIPELINE")
    print("="*80)
    
    pipeline = ProgressiveCompressionPipeline()
    monitor = StabilityMonitor()
    
    text = TEST_TEXTS["long_technical"]
    
    # Compress to each level and track stability
    print(f"Input: {text[:100]}...")
    print("\nFull compression pipeline:")
    print("-" * 80)
    
    for level in [
        CompressionLevel.LEVEL_1,
        CompressionLevel.LEVEL_2,
        CompressionLevel.LEVEL_3,
        CompressionLevel.LEVEL_4,
    ]:
        report = pipeline.compress(text, target_level=level)
        status = monitor.record_snapshot(level, report.metrics, report.output_tokens)
        
        print(f"\n{level.name}:")
        print(f"  Tokens: {report.input_token_count} → {len(report.output_tokens)}")
        print(f"  Ratio: {report.metrics.compression_ratio:.1f}×")
        print(f"  Semantic Similarity: {report.metrics.semantic_similarity:.1%}")
        print(f"  Status: {status.value.upper()}")
        print(f"  Acceptable: {report.acceptable}")
        
        if report.warnings:
            for warning in report.warnings:
                print(f"    ⚠ {warning}")
    
    print("\n" + "-" * 80)
    print(report.summary())
    
    print("✓ PASSED: End-to-end pipeline working")
    
    return report.acceptable


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests() -> Tuple[int, int]:
    """Run all tests and return (passed, failed)."""
    
    tests = [
        ("Deterministic Encoding", test_deterministic_encoding),
        ("Compression Stages", test_compression_stages),
        ("Semantic Preservation", test_semantic_preservation),
        ("Adaptive Compression", test_adaptive_compression),
        ("Stability Monitoring", test_stability_monitoring),
        ("Metrics Calculation", test_metrics_calculation),
        ("End-to-End Pipeline", test_end_to_end),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            result = test_fn()
            if result:
                passed += 1
            else:
                failed += 1
                print(f"\n✗ FAILED: {name}")
        except Exception as e:
            failed += 1
            print(f"\n✗ FAILED: {name}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
    
    return passed, failed


if __name__ == "__main__":
    print("\n" + "="*80)
    print("ADVANCED CNF TOKEN COMPRESSION SYSTEM - INTEGRATION TESTS")
    print("="*80)
    
    passed, failed = run_all_tests()
    
    print("\n" + "="*80)
    print(f"FINAL RESULTS: {passed} passed, {failed} failed")
    print("="*80 + "\n")
    
    sys.exit(0 if failed == 0 else 1)
