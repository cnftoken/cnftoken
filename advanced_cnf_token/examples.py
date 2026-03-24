"""
Complete Usage Example of Advanced CNF Token Compression System

This example demonstates the entire system end-to-end:
1. Text input
2. Adaptive compression selection
3. Progressive compression
4. Stability monitoring
5. Metrics evaluation
6. Result visualization
"""

import logging
from advanced_cnf_token import (
    ProgressiveCompressionPipeline,
    AdaptiveCompressionController,
    StabilityMonitor,
    ComprehensiveMetricsCalculator,
    CompressionLevel,
)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='[%(levelname)s] %(message)s'
)


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_metrics_table(report):
    """Print metrics in table format."""
    print("Compression Metrics:")
    print("-" * 80)
    print(f"  Compression Ratio:      {report.metrics.compression_ratio:8.1f}×")
    print(f"  Semantic Similarity:    {report.metrics.semantic_similarity:8.1%}")
    print(f"  Reconstruction Score:   {report.metrics.reconstruction_score:8.1%}")
    print(f"  Variance:               {report.metrics.variance:8.3f}")
    print(f"  Failure Rate:           {report.metrics.failure_rate:8.1%}")
    print(f"  Mean Confidence:        {report.metrics.confidence_mean:8.2f}")
    print(f"  Anchor Coverage:        {report.metrics.anchor_coverage:8.1%}")
    print("-" * 80)


def example_basic_compression():
    """Example 1: Basic compression with default settings."""
    print_header("Example 1: Basic Compression")
    
    pipeline = ProgressiveCompressionPipeline()
    
    text = (
        "Advanced Transformer architectures revolutionize natural language processing. "
        "CNF Token compression enables efficient processing of long sequences while "
        "maintaining semantic integrity and deterministic mapping."
    )
    
    print(f"Input text:\n  {text}\n")
    print(f"Input length: {len(text.split())} tokens\n")
    
    # Compress to level 2 (10×)
    report = pipeline.compress(text, target_level=CompressionLevel.LEVEL_2)
    
    print(f"Compression Level: {report.level.name}")
    print(f"Output tokens: {len(report.output_tokens)}")
    print_metrics_table(report)
    
    # Show some output tokens
    print("\nRepresentative Output Tokens:")
    print("-" * 80)
    for i, token in enumerate(report.output_tokens[:5]):
        anchors = ", ".join([a.text for a in token.subword_anchors])
        print(f"  {i+1}. {token.semantic_repr:20} → [{anchors}]")
    print("-" * 80)
    
    return report


def example_adaptive_selection():
    """Example 2: Let the system auto-select compression level."""
    print_header("Example 2: Adaptive Compression Selection")
    
    controller = AdaptiveCompressionController()
    pipeline = ProgressiveCompressionPipeline()
    
    texts = {
        "Technical": (
            "Implementation of convolutional neural networks requires careful "
            "consideration of hyperparameters including learning rate, batch size, "
            "and regularization strength."
        ),
        "Formulaic": (
            "Smith, John. Residence: New York. Occupation: Engineer. "
            "Contact: john@email.com. Phone: 555-1234."
        ),
        "Diverse": (
            "The café in São Paulo serves exceptional feijoada. "
            "🌟 Customer: 매우 만족! ⭐ Muy bueno! 很好吃!"
        ),
    }
    
    print("Auto-selecting compression level for different text types:\n")
    print("-" * 80)
    
    for name, text in texts.items():
        tokens = text.lower().split()
        
        # Get adaptive recommendation
        level, factors = controller.select_compression_level(tokens)
        
        print(f"\n{name} Text:")
        print(f"  Entropy:          {factors['entropy']:.3f}")
        print(f"  Uniqueness:       {factors['unique_token_ratio']:.1%}")
        print(f"  Language Diversity: {factors['language_diversity']:.3f}")
        print(f"  → Recommended:    {level.name}")
        
        # Compress with recommended level
        report = pipeline.compress(text, target_level=level)
        print(f"  Actual Ratio:     {report.metrics.compression_ratio:.1f}×")
        print(f"  Similarity:       {report.metrics.semantic_similarity:.1%}")
    
    print("\n" + "-" * 80)


def example_progressive_compression():
    """Example 3: See how compression improves through stages."""
    print_header("Example 3: Progressive Compression Through Stages")
    
    pipeline = ProgressiveCompressionPipeline()
    
    text = (
        "The advancement in machine learning has transformed multiple industries. "
        "Deep learning models now power virtual assistants, recommendation systems, "
        "and autonomous vehicles. CNF Token compression enables efficient deployment "
        "of these models by reducing token requirements."
    )
    
    print(f"Input: {len(text.split())} tokens\n")
    print("Compressing through stages:")
    print("-" * 80)
    print(f"{'Level':8} {'Tokens':8} {'Ratio':8} {'Similarity':12} {'Status':10}")
    print("-" * 80)
    
    for level in [
        CompressionLevel.LEVEL_1,
        CompressionLevel.LEVEL_2,
        CompressionLevel.LEVEL_3,
        CompressionLevel.LEVEL_4,
    ]:
        report = pipeline.compress(text, target_level=level)
        
        status = "✓ OK" if report.acceptable else "✗ WARN"
        
        print(f"{level.name:8} {len(report.output_tokens):8} "
              f"{report.metrics.compression_ratio:7.1f}x "
              f"{report.metrics.semantic_similarity:11.1%} "
              f"{status:10}")
    
    print("-" * 80)


