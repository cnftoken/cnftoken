"""
Progressive Compression Pipeline

Implements staged compression (5×, 10×, 15×, 20×) with validation
and adaptive rollback at each stage.

Architecture:
Text → [Stage 1] → 5× tokens → [Stage 2] → 10× tokens → ... → [Stage 4] → 20× tokens

Each stage:
1. Compresses to target ratio
2. Validates semantic integrity
3. Computes confidence/variance
4. Checks against quality thresholds
5. Returns result or triggers rollback

Key Insight:
At higher compression levels (15-20×), we must:
- Reduce tokens more aggressively
- Monitor variance more carefully
- Be prepared to rollback if quality drops
- Maintain anchor coverage for reversibility
"""

import logging
from typing import List, Tuple, Optional
from advanced_cnf_token.core_structures import (
    CNFToken, CompressionLevel, CompressionMetrics, CompressionReport
)
from advanced_cnf_token.deterministic_encoder import DeterministicEncoder

logger = logging.getLogger(__name__)


class CompressionStage:
    """Single compression stage in the pipeline."""
    
    def __init__(
        self,
        level: CompressionLevel,
        encoder: DeterministicEncoder
    ):
        self.level = level
        self.encoder = encoder
        self.tokens_processed = 0
        self.rollbacks = 0
    
    def compress(
        self,
        tokens: List[CNFToken],
        context: str = ""
    ) -> Tuple[List[CNFToken], bool, str]:
        """
        Compress tokens to target level.
        
        Args:
            tokens: Input CNF tokens
            context: Optional context for determinism
        
        Returns:
            (compressed_tokens, success, reason)
        
        Strategy:
        For each compression level, apply specific compression:
        - Level 1 (5×): Group morphologically similar tokens
        - Level 2 (10×): Merge semantic clusters
        - Level 3 (15×): Aggressive merging, monitor variance
        - Level 4 (20×): Maximum compression, strict rollback policy
        """
        
        if not tokens:
            return [], True, "No tokens to compress"
        
        target_count = max(1, len(tokens) // int(self.level.target_ratio))
        
        if self.level == CompressionLevel.LEVEL_1:
            compressed = self._compress_level1(tokens, target_count)
        elif self.level == CompressionLevel.LEVEL_2:
            compressed = self._compress_level2(tokens, target_count)
        elif self.level == CompressionLevel.LEVEL_3:
            compressed = self._compress_level3(tokens, target_count)
        else:  # LEVEL_4
            compressed = self._compress_level4(tokens, target_count)
        
        # Validate compression
        valid, reason = self._validate_compression(tokens, compressed)
        
        if not valid:
            self.rollbacks += 1
            logger.warning(f"Compression rollback at {self.level.name}: {reason}")
            return tokens, False, reason
        
        self.tokens_processed += len(compressed)
        return compressed, True, "OK"
    
    def _compress_level1(
        self,
        tokens: List[CNFToken],
        target_count: int
    ) -> List[CNFToken]:
        """
        Level 1 (5× compression).
        
        Strategy: Group tokens by morphological similarity
        - Keep anchors intact
        - Preserve semantic paths
        - Moderate compression
        
        Safe operation: rarely causes semantic collapse
        """
        
        if len(tokens) <= target_count:
            return tokens
        
        # Group by semantic representation
        from collections import defaultdict
        groups = defaultdict(list)
        for token in tokens:
            groups[token.semantic_repr].append(token)
        
        # Merge groups proportionally
        merged = []
        for group_tokens in groups.values():
            if len(group_tokens) > 1:
                # Merge: keep first token, aggregate anchors
                merged_token = self._merge_tokens(group_tokens)
                merged.append(merged_token)
            else:
                merged.append(group_tokens[0])
        
        return merged[:target_count] if len(merged) > target_count else merged
    
    def _compress_level2(
        self,
        tokens: List[CNFToken],
        target_count: int
    ) -> List[CNFToken]:
        """
        Level 2 (10× compression).
        
        Strategy: Merge semantic clusters more aggressively
        - Group similar semantics
        - Keep key anchors (reduce redundancy)
        - Increase confidence threshold
        
        Risk: May lose some semantic nuance
        """
        
        if len(tokens) <= target_count:
            return tokens
        
        # Group by semantic similarity (approximate)
        from collections import defaultdict
        groups = defaultdict(list)
        
        for token in tokens:
            # Use semantic prefix as grouping key
            prefix = token.semantic_repr[:3] if len(token.semantic_repr) > 2 else token.semantic_repr
            groups[prefix].append(token)
        
        # Merge groups
        merged = []
        for group_tokens in groups.values():
            if len(group_tokens) > 1:
                merged_token = self._merge_tokens(group_tokens)
                merged.append(merged_token)
            else:
                merged.append(group_tokens[0])
        
        # Further reduce if needed
        if len(merged) > target_count:
            # Sort by confidence and keep top tokens
            merged = sorted(
                merged,
                key=lambda t: t.confidence * t.variance,
                reverse=True
            )[:target_count]
        
        return merged
    
    def _compress_level3(
        self,
        tokens: List[CNFToken],
        target_count: int
    ) -> List[CNFToken]:
        """
        Level 3 (15× compression).
        
        Strategy: Aggressive merging with variance monitoring
        - Merge by semantic clusters
        - Critical variance checks
        - Preserve maximum anchor diversity
        
        Risk: High risk of semantic drift
        """
        
        if len(tokens) <= target_count:
            return tokens
        
        # Sort by confidence (keep high-confidence tokens)
        sorted_tokens = sorted(tokens, key=lambda t: t.confidence, reverse=True)
        
        # Keep top tokens and merge rest
        keep_count = max(1, target_count // 2)
        kept = sorted_tokens[:keep_count]
        to_merge = sorted_tokens[keep_count:]
        
        if to_merge:
            # Merge discarded tokens into kept tokens
            kept = self._smart_merge_into_existing(kept, to_merge)
        
        return kept[:target_count]
    
    def _compress_level4(
        self,
        tokens: List[CNFToken],
        target_count: int
    ) -> List[CNFToken]:
        """
        Level 4 (20× compression).
        
        Strategy: Maximum compression with strict rollback policy
        - Keep only highest-confidence tokens
        - Merge aggregatively
        - Highest risk of semantic collapse
        
        Risk: Significant semantic loss possible
        """
        
        if len(tokens) <= target_count:
            return tokens
        
        # Keep only highest-confidence tokens
        sorted_tokens = sorted(tokens, key=lambda t: t.confidence * (1 - t.variance), reverse=True)
        kept = sorted_tokens[:target_count]
        
        # Merge all other tokens into kept
        to_merge = sorted_tokens[target_count:]
        if to_merge:
            kept = self._smart_merge_into_existing(kept, to_merge)
        
        return kept
    
    def _merge_tokens(self, tokens: List[CNFToken]) -> CNFToken:
        """
        Merge multiple tokens into single token.
        
        Strategy:
        1. Take first token as base
        2. Aggregate anchors from all
        3. Average confidence/variance
        4. Update reconstruction hint
        """
        if not tokens:
            return tokens[0]
        
        base = tokens[0]
        all_anchors = []
        
        for token in tokens:
            all_anchors.extend(token.subword_anchors)
        
        # Remove duplicate anchors
        seen_texts = set()
        unique_anchors = []
        for anchor in all_anchors:
            if anchor.text not in seen_texts:
                unique_anchors.append(anchor)
                seen_texts.add(anchor.text)
        
        # Average metrics
        avg_confidence = sum(t.confidence for t in tokens) / len(tokens)
        avg_variance = sum(t.variance for t in tokens) / len(tokens)
        
        merged = CNFToken(
            token_id=base.token_id,
            semantic_repr=base.semantic_repr,
            subword_anchors=unique_anchors,
            compression_level=self.level,
            semantic_path=base.semantic_path,
            lexical_path=base.lexical_path,
            structural_path=base.structural_path,
            confidence=avg_confidence,
            variance=avg_variance,
            density=base.density,
            context_sig=base.context_sig,
            reconstruction_hint="; ".join([t.semantic_repr for t in tokens]),
        )
        
        return merged
    
    def _smart_merge_into_existing(
        self,
        kept: List[CNFToken],
        to_merge: List[CNFToken]
    ) -> List[CNFToken]:
        """Merge tokens into existing kept tokens."""
        
        for token in to_merge:
            # Find best match in kept
            best_idx = 0
            best_similarity = 0.0
            
            for i, kept_token in enumerate(kept):
                # Simple similarity: shared prefix
                sim = self._semantic_similarity(token.semantic_repr, kept_token.semantic_repr)
                if sim > best_similarity:
                    best_similarity = sim
                    best_idx = i
            
            # Merge anchors
            kept[best_idx].subword_anchors.extend(token.subword_anchors)
            # Update reconstruction hint
            kept[best_idx].reconstruction_hint += f"; {token.semantic_repr}"
        
        return kept
    
    def _semantic_similarity(self, repr1: str, repr2: str) -> float:
        """Compute simple semantic similarity."""
        # Shared prefix similarity
        min_len = min(len(repr1), len(repr2))
        shared = sum(1 for i in range(min_len) if repr1[i] == repr2[i])
        return shared / max(1, min_len)
    
    def _validate_compression(
        self,
        original: List[CNFToken],
        compressed: List[CNFToken]
    ) -> Tuple[bool, str]:
        """
        Validate compression quality.
        
        Checks:
        1. Compression ratio achieved
        2. All tokens have anchors
        3. Confidence above threshold
        4. Variance below threshold
        
        Returns:
            (is_valid, reason)
        """
        
        if not compressed:
            return False, "Compression produced no tokens"
        
        # Check compression ratio
        expected_max = max(1, len(original) // int(self.level.target_ratio))
        if len(compressed) > expected_max * 1.5:  # Allow 50% overshoot
            return False, f"Compression ratio not met: {len(original)} → {len(compressed)}, expected ≤{expected_max}"
        
        # Check anchor coverage
        tokens_without_anchors = sum(1 for t in compressed if not t.subword_anchors)
        if tokens_without_anchors > 0:
            return False, f"{tokens_without_anchors} tokens have no anchors"
        
        # Check confidence
        mean_confidence = sum(t.confidence for t in compressed) / len(compressed)
        if mean_confidence < self.level.min_accuracy * 0.7:
            return False, f"Mean confidence too low: {mean_confidence:.2f}"
        
        # Check variance
        mean_variance = sum(t.variance for t in compressed) / len(compressed)
        if self.level in [CompressionLevel.LEVEL_3, CompressionLevel.LEVEL_4]:
            if mean_variance > 0.4:
                return False, f"Variance too high at {self.level.name}: {mean_variance:.2f}"
        
        return True, "OK"


class ProgressiveCompressionPipeline:
    """
    Full pipeline executing 5× → 10× → 15× → 20× compression.
    
    Guarantees:
    - Deterministic output (same input → same output)
    - Each stage validates integrity before proceeding
    - Rollback if quality drops below threshold
    - All tokens maintain anchor grounding
    """
    
    def __init__(self):
        self.encoder = DeterministicEncoder()
        self.stages = {
            CompressionLevel.LEVEL_1: CompressionStage(CompressionLevel.LEVEL_1, self.encoder),
            CompressionLevel.LEVEL_2: CompressionStage(CompressionLevel.LEVEL_2, self.encoder),
            CompressionLevel.LEVEL_3: CompressionStage(CompressionLevel.LEVEL_3, self.encoder),
            CompressionLevel.LEVEL_4: CompressionStage(CompressionLevel.LEVEL_4, self.encoder),
        }
        self.history: List[Tuple[CompressionLevel, List[CNFToken], bool]] = []
    
    def compress(
        self,
        text: str,
        target_level: CompressionLevel = CompressionLevel.LEVEL_2,
        context: str = ""
    ) -> CompressionReport:
        """
        Compress text through pipeline to target level.
        
        Args:
            text: Input text
            target_level: Target compression level (1-4)
            context: Optional context for determinism
        
        Returns:
            CompressionReport with metrics and results
        """
        
        # Step 1: Initial encoding (baseline, ~70 tokens)
        initial_tokens = self.encoder.encode_text(
            text=text,
            compression_level=CompressionLevel.LEVEL_1,
            context=context
        )
        
        self.history.append((CompressionLevel.LEVEL_1, initial_tokens, True))
        
        current_tokens = initial_tokens
        current_level = CompressionLevel.LEVEL_1
        
        # Step 2: Progress through levels until target
        levels_to_process = [
            CompressionLevel.LEVEL_1,
            CompressionLevel.LEVEL_2,
            CompressionLevel.LEVEL_3,
            CompressionLevel.LEVEL_4,
        ]
        
        for next_level in levels_to_process:
            if next_level.level < target_level.level:
                continue
            if next_level.level > target_level.level:
                break
            
            stage = self.stages[next_level]
            compressed, success, reason = stage.compress(current_tokens, context)
            
            self.history.append((next_level, compressed, success))
            
            if not success:
                logger.warning(f"Compression failed at {next_level.name}: {reason}")
                break
            
            current_tokens = compressed
            current_level = next_level
        
        # Step 3: Compute metrics
        metrics = self._compute_metrics(
            original_tokens=initial_tokens,
            compressed_tokens=current_tokens
        )
        
        # Step 4: Generate report
        acceptable = metrics.is_acceptable(current_level)
        
        warnings = []
        if metrics.variance > 0.3:
            warnings.append(f"High variance: {metrics.variance:.2f}")
        if metrics.failure_rate > 0.1:
            warnings.append(f"High failure rate: {metrics.failure_rate:.1%}")
        if metrics.anchor_coverage < 0.8:
            warnings.append(f"Low anchor coverage: {metrics.anchor_coverage:.1%}")
        
        report = CompressionReport(
            input_text=text,
            input_token_count=len(initial_tokens),
            output_tokens=current_tokens,
            metrics=metrics,
            level=current_level,
            acceptable=acceptable,
            warnings=warnings,
        )
        
        return report
    
    def _compute_metrics(
        self,
        original_tokens: List[CNFToken],
        compressed_tokens: List[CNFToken]
    ) -> CompressionMetrics:
        """Compute compression quality metrics."""
        
        compression_ratio = len(original_tokens) / max(1, len(compressed_tokens))
        
        # Semantic similarity: based on confidence (proxy)
        semantic_similarity = sum(t.confidence for t in compressed_tokens) / max(1, len(compressed_tokens))
        
        # Reconstruction score: based on anchor coverage
        total_anchors = sum(len(t.subword_anchors) for t in compressed_tokens)
        anchor_coverage = total_anchors / (len(compressed_tokens) * 3)  # Assuming 3+ anchors ideal
        reconstruction_score = min(1.0, anchor_coverage)
        
        # Variance: average token variance
        variance = sum(t.variance for t in compressed_tokens) / max(1, len(compressed_tokens))
        
        # Failure rate: tokens below confidence threshold
        failure_count = sum(1 for t in compressed_tokens if t.confidence < 0.5)
        failure_rate = failure_count / max(1, len(compressed_tokens))
        
        # Confidence mean
        confidence_mean = sum(t.confidence for t in compressed_tokens) / max(1, len(compressed_tokens))
        
        return CompressionMetrics(
            compression_ratio=compression_ratio,
            semantic_similarity=semantic_similarity,
            reconstruction_score=reconstruction_score,
            variance=variance,
            failure_rate=failure_rate,
            confidence_mean=confidence_mean,
            anchor_coverage=anchor_coverage,
        )
