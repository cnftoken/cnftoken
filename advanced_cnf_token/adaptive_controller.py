"""
Adaptive Compression Controller

Dynamically adjusts compression level based on:
- Entropy (randomness/unpredictability in text)
- Token density (semantic compression)
- Semantic importance (rarity, domain-specificity)
- Stability indicators (variance, confidence)

Strategy:
- Low entropy text → can compress more aggressively (20×)
- High entropy text → be conservative (5-10×)
- Important tokens → always preserve
- Unstable tokens → rollback

This module is the "brain" that decides what compression level
is appropriate for a given input.
"""

import logging
import math
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from advanced_cnf_token.core_structures import (
    CNFToken, CompressionLevel, CompressionMetrics
)

logger = logging.getLogger(__name__)


@dataclass
class TextCharacteristics:
    """Characteristics of input text affecting compression decisions."""
    entropy: float                  # Shannon entropy (0-1 normalized)
    unique_token_ratio: float       # Unique tokens / total tokens
    token_frequency_skew: float     # Zipf's law coefficient
    average_token_length: float     # Mean token length
    language_diversity: float       # 0 = monolingual, 1 = highly diverse
    named_entity_density: float     # % of tokens that are NER entities


class TextAnalyzer:
    """Analyzes text to determine compression suitability."""
    
    def __init__(self):
        self.common_words = {
            'the', 'a', 'an', 'and', 'or', 'is', 'was', 'be', 'been',
            'of', 'to', 'in', 'on', 'at', 'for', 'with', 'by', 'from',
            'that', 'this', 'which', 'who', 'when', 'where', 'what',
            'en', 'de', 'et', 'le', 'la', 'los', 'las'  # Common foreign
        }
    
    def analyze(self, tokens: List[str]) -> TextCharacteristics:
        """
        Analyze text tokens to determine compression suitability.
        
        Returns:
            TextCharacteristics with metrics
        """
        
        if not tokens:
            return TextCharacteristics(
                entropy=0.0,
                unique_token_ratio=0.0,
                token_frequency_skew=0.0,
                average_token_length=0.0,
                language_diversity=0.0,
                named_entity_density=0.0,
            )
        
        # Basic statistics
        total_tokens = len(tokens)
        unique_tokens = len(set(tokens))
        unique_ratio = unique_tokens / total_tokens if total_tokens > 0 else 0
        
        # Token length
        avg_length = sum(len(t) for t in tokens) / total_tokens if total_tokens > 0 else 0
        
        # Entropy
        entropy = self._compute_entropy(tokens)
        
        # Frequency skew (Zipf's law)
        skew = self._compute_frequency_skew(tokens)
        
        # Language diversity (assumed from unique ratio + entropy)
        diversity = min(1.0, unique_ratio * entropy)
        
        # Named entity density (heuristic)
        ner_count = sum(1 for t in tokens if self._is_likely_entity(t))
        ner_density = ner_count / total_tokens if total_tokens > 0 else 0
        
        return TextCharacteristics(
            entropy=entropy,
            unique_token_ratio=unique_ratio,
            token_frequency_skew=skew,
            average_token_length=avg_length,
            language_diversity=diversity,
            named_entity_density=ner_density,
        )
    
    def _compute_entropy(self, tokens: List[str]) -> float:
        """
        Compute Shannon entropy of token distribution.
        
        High entropy = diverse/unpredictable text (news, technical)
        Low entropy = repetitive/formulaic text (poetry, code)
        
        Returns normalized entropy [0, 1]
        """
        if not tokens:
            return 0.0
        
        freq = Counter(tokens)
        total = len(tokens)
        
        entropy = 0.0
        for count in freq.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Normalize to [0, 1]
        max_entropy = math.log2(min(len(freq), total))
        if max_entropy > 0:
            entropy = entropy / max_entropy
        
        return min(1.0, entropy)
    
    def _compute_frequency_skew(self, tokens: List[str]) -> float:
        """
        Compute Zipf's law skew.
        
        High skew = few tokens dominate (compressible)
        Low skew = distribution is flat (hard to compress)
        
        Returns: Zipf coefficient [0, 2]
        """
        if len(set(tokens)) <= 1:
            return 0.0
        
        freq = sorted(Counter(tokens).values(), reverse=True)
        
        # Simple skew metric: ratio of top 20% vs bottom 20%
        cutoff = max(1, len(freq) // 5)
        top_sum = sum(freq[:cutoff])
        bottom_sum = sum(freq[-cutoff:])
        
        if bottom_sum == 0:
            return 2.0
        
        ratio = top_sum / bottom_sum
        return min(2.0, math.log2(ratio + 1))
    
    def _is_likely_entity(self, token: str) -> bool:
        """Heuristic check if token is likely named entity."""
        # Capitalized, uppercase, or contains digits
        if token[0].isupper() and token not in self.common_words:
            return True
        if token.isupper() and len(token) > 1:
            return True
        if any(c.isdigit() for c in token):
            return True
        return False


class AdaptiveCompressionController:
    """
    Dynamically selects compression level based on text characteristics.
    
    Decision Logic:
    
    1. Analyze text entropy, diversity, frequency skew
    2. Score compression suitability (0-1)
    3. Map to optimal compression level:
       - Score 0.0-0.3: LEVEL_1 (5×) - conservative
       - Score 0.3-0.6: LEVEL_2 (10×) - balanced
       - Score 0.6-0.8: LEVEL_3 (15×) - aggressive
       - Score 0.8-1.0: LEVEL_4 (20×) - maximum
    4. Apply additional constraints:
       - Named entities → reduce compression by 1 level
       - High variance → reduce compression by 1 level
       - Low confidence → reduce compression by 1 level
    """
    
    def __init__(self):
        self.analyzer = TextAnalyzer()
        self.decision_history: List[Tuple[str, CompressionLevel, float]] = []
    
    def select_compression_level(
        self,
        tokens: List[str],
        user_preference: Optional[CompressionLevel] = None,
        metrics: Optional[CompressionMetrics] = None
    ) -> Tuple[CompressionLevel, Dict[str, float]]:
        """
        Select optimal compression level for given text.
        
        Args:
            tokens: Input tokens
            user_preference: User-requested level (optional)
            metrics: Current compression metrics (optional)
        
        Returns:
            (selected_level, decision_factors)
        
        Strategy:
        - If user specified level, validate it's safe
        - Otherwise, compute optimal level from characteristics
        - Apply safety constraints if metrics indicate instability
        """
        
        characteristics = self.analyzer.analyze(tokens)
        
        # Compute suitability score
        suitability = self._compute_suitability_score(characteristics)
        
        # Map to compression level
        if user_preference:
            level = user_preference
            logger.info(f"Using user-preferred level: {level.name}")
        else:
            level = self._map_score_to_level(suitability)
            logger.info(f"Auto-selected compression level: {level.name} (suitability: {suitability:.2f})")
        
        # Apply safety constraints
        if metrics:
            level = self._apply_safety_constraints(level, metrics)
        
        level = self._apply_content_constraints(level, characteristics)
        
        decision_factors = {
            "suitability_score": suitability,
            "entropy": characteristics.entropy,
            "unique_token_ratio": characteristics.unique_token_ratio,
            "token_frequency_skew": characteristics.token_frequency_skew,
            "language_diversity": characteristics.language_diversity,
            "named_entity_density": characteristics.named_entity_density,
        }
        
        return level, decision_factors
    
    def _compute_suitability_score(self, chars: TextCharacteristics) -> float:
        """
        Compute compression suitability score.
        
        High score = text is compressible (formulaic, low entropy)
        Low score = text is not compressible (diverse, high entropy)
        
        Formula:
        suitability = (1 - entropy) * (1 - diversity) * (1 + skew)
        
        Normalized to [0, 1]
        """
        
        # Entropy factor: low entropy is good
        entropy_factor = 1.0 - chars.entropy
        
        # Diversity factor: low diversity is good (repetitive)
        diversity_factor = 1.0 - chars.language_diversity
        
        # Skew factor: high skew (Zipfian) is good
        skew_factor = 1.0 + (chars.token_frequency_skew / 4.0)
        
        # Unique token ratio factor
        unique_factor = 1.0 - chars.unique_token_ratio
        
        # Combine
        suitability = (entropy_factor * 0.3 + 
                      diversity_factor * 0.2 + 
                      skew_factor * 0.3 + 
                      unique_factor * 0.2)
        
        return min(1.0, max(0.0, suitability))
    
    def _map_score_to_level(self, score: float) -> CompressionLevel:
        """Map suitability score to compression level."""
        
        if score < 0.25:
            return CompressionLevel.LEVEL_1
        elif score < 0.5:
            return CompressionLevel.LEVEL_2
        elif score < 0.75:
            return CompressionLevel.LEVEL_3
        else:
            return CompressionLevel.LEVEL_4
    
    def _apply_safety_constraints(
        self,
        level: CompressionLevel,
        metrics: CompressionMetrics
    ) -> CompressionLevel:
        """
        Apply safety constraints based on compression metrics.
        
        Constraints:
        - High variance → reduce by 1 level
        - Low confidence → reduce by 1 level
        - High failure rate → reduce by 1-2 levels
        """
        
        adjusted_level = level
        
        # Variance constraint
        if metrics.variance > 0.4:
            adjusted_level = self._reduce_level(adjusted_level)
            logger.warning(f"Reducing compression due to high variance: {metrics.variance:.2f}")
        
        # Confidence constraint
        if metrics.confidence_mean < 0.6:
            adjusted_level = self._reduce_level(adjusted_level)
            logger.warning(f"Reducing compression due to low confidence: {metrics.confidence_mean:.2f}")
        
        # Failure rate constraint
        if metrics.failure_rate > 0.2:
            adjusted_level = self._reduce_level(adjusted_level)
            adjusted_level = self._reduce_level(adjusted_level)
            logger.warning(f"Reducing compression due to failure rate: {metrics.failure_rate:.1%}")
        
        return adjusted_level
    
    def _apply_content_constraints(
        self,
        level: CompressionLevel,
        chars: TextCharacteristics
    ) -> CompressionLevel:
        """
        Apply constraints based on content characteristics.
        
        Constraints:
        - High NER density → reduce compression
        - Low frequency skew → reduce compression
        """
        
        adjusted_level = level
        
        # Named entity constraint (entities are hard to compress)
        if chars.named_entity_density > 0.3:
            adjusted_level = self._reduce_level(adjusted_level)
            logger.info(f"Reducing compression due to high NER density: {chars.named_entity_density:.1%}")
        
        # Frequency skew constraint
        if chars.token_frequency_skew < 0.3:
            adjusted_level = self._reduce_level(adjusted_level)
            logger.info(f"Reducing compression due to low frequency skew: {chars.token_frequency_skew:.2f}")
        
        return adjusted_level
    
    def _reduce_level(self, level: CompressionLevel) -> CompressionLevel:
        """Safely reduce compression level by 1 step."""
        
        if level == CompressionLevel.LEVEL_4:
            return CompressionLevel.LEVEL_3
        elif level == CompressionLevel.LEVEL_3:
            return CompressionLevel.LEVEL_2
        elif level == CompressionLevel.LEVEL_2:
            return CompressionLevel.LEVEL_1
        else:
            return CompressionLevel.LEVEL_1  # Floor
    
    def should_attempt_higher_compression(
        self,
        current_level: CompressionLevel,
        current_metrics: CompressionMetrics
    ) -> Tuple[bool, str]:
        """
        Determine if should attempt next compression level.
        
        Returns:
            (should_attempt, reason)
        """
        
        if current_level == CompressionLevel.LEVEL_4:
            return False, "Already at maximum compression"
        
        # Check if current level is stable
        if current_metrics.variance > 0.3:
            return False, f"Current variance too high: {current_metrics.variance:.2f}"
        
        if current_metrics.confidence_mean < 0.7:
            return False, f"Current confidence too low: {current_metrics.confidence_mean:.2f}"
        
        if current_metrics.failure_rate > 0.1:
            return False, f"Current failure rate too high: {current_metrics.failure_rate:.1%}"
        
        return True, "OK to attempt higher compression"
    
    def get_recommendation(
        self,
        tokens: List[str],
        current_level: CompressionLevel,
        metrics: CompressionMetrics
    ) -> Dict[str, any]:
        """
        Get comprehensive compression recommendation.
        
        Returns:
            {
                "recommended_level": CompressionLevel,
                "reason": str,
                "next_steps": [str],
                "risk_level": str,
            }
        """
        
        next_level, factors = self.select_compression_level(tokens, metrics=metrics)
        
        if next_level == current_level:
            reason = "Current compression level is optimal"
        elif next_level > current_level:
            reason = "Can safely increase compression"
        else:
            reason = "Should reduce compression for stability"
        
        # Determine risk level
        if metrics.variance > 0.4 or metrics.failure_rate > 0.2:
            risk_level = "HIGH"
        elif metrics.variance > 0.2 or metrics.failure_rate > 0.1:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        next_steps = []
        if next_level.level > current_level.level:
            next_steps.append("Increase compression to next level")
        elif next_level.level < current_level.level:
            next_steps.append("Rollback to lower compression level")
        else:
            next_steps.append("Maintain current compression level")
        
        if metrics.anchor_coverage < 0.7:
            next_steps.append("Review token anchors for completeness")
        
        if metrics.semantic_similarity < 0.9:
            next_steps.append("Validate semantic preservation")
        
        return {
            "recommended_level": next_level.name,
            "reason": reason,
            "next_steps": next_steps,
            "risk_level": risk_level,
            "factors": factors,
        }