def example_stability_monitoring():
    """Example 4: Monitor compression stability."""
    print_header("Example 4: Stability Monitoring")
    
    pipeline = ProgressiveCompressionPipeline()
    monitor = StabilityMonitor()
    
    text = (
        "The quick brown fox jumps over the lazy dog multiple times. "
        "This pangram contains all letters of the English alphabet. "
        "Stability monitoring ensures compression quality across different levels."
    )
    
    print(f"Input: {len(text.split())} tokens\n")
    print("Monitoring stability through compression levels:")
    print("-" * 80)
    print(f"{'Level':8} {'Status':12} {'Variance':10} {'Confidence':12} {'Action':15}")
    print("-" * 80)
    
    last_successful_level = CompressionLevel.LEVEL_1
    
    for level in [
        CompressionLevel.LEVEL_1,
        CompressionLevel.LEVEL_2,
        CompressionLevel.LEVEL_3,
        CompressionLevel.LEVEL_4,
    ]:
        report = pipeline.compress(text, target_level=level)
        
        status = monitor.record_snapshot(
            level=level,
            metrics=report.metrics,
            tokens=report.output_tokens,
        )
        
        # Get adjustment recommendation
        adjusted, reasons = monitor.get_adjustment_recommendation(level)
        action = adjusted.name if adjusted else "Continue"
        
        print(f"{level.name:8} {status.value:12} "
              f"{report.metrics.variance:9.3f} "
              f"{report.metrics.confidence_mean:11.2f} "
              f"{action:15}")
        
        last_successful_level = level
    
    print("-" * 80)
    
    # Print risk assessment
    risk = monitor.get_risk_assessment()
    print(f"\nFinal Risk Assessment: {risk['current_risk']}")
    print(f"Trend: {risk['trend']}")
    
    return last_successful_level


def example_detailed_analysis():
    """Example 5: Detailed analysis of compression quality."""
    print_header("Example 5: Detailed Compression Analysis")
    
    encoder = DeterministicEncoder()
    calculator = ComprehensiveMetricsCalculator()
    pipeline = ProgressiveCompressionPipeline()
    
    text = (
        "Natural language processing represents one of the most challenging areas "
        "in artificial intelligence. Modern transformer models achieve impressive "
        "results on various NLP tasks including translation, summarization, and "
        "question answering systems."
    )
    
    # Compress to level 2
    report = pipeline.compress(text, target_level=CompressionLevel.LEVEL_2)
    
    print(f"Input: '{text[:80]}...'\n")
    print(f"Input tokens: {report.input_token_count}")
    print(f"Output tokens: {len(report.output_tokens)}\n")
    
    # Detailed metrics
    print("Detailed Metrics Analysis:")
    print_metrics_table(report)
    
    # Token-level analysis
    print("\nToken-Level Analysis:")
    print("-" * 80)
    print(f"{'Semantic':20} {'Anchors':30} {'Conf':5} {'Var':5} {'Dense':5}")
    print("-" * 80)
    
    for token in report.output_tokens[:5]:
        is_valid, _ = token.validate_semantic_integrity()
        anchors = ", ".join([a.text for a in token.subword_anchors[:2]])
        if len(token.subword_anchors) > 2:
            anchors += ", ..."
        
        print(f"{token.semantic_repr:20} {anchors:30} "
              f"{token.confidence:5.2f} {token.variance:5.2f} {token.density:5.1f}")
    
    print("-" * 80)
    
    # Validation
    if report.acceptable:
        print("\n✓ Compression is ACCEPTABLE")
    else:
        print("\n✗ Compression has ISSUES:")
        for warning in report.warnings:
            print(f"  - {warning}")


def example_deterministic_guarantee():
    """Example 6: Verify deterministic encoding."""
    print_header("Example 6: Deterministic Encoding Guarantee")
    
    from advanced_cnf_token import DeterministicEncoder
    
    encoder = DeterministicEncoder()
    text = "The same text always produces the same tokens"
    context = "demo_context"
    
    # Encode 3 times
    print(f"Input text: '{text}'\n")
    print("Encoding 3 times with same context...\n")
    
    encodings = []
    for i in range(3):
        tokens = encoder.encode_text(text, CompressionLevel.LEVEL_1, context)
        token_ids = [t.token_id for t in tokens]
        encodings.append(token_ids)
        print(f"Encoding {i+1}: {token_ids[:5]}... ({len(token_ids)} tokens)")
    
    print("\nVerification:")
    if encodings[0] == encodings[1] == encodings[2]:
        print("✓ PASSED: All encodings are identical!")
        print("  Same input + context → same output (deterministic)")
    else:
        print("✗ FAILED: Encodings differ!")


# Required import
from advanced_cnf_token import DeterministicEncoder


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("ADVANCED CNF TOKEN COMPRESSION - COMPLETE USAGE EXAMPLES")
    print("=" * 80)
    
    try:
        # Run examples
        example_basic_compression()
        example_adaptive_selection()
        example_progressive_compression()
        example_stability_monitoring()
        example_detailed_analysis()
        example_deterministic_guarantee()
        
        print_header("All Examples Completed Successfully!")
        print("Next steps:")
        print("  1. Review the examples above")
        print("  2. Check ARCHITECTURE.md for detailed documentation")
        print("  3. Run integration_tests.py for comprehensive validation")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
