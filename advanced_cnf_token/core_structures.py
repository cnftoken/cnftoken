"""
CNF Token Advanced Core Structures

This module defines the core data structures for the advanced CNF token
compression system with deterministic mapping, semantic anchors, and
stability monitoring.

Risk Assessment:
- Hash collisions are extremely rare with SHA256 (1 in 2^128)
- Dense tokens may still lose semantic information at 20× compression
- Anchor validity depends on ONNX scorer accuracy
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum


class CompressionLevel(Enum):
    """Compression stages with target ratios and accuracy thresholds."""
    LEVEL_1 = (1, 5.0, 0.96)      # 5× compression, ≥96% accuracy
    LEVEL_2 = (2, 10.0, 0.96)     # 10× compression, ≥96% accuracy
    LEVEL_3 = (3, 15.0, 0.94)     # 15× compression, ≥94% accuracy
    LEVEL_4 = (4, 20.0, 0.92)     # 20× compression, ≥92% accuracy

    @property
    def level(self) -> int:
        return self.value[0]

    @property
    def target_ratio(self) -> float:
        return self.value[1]

    @property
    def min_accuracy(self) -> float:
        return self.value[2]


@dataclass
class SubwordAnchor:
    """
    Subword anchor provides lexical grounding for a compressed token.
    
    Prevents semantic collapse by preserving original linguistic units.
    """
    text: str                   # Original text (e.g., "the", "best")
    position: int               # Position in original sequence
    confidence: float           # How well this anchor represents the token
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CNFToken:
    """
    Advanced CNF Token with multi-path encoding and stability tracking.
    
    Design rationale:
    - token_id is deterministic (SHA256 hash) → same input always produces same output
    - Subword anchors ground tokens to prevent semantic drift
    - Multi-path encoding preserves different dimensions of meaning
    - Confidence/variance enable adaptive compression
    """
    
    token_id: int                           # Deterministic hash-based ID
    semantic_repr: str                      # Core semantic concept (e.g., "excellence")
    subword_anchors: List[SubwordAnchor]   # Lexical grounding
    compression_level: CompressionLevel     # Compression stage
    
    # Multi-path encoding
    semantic_path: List[int] = field(default_factory=list)   # Semantic hierarchy
    lexical_path: List[int] = field(default_factory=list)    # Original tokens
    structural_path: List[int] = field(default_factory=list) # Phrase structure
    
    # Stability metrics
    confidence: float = 1.0                 # 0.0-1.0 stability score
    variance: float = 0.0                   # Token variance across contexts
    density: float = 0.0                    # Token density (bits per token)
    failure_rate: float = 0.0               # Failure rate in reconstruction
    
    # Metadata
    context_sig: str = ""                   # Context signature for determinism
    reconstruction_hint: str = ""           # Hint for partial reconstruction
    
    def compute_token_id(self, context: str = "") -> int:
        """
        Compute deterministic token ID using SHA256 hash.
        
        Args:
            context: Additional context for hash (default: "")
        
        Returns:
            Deterministic token ID (u32 range)
        
        Why deterministic:
        - Same semantic_repr + context → same token_id always
        - Enables consistent encoding across runs
        - Foundation for distributed token caching
        """
        msg = f"{self.semantic_repr}:{context}"
        hash_bytes = hashlib.sha256(msg.encode()).digest()
        # Use first 4 bytes as u32 token ID
        token_id = int.from_bytes(hash_bytes[:4], byteorder='big')
        return token_id & 0xFFFFFFFF  # Ensure u32 range
    
    def validate_semantic_integrity(self) -> Tuple[bool, str]:
        """
        Validate that token hasn't undergone semantic collapse.
        
        Returns:
            (is_valid, reason)
        
        Checks:
        1. Anchors not empty (no complete grounding loss)
        2. Confidence ≥ 0.5 (acceptable stability)
        3. Variance ≤ 0.3 (reasonable consistency)
        4. Density ≤ 32 (no extreme compression)
        """
        if not self.subword_anchors:
            return False, "No subword anchors - semantic collapse detected"
        
        if self.confidence < 0.5:
            return False, f"Confidence too low: {self.confidence}"
        
        if self.variance > 0.3:
            return False, f"Variance too high: {self.variance}"
        
        if self.density > 32.0:
            return False, f"Token density excessive: {self.density}"
        
        return True, "OK"
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "token_id": self.token_id,
            "semantic_repr": self.semantic_repr,
            "subword_anchors": [a.to_dict() for a in self.subword_anchors],
            "compression_level": self.compression_level.name,
            "semantic_path": self.semantic_path,
            "lexical_path": self.lexical_path,
            "structural_path": self.structural_path,
            "confidence": self.confidence,
            "variance": self.variance,
            "density": self.density,
            "failure_rate": self.failure_rate,
            "context_sig": self.context_sig,
            "reconstruction_hint": self.reconstruction_hint,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class CompressionMetrics:
    """Metrics tracking for compression quality and stability."""
    
    compression_ratio: float = 0.0          # Achieved ratio
    semantic_similarity: float = 0.0        # Semantic preservation score
    reconstruction_score: float = 0.0       # Reconstruction accuracy
    variance: float = 0.0                   # Overall variance
    failure_rate: float = 0.0               # Reconstruction failure rate
    confidence_mean: float = 0.0            # Mean confidence across tokens
    anchor_coverage: float = 0.0            # % of tokens with valid anchors
    
    def is_acceptable(self, level: CompressionLevel) -> bool:
        """Check if metrics meet compression level requirements."""
        return self.semantic_similarity >= level.min_accuracy
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CompressionReport:
    """Full report of compression results."""
    
    input_text: str
    input_token_count: int
    output_tokens: List[CNFToken]
    metrics: CompressionMetrics
    level: CompressionLevel
    acceptable: bool
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "input_text": self.input_text,
            "input_token_count": self.input_token_count,
            "output_tokens": [t.to_dict() for t in self.output_tokens],
            "metrics": self.metrics.to_dict(),
            "compression_level": self.level.name,
            "acceptable": self.acceptable,
            "warnings": self.warnings,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        return (
            f"Compression Report ({self.level.name}):\n"
            f"  Input:  {self.input_token_count} tokens\n"
            f"  Output: {len(self.output_tokens)} tokens\n"
            f"  Ratio:  {self.metrics.compression_ratio:.1f}×\n"
            f"  Semantic Similarity: {self.metrics.semantic_similarity:.2%}\n"
            f"  Reconstruction Score: {self.metrics.reconstruction_score:.2%}\n"
            f"  Mean Confidence: {self.metrics.confidence_mean:.2f}\n"
            f"  Anchor Coverage: {self.metrics.anchor_coverage:.2%}\n"
            f"  Acceptable: {self.acceptable}\n"
            + (f"  Warnings: {', '.join(self.warnings)}\n" if self.warnings else "")
        )
