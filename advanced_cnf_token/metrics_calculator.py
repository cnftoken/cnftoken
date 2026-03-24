"""
Validation & Metrics Module

Implements comprehensive metrics calculation and validation for compression quality.

Key Metrics:
1. Compression Ratio - Input tokens / output tokens
2. Semantic Similarity - Preservation of meaning
3. Reconstruction Score - How well we can recover original
4. Variance - Stability across contexts
5. Failure Rate - % of tokens failing validation
6. Confidence Calibration - How well confidence scores predict actual quality

All metrics normalize to [0, 1] range for easy comparison.
"""

import logging
import math
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import Counter
from advanced_cnf_token.core_structures import (
    CNFToken, CompressionLevel, CompressionMetrics
)

logger = logging.getLogger(__name__)


class SemanticSimilarityCalculator:
    """Calculates semantic similarity between original and compressed text."""
    
    def __init__(self):
        self.semantic_cache: Dict[str, float] = {}
    
    def calculate(
        self,
        original_tokens: List[str],
        compressed_tokens: List[CNFToken]
    ) -> float:
        """
        Calculate semantic similarity.
        
        Strategy:
        1. Extract semantic representations from compressed tokens
        2. Compute how well they cover original tokens
        3. Account for anchor grounding
        
        Returns:
            Score [0, 1] where 1.0 = perfect preservation
        
        Formula:
        similarity = (covered_concepts / total_concepts) * anchor_weight
        
        where:
        - covered_concepts = unique semantic reprs in compressed
        - total_concepts = unique tokens in original
        - anchor_weight = 0.5 to 1.0 based on anchor coverage
        """
        
        if not original_tokens or not compressed_tokens:
            return 1.0 if len(original_tokens) == len(compressed_tokens) else 0.0
        
        # Get unique original concepts
        original_concepts = set(original_tokens)
        
        # Get covered concepts from compression
        covered_concepts: Set[str] = set()
        anchor_count = 0
        
        for token in compressed_tokens:
            # Add semantic repr
            covered_concepts.add(token.semantic_repr)
            
            # Add all anchors
            for anchor in token.subword_anchors:
                covered_concepts.add(anchor.text)
                anchor_count += 1
        
        # Calculate coverage
        covered = len(covered_concepts & original_concepts)
        total = len(original_concepts)
        
        if total == 0:
            return 1.0
        
        coverage_score = covered / total
        
        # Anchor weight (higher anchor count = better grounding)
        max_anchors = len(compressed_tokens) * 5
        anchor_weight = min(1.0, 0.5 + (anchor_count / max_anchors) * 0.5)
        
        similarity = coverage_score * anchor_weight
        
        return min(1.0, max(0.0, similarity))


class ReconstructionScoreCalculator:
    """Calculates how well we can reconstruct original text from compressed."""
    
    def calculate(self, compressed_tokens: List[CNFToken]) -> float:
        """
        Calculate reconstruction score.
        
        Strategy:
        1. Check that every token has anchors (without anchors, reconstruction is impossible)
        2. Check anchor diversity (more diverse anchors = better reconstruction)
        3. Check reconstruction hints completeness
        
        Returns:
            Score [0, 1] where 1.0 = perfect reconstruction possible
        
        Formula:
        score = anchor_coverage * diversity_factor * completeness_factor
        """
        
        if not compressed_tokens:
            return 1.0
        
        tokens_with_anchors = sum(1 for t in compressed_tokens if t.subword_anchors)
        anchor_coverage = tokens_with_anchors / len(compressed_tokens)
        
        # Diversity factor: how many unique anchors
        all_anchors = []
        for token in compressed_tokens:
            all_anchors.extend([a.text for a in token.subword_anchors])
        
        unique_anchors = len(set(all_anchors))
        total_possible_anchors = len(compressed_tokens) * 5
        diversity_factor = min(1.0, unique_anchors / max(1, total_possible_anchors))
        
        # Completeness factor: whether all tokens have reconstruction hints
        tokens_with_hints = sum(1 for t in compressed_tokens if t.reconstruction_hint)
        completeness_factor = tokens_with_hints / max(1, len(compressed_tokens))
        
        score = anchor_coverage * 0.5 + diversity_factor * 0.3 + completeness_factor * 0.2
        
        return min(1.0, max(0.0, score))


