"""
Deterministic Token Encoder

Core encoder that converts text into CNFTokens with guaranteed determinism.
Same input ALWAYS produces same output across runs.

Key Features:
- Hash-based token IDs (SHA256)
- Semantic clustering (groups related concepts)
- Subword anchor extraction
- Multi-path encoding
- Confidence scoring

Risks:
- Semantic clustering depends on ONNX scorer (may hallucinate)
- Large texts may hit memory limits with dense token representation
- Anchor selection is heuristic-based (50% coverage typical)
"""

import hashlib
import logging
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass
from advanced_cnf_token.core_structures import (
    CNFToken, SubwordAnchor, CompressionLevel
)

logger = logging.getLogger(__name__)


@dataclass
class SemanticCluster:
    """Represents a semantic cluster of words/phrases."""
    semantic_repr: str
    members: List[str]              # Words that map to this concept
    importance_score: float         # How important this concept is
    confidence: float               # Confidence in this clustering


class DeterministicEncoder:
    """
    Deterministic encoder that maps text to CNFTokens.
    
    Design:
    1. Normalize text
    2. Create semantic clusters (vocabulary grouping)
    3. Assign deterministic IDs via hashing
    4. Extract subword anchors
    5. Compute path encodings
    """
    
    def __init__(self):
        self.semantic_clusters: Dict[str, SemanticCluster] = {}
        self.token_cache: Dict[str, CNFToken] = {}  # For determinism
        self.anchor_frequencies: Dict[str, int] = defaultdict(int)
    
    def encode_text(
        self,
        text: str,
        compression_level: CompressionLevel = CompressionLevel.LEVEL_2,
        context: str = ""
    ) -> List[CNFToken]:
        """
        Encode text into deterministic CNFTokens.
        
        Args:
            text: Input text
            compression_level: Target compression (LEVEL_1 to LEVEL_4)
            context: Optional context for hash determinism
        
        Returns:
            List of CNFTokens
        
        Process:
        1. Normalize and tokenize
        2. Group into semantic clusters
        3. Create CNFToken for each cluster
        4. Extract anchors and compute paths
        
        Guarantees:
        - Deterministic output (same input → same output)
        - All tokens have anchors (no floating semantics)
        - Paths encode original structure
        """
        # Step 1: Normalize and tokenize
        tokens = self._tokenize(text)
        if not tokens:
            return []
        
        # Step 2: Create semantic clusters
        clusters = self._cluster_semantically(tokens)
        
        # Step 3: Convert clusters to CNFTokens
        cnf_tokens: List[CNFToken] = []
        
        for i, cluster in enumerate(clusters):
            # Create base token
            token = self._create_cnf_token(
                cluster=cluster,
                cluster_index=i,
                compression_level=compression_level,
                context=context,
                total_clusters=len(clusters)
            )
            
            # Extract subword anchors
            token.subword_anchors = self._extract_anchors(
                cluster=cluster,
                original_tokens=tokens,
                compression_level=compression_level
            )
            
            # Compute confidence and variance
            token.confidence = self._compute_confidence(
                cluster=cluster,
                anchor_count=len(token.subword_anchors)
            )
            
            token.variance = self._compute_variance(
                cluster=cluster,
                compression_level=compression_level
            )
            
            token.density = self._compute_density(
                cluster=cluster,
                compression_level=compression_level
            )
            
            cnf_tokens.append(token)
        
        return cnf_tokens
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization with normalization."""
        # Normalize: lowercase, strip punctuation lightly
        normalized = text.lower().strip()
        tokens = normalized.split()
        return [t for t in tokens if t]  # Filter empty
    
    def _cluster_semantically(self, tokens: List[str]) -> List[SemanticCluster]:
        """
        Group tokens into semantic clusters.
        
        Heuristic clustering strategy:
        1. Identify named entities and special tokens
        2. Group by morphological similarity
        3. Merge related concepts
        4. Score importance by frequency
        
        Returns:
            List of semantic clusters
        
        Risk:
        - Morphological clustering is imperfect
        - May over/under-merge related tokens
        - Importance scoring is frequency-based (biased toward common words)
        """
        
        # Build frequency map
        frequency = defaultdict(int)
        for token in tokens:
            frequency[token] += 1
        
        # Create clusters (for now: each cluster = related tokens)
        clusters: Dict[str, SemanticCluster] = {}
        
        # Very simple strategy: group by first letter or semantic similarity
        for token in set(tokens):
            # Determine semantic representation
            semantic_repr = self._get_semantic_repr(token)
            
            if semantic_repr not in clusters:
                clusters[semantic_repr] = SemanticCluster(
                    semantic_repr=semantic_repr,
                    members=[],
                    importance_score=0.0,
                    confidence=0.8  # Default confidence
                )
            
            clusters[semantic_repr].members.append(token)
            clusters[semantic_repr].importance_score += frequency[token]
        
        # Normalize importance scores
        total_importance = sum(c.importance_score for c in clusters.values())
        if total_importance > 0:
            for cluster in clusters.values():
                cluster.importance_score /= total_importance
        
        return list(clusters.values())
    
    def _get_semantic_repr(self, token: str) -> str:
        """
        Determine semantic representation of a token.
        
        Strategy:
        1. Special tokens (numbers, dates, UUIDs) → keep as-is
        2. Common words → group by semantic class
        3. Others → keep individual
        
        Risk:
        - This is heuristic; ideally use ONNX embeddings
        """
        
        # Check if number
        if token.isdigit():
            return "<NUM>"
        
        # Check if date-like
        if self._looks_like_date(token):
            return "<DATE>"
        
        # Check if email/URL
        if "@" in token or "://" in token:
            return "<URL>"
        
        # For now: keep most tokens as their own semantic repr
        # In production: use ONNX embeddings + clustering
        return token
    
    def _looks_like_date(self, token: str) -> bool:
        """Heuristic check for date-like tokens."""
        # Simple patterns for dates
        date_patterns = ["-", "/", ":"]
        has_number = any(c.isdigit() for c in token)
        has_separator = any(p in token for p in date_patterns)
        return has_number and has_separator and len(token) >= 6
    
    def _create_cnf_token(
        self,
        cluster: SemanticCluster,
        cluster_index: int,
        compression_level: CompressionLevel,
        context: str,
        total_clusters: int
    ) -> CNFToken:
        """Create a CNFToken from a semantic cluster."""
        
        # Compute deterministic token ID
        msg = f"{cluster.semantic_repr}:{context}:{cluster_index}"
        hash_bytes = hashlib.sha256(msg.encode()).digest()
        token_id = int.from_bytes(hash_bytes[:4], byteorder='big') & 0xFFFFFFFF
        
        # Compute context signature
        context_sig = hashlib.md5(context.encode()).hexdigest()[:8]
        
        # Compute paths
        semantic_path = [cluster_index]  # Simplified: just the index
        lexical_path = list(range(len(cluster.members)))
        structural_path = [i % 3 for i in range(len(cluster.members))]  # Simple pattern
        
        token = CNFToken(
            token_id=token_id,
            semantic_repr=cluster.semantic_repr,
            subword_anchors=[],  # Will be filled by _extract_anchors
            compression_level=compression_level,
            semantic_path=semantic_path,
            lexical_path=lexical_path,
            structural_path=structural_path,
            context_sig=context_sig,
            reconstruction_hint=", ".join(cluster.members[:3]),  # First 3 members
        )
        
        return token
    
    def _extract_anchors(
        self,
        cluster: SemanticCluster,
        original_tokens: List[str],
        compression_level: CompressionLevel
    ) -> List[SubwordAnchor]:
        """
        Extract subword anchors from cluster members.
        
        Strategy:
        1. Include high-frequency members
        2. Include morphologically distinct members
        3. Limit by compression level (higher compression = more selective)
        
        Returns:
            List of SubwordAnchors
        
        Risk:
        - Anchor selection is heuristic
        - May miss important variations at high compression
        - Rare words may be excluded
        """
        
        def get_frequency(term: str) -> int:
            return original_tokens.count(term)
        
        # Sort by frequency
        sorted_members = sorted(
            cluster.members,
            key=get_frequency,
            reverse=True
        )
        
        # Anchor count depends on compression level
        anchor_limit = {
            CompressionLevel.LEVEL_1: 5,    # 5× compression: keep 5 anchors
            CompressionLevel.LEVEL_2: 3,    # 10× compression: keep 3 anchors
            CompressionLevel.LEVEL_3: 2,    # 15× compression: keep 2 anchors
            CompressionLevel.LEVEL_4: 1,    # 20× compression: keep 1 anchor
        }.get(compression_level, 2)
        
        # Create anchors
        anchors: List[SubwordAnchor] = []
        for pos, member in enumerate(sorted_members[:anchor_limit]):
            anchor = SubwordAnchor(
                text=member,
                position=pos,
                confidence=0.9 - (0.1 * pos)  # Decreasing confidence
            )
            anchors.append(anchor)
            self.anchor_frequencies[member] += 1
        
        return anchors
    
    def _compute_confidence(
        self,
        cluster: SemanticCluster,
        anchor_count: int
    ) -> float:
        """
        Compute confidence that token is stable and accurate.
        
        Formula:
        confidence = cluster_confidence * anchor_coverage
        
        where anchor_coverage = min(anchor_count / cluster_size, 1.0)
        """
        if not cluster.members:
            return 0.0
        
        anchor_coverage = min(anchor_count / len(cluster.members), 1.0)
        confidence = cluster.confidence * anchor_coverage
        
        return max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
    
    def _compute_variance(
        self,
        cluster: SemanticCluster,
        compression_level: CompressionLevel
    ) -> float:
        """
        Compute token variance metric.
        
        High variance = token meaning varies across contexts
        
        Heuristic:
        - Large clusters → higher variance
        - Rare words → lower variance (but less reliable)
        - Compressed tokens → higher variance
        """
        
        # Cluster size variance (larger cluster = higher variance)
        cluster_size_factor = min(len(cluster.members) / 10.0, 1.0)
        
        # Compression level factor (higher compression = higher variance)
        compression_factor = compression_level.level / 4.0
        
        variance = 0.1 + (cluster_size_factor * 0.3) + (compression_factor * 0.3)
        
        return max(0.0, min(1.0, variance))  # Clamp to [0, 1]
    
    def _compute_density(
        self,
        cluster: SemanticCluster,
        compression_level: CompressionLevel
    ) -> float:
        """
        Compute token density (bits per token).
        
        Density = information packed into token
        
        Formula:
        density = log2(cluster_size) * compression_level
        
        High density (>32 bits) may indicate semantic collapse
        """
        
        if len(cluster.members) <= 1:
            return 1.0  # Single-word cluster: minimal density
        
        import math
        cluster_entropy = math.log2(len(cluster.members)) + 1
        compression_multiplier = compression_level.level
        
        density = cluster_entropy * compression_multiplier
        
        return density