class VarianceCalculator:
    """Calculates token variance (stability across contexts)."""
    
    def calculate(self, compressed_tokens: List[CNFToken]) -> float:
        """
        Calculate overall variance score.
        
        High variance = token meaning varies significantly across contexts
        Low variance = stable meaning
        
        Returns:
            Score [0, 1] where 0 = stable, 1 = highly variable
        
        Strategy:
        - Average individual token variances
        - Weight by confidence (low-confidence tokens are unreliable)
        """
        
        if not compressed_tokens:
            return 0.0
        
        # Simple average of token variances weighted by inverse confidence
        total_variance = 0.0
        total_weight = 0.0
        
        for token in compressed_tokens:
            # Tokens with low confidence are more variable
            weight = 1.0 / max(0.1, token.confidence)
            total_variance += token.variance * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        avg_variance = total_variance / total_weight
        
        # Normalize to [0, 1]
        return min(1.0, max(0.0, avg_variance))


class FailureRateCalculator:
    """Calculates token failure rate (% failing reconstruction)."""
    
    def calculate(self, compressed_tokens: List[CNFToken]) -> float:
        """
        Calculate failure rate.
        
        Failure = token fails to meet quality standards
        
        Returns:
            Score [0, 1] where 0 = no failures, 1 = all failed
        
        Criteria for failure:
        - No anchors
        - Confidence < 0.4
        - Variance > 0.5
        - No reconstruction hint
        """
        
        if not compressed_tokens:
            return 0.0
        
        failures = 0
        
        for token in compressed_tokens:
            failed = False
            
            if not token.subword_anchors:
                failed = True
            elif token.confidence < 0.4:
                failed = True
            elif token.variance > 0.5:
                failed = True
            elif not token.reconstruction_hint:
                failed = True
            
            if failed:
                failures += 1
        
        failure_rate = failures / len(compressed_tokens)
        
        return min(1.0, max(0.0, failure_rate))


class ConfidenceCalibrationAnalyzer:
    """Analyzes whether confidence scores accurately predict quality."""
    
    def analyze(
        self,
        compressed_tokens: List[CNFToken],
        actual_failures: Optional[List[int]] = None
    ) -> Dict[str, float]:
        """
        Analyze confidence calibration.
        
        Compares predicted confidence against actual quality metrics.
        
        Args:
            compressed_tokens: Tokens with confidence scores
            actual_failures: Optional list of token indices that failed
        
        Returns:
            {
                "mean_confidence": float,
                "std_deviation": float,
                "calibration_score": float,  # How well predicted vs actual
                "overconfidence": float,      # How much over-predicted
                "underconfidence": float,     # How much under-predicted
            }
        """
        
        if not compressed_tokens:
            return {
                "mean_confidence": 0.0,
                "std_deviation": 0.0,
                "calibration_score": 0.0,
                "overconfidence": 0.0,
                "underconfidence": 0.0,
            }
        
        # Compute actual quality for each token
        confidences = []
        actual_qualities = []
        
        for i, token in enumerate(compressed_tokens):
            confidences.append(token.confidence)
            
            # Compute actual quality
            quality = 1.0
            if not token.subword_anchors:
                quality -= 0.4
            if token.variance > 0.5:
                quality -= 0.3
            if token.density > 32:
                quality -= 0.2
            
            # Check if token was in failure list
            if actual_failures and i in actual_failures:
                quality -= 0.5
            
            actual_qualities.append(max(0.0, quality))
        
        # Statistical analysis
        mean_confidence = sum(confidences) / len(confidences)
        
        variance = sum((c - mean_confidence) ** 2 for c in confidences) / len(confidences)
        std_deviation = math.sqrt(variance)
        
        # Calibration: how well do predictions match actual
        calibration_errors = []
        for pred, actual in zip(confidences, actual_qualities):
            error = abs(pred - actual)
            calibration_errors.append(error)
        
        mean_error = sum(calibration_errors) / len(calibration_errors)
        calibration_score = 1.0 - min(1.0, mean_error)
        
        # Over/underconfidence
        mean_actual = sum(actual_qualities) / len(actual_qualities)
        overconfidence = max(0.0, mean_confidence - mean_actual)
        underconfidence = max(0.0, mean_actual - mean_confidence)
        
        return {
            "mean_confidence": mean_confidence,
            "std_deviation": std_deviation,
            "calibration_score": calibration_score,
            "overconfidence": overconfidence,
            "underconfidence": underconfidence,
        }


class MetricsValidator:
    """Validates that metrics meet compression level requirements."""
    
    def validate_metrics(
        self,
        metrics: CompressionMetrics,
        level: CompressionLevel
    ) -> Tuple[bool, List[str]]:
        """
        Validate metrics against level requirements.
        
        Returns:
            (is_valid, list_of_issues)
        """
        
        issues = []
        
        # Compression ratio check
        expected_ratio = level.target_ratio
        if metrics.compression_ratio < (expected_ratio * 0.7):
            issues.append(f"Compression ratio too low: {metrics.compression_ratio:.1f}× (target: {expected_ratio}×)")
        
        # Semantic similarity check
        min_similarity = level.min_accuracy
        if metrics.semantic_similarity < (min_similarity * 0.95):
            issues.append(f"Semantic similarity too low: {metrics.semantic_similarity:.2%} (min: {min_similarity:.2%})")
        
        # Variance check
        if level in [CompressionLevel.LEVEL_3, CompressionLevel.LEVEL_4]:
            if metrics.variance > 0.4:
                issues.append(f"Variance too high for {level.name}: {metrics.variance:.2f}")
        else:
            if metrics.variance > 0.5:
                issues.append(f"Variance too high: {metrics.variance:.2f}")
        
        # Failure rate check
        if metrics.failure_rate > 0.2:
            issues.append(f"Failure rate too high: {metrics.failure_rate:.1%}")
        
        # Anchor coverage check
        if metrics.anchor_coverage < 0.6:
            issues.append(f"Anchor coverage too low: {metrics.anchor_coverage:.1%}")
        
        # Confidence check
        if metrics.confidence_mean < 0.5:
            issues.append(f"Mean confidence too low: {metrics.confidence_mean:.2f}")
        
        is_valid = len(issues) == 0
        
        return is_valid, issues


class ComprehensiveMetricsCalculator:
    """
    Calculates all metrics in one go.
    
    This is the main interface for metrics computation.
    """
    
    def __init__(self):
        self.semantic_calc = SemanticSimilarityCalculator()
        self.reconstruction_calc = ReconstructionScoreCalculator()
        self.variance_calc = VarianceCalculator()
        self.failure_calc = FailureRateCalculator()
        self.calibration_analyzer = ConfidenceCalibrationAnalyzer()
        self.validator = MetricsValidator()
    
    def calculate_all(
        self,
        original_tokens: List[str],
        compressed_tokens: List[CNFToken]
    ) -> CompressionMetrics:
        """
        Calculate all metrics.
        
        Args:
            original_tokens: Original tokenized text
            compressed_tokens: Compressed CNF tokens
        
        Returns:
            CompressionMetrics object with all scores
        """
        
        # Individual metrics
        compression_ratio = (
            len(original_tokens) / max(1, len(compressed_tokens))
        )
        
        semantic_similarity = self.semantic_calc.calculate(
            original_tokens, compressed_tokens
        )
        
        reconstruction_score = self.reconstruction_calc.calculate(
            compressed_tokens
        )
        
        variance = self.variance_calc.calculate(compressed_tokens)
        
        failure_rate = self.failure_calc.calculate(compressed_tokens)
        
        confidence_mean = (
            sum(t.confidence for t in compressed_tokens) / max(1, len(compressed_tokens))
        )
        
        anchor_coverage = (
            sum(len(t.subword_anchors) for t in compressed_tokens) / 
            (max(1, len(compressed_tokens)) * 3)  # Assume 3+ anchors ideal
        )
        anchor_coverage = min(1.0, anchor_coverage)
        
        return CompressionMetrics(
            compression_ratio=compression_ratio,
            semantic_similarity=semantic_similarity,
            reconstruction_score=reconstruction_score,
            variance=variance,
            failure_rate=failure_rate,
            confidence_mean=confidence_mean,
            anchor_coverage=anchor_coverage,
        )
    
    def validate_and_report(
        self,
        metrics: CompressionMetrics,
        level: CompressionLevel
    ) -> Dict[str, any]:
        """
        Validate metrics and generate report.
        
        Returns:
            {
                "is_valid": bool,
                "issues": [str],
                "summary": str,
            }
        """
        
        is_valid, issues = self.validator.validate_metrics(metrics, level)
        
        summary = (
            f"Compression Level: {level.name}\n"
            f"  Compression Ratio: {metrics.compression_ratio:.1f}×\n"
            f"  Semantic Similarity: {metrics.semantic_similarity:.2%}\n"
            f"  Reconstruction Score: {metrics.reconstruction_score:.2%}\n"
            f"  Variance: {metrics.variance:.3f}\n"
            f"  Failure Rate: {metrics.failure_rate:.1%}\n"
            f"  Mean Confidence: {metrics.confidence_mean:.2f}\n"
            f"  Anchor Coverage: {metrics.anchor_coverage:.1%}\n"
            f"  Valid: {'YES' if is_valid else 'NO'}\n"
        )
        
        if issues:
            summary += "\nIssues:\n"
            for issue in issues:
                summary += f"  - {issue}\n"
        
        return {
            "is_valid": is_valid,
            "issues": issues,
            "summary": summary,
        }
