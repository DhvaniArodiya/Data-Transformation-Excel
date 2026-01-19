"""
Global Function Library - Pattern Memory System
Stores and retrieves successful transformation patterns for reuse.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from ..config import get_settings


@dataclass
class TransformationPattern:
    """A learned transformation pattern."""
    pattern_id: str
    source_signature: str  # Hash of source column characteristics
    source_column_name: str
    source_semantic_type: str
    target_column_name: str
    function_used: str
    params_used: Dict[str, Any]
    success_count: int = 1
    last_used: str = ""
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransformationPattern":
        return cls(**data)


class GlobalLibrary:
    """
    Global Function Library for storing and retrieving transformation patterns.
    
    This system learns from successful transformations to:
    1. Auto-suggest mappings for similar columns
    2. Reduce LLM API calls for known patterns
    3. Improve accuracy over time
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the library.
        
        Args:
            storage_path: Path to store patterns. Defaults to jobs_dir/patterns.json
        """
        settings = get_settings()
        settings.ensure_directories()
        
        self.storage_path = storage_path or (settings.jobs_dir / "patterns.json")
        self._patterns: Dict[str, TransformationPattern] = {}
        self._index_by_source: Dict[str, List[str]] = {}  # source_signature -> pattern_ids
        self._index_by_function: Dict[str, List[str]] = {}  # function_name -> pattern_ids
        
        self._load()
    
    def _load(self):
        """Load patterns from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                for pattern_data in data.get("patterns", []):
                    pattern = TransformationPattern.from_dict(pattern_data)
                    self._patterns[pattern.pattern_id] = pattern
                    self._update_indices(pattern)
            except Exception as e:
                print(f"Warning: Failed to load patterns: {e}")
    
    def _save(self):
        """Save patterns to storage."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "patterns": [p.to_dict() for p in self._patterns.values()]
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _update_indices(self, pattern: TransformationPattern):
        """Update search indices for a pattern."""
        # Index by source signature
        if pattern.source_signature not in self._index_by_source:
            self._index_by_source[pattern.source_signature] = []
        if pattern.pattern_id not in self._index_by_source[pattern.source_signature]:
            self._index_by_source[pattern.source_signature].append(pattern.pattern_id)
        
        # Index by function
        if pattern.function_used not in self._index_by_function:
            self._index_by_function[pattern.function_used] = []
        if pattern.pattern_id not in self._index_by_function[pattern.function_used]:
            self._index_by_function[pattern.function_used].append(pattern.pattern_id)
    
    @staticmethod
    def create_signature(
        column_name: str,
        semantic_type: Optional[str] = None,
        sample_values: Optional[List[str]] = None,
    ) -> str:
        """
        Create a signature hash for a source column.
        
        Args:
            column_name: Column name
            semantic_type: Semantic type (phone, email, etc.)
            sample_values: Sample values from the column
            
        Returns:
            Signature hash string
        """
        # Normalize column name
        normalized_name = column_name.lower().replace("_", "").replace(" ", "").replace("-", "")
        
        # Create signature components
        components = [normalized_name]
        
        if semantic_type:
            components.append(semantic_type.lower())
        
        if sample_values:
            # Add pattern hints from samples
            for val in sample_values[:3]:
                val_str = str(val).strip()
                if "@" in val_str:
                    components.append("has_at")
                if any(c.isdigit() for c in val_str):
                    components.append("has_digits")
                if len(val_str) > 50:
                    components.append("long_text")
        
        # Create hash
        signature_str = "|".join(sorted(set(components)))
        return hashlib.md5(signature_str.encode()).hexdigest()[:12]
    
    def find_patterns(
        self,
        column_name: str,
        semantic_type: Optional[str] = None,
        sample_values: Optional[List[str]] = None,
        target_column: Optional[str] = None,
        min_confidence: float = 0.5,
    ) -> List[TransformationPattern]:
        """
        Find matching patterns for a source column.
        
        Args:
            column_name: Source column name
            semantic_type: Semantic type if known
            sample_values: Sample values
            target_column: Target column name (if known)
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of matching patterns, sorted by success_count
        """
        signature = self.create_signature(column_name, semantic_type, sample_values)
        
        # Find by signature
        pattern_ids = self._index_by_source.get(signature, [])
        patterns = [self._patterns[pid] for pid in pattern_ids if pid in self._patterns]
        
        # Filter by target column if specified
        if target_column:
            target_normalized = target_column.lower().replace("_", "")
            patterns = [
                p for p in patterns 
                if p.target_column_name.lower().replace("_", "") == target_normalized
            ]
        
        # Filter by confidence
        patterns = [p for p in patterns if p.confidence >= min_confidence]
        
        # Sort by success count
        patterns.sort(key=lambda x: x.success_count, reverse=True)
        
        return patterns
    
    def suggest_function(
        self,
        column_name: str,
        semantic_type: Optional[str] = None,
        sample_values: Optional[List[str]] = None,
        target_column: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest a transformation function based on learned patterns.
        
        Returns:
            Dict with 'function', 'params', 'confidence' or None
        """
        patterns = self.find_patterns(
            column_name, semantic_type, sample_values, target_column
        )
        
        if patterns:
            best = patterns[0]
            return {
                "function": best.function_used,
                "params": best.params_used,
                "confidence": best.confidence,
                "based_on": f"{best.success_count} successful uses",
            }
        
        return None
    
    def record_success(
        self,
        source_column_name: str,
        source_semantic_type: str,
        target_column_name: str,
        function_used: str,
        params_used: Dict[str, Any],
        sample_values: Optional[List[str]] = None,
    ):
        """
        Record a successful transformation for learning.
        
        Args:
            source_column_name: Source column name
            source_semantic_type: Semantic type
            target_column_name: Target column name
            function_used: Function that was used
            params_used: Parameters that were used
            sample_values: Sample values from source
        """
        signature = self.create_signature(
            source_column_name, source_semantic_type, sample_values
        )
        
        # Check if pattern exists
        existing_ids = self._index_by_source.get(signature, [])
        for pid in existing_ids:
            pattern = self._patterns.get(pid)
            if pattern and pattern.function_used == function_used and pattern.target_column_name == target_column_name:
                # Update existing pattern
                pattern.success_count += 1
                pattern.last_used = datetime.now().isoformat()
                pattern.confidence = min(1.0, pattern.success_count / 10)  # Max confidence at 10 uses
                self._save()
                return
        
        # Create new pattern
        pattern_id = f"pat_{signature}_{len(self._patterns)}"
        pattern = TransformationPattern(
            pattern_id=pattern_id,
            source_signature=signature,
            source_column_name=source_column_name,
            source_semantic_type=source_semantic_type or "",
            target_column_name=target_column_name,
            function_used=function_used,
            params_used=params_used,
            success_count=1,
            last_used=datetime.now().isoformat(),
            confidence=0.1,
        )
        
        self._patterns[pattern_id] = pattern
        self._update_indices(pattern)
        self._save()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics."""
        if not self._patterns:
            return {"total_patterns": 0, "functions_used": {}, "top_patterns": []}
        
        function_counts = {}
        for pattern in self._patterns.values():
            func = pattern.function_used
            function_counts[func] = function_counts.get(func, 0) + 1
        
        top_patterns = sorted(
            self._patterns.values(),
            key=lambda x: x.success_count,
            reverse=True
        )[:5]
        
        return {
            "total_patterns": len(self._patterns),
            "functions_used": function_counts,
            "top_patterns": [
                {
                    "source": p.source_column_name,
                    "target": p.target_column_name,
                    "function": p.function_used,
                    "uses": p.success_count,
                }
                for p in top_patterns
            ]
        }


# Global library instance
_library: Optional[GlobalLibrary] = None


def get_global_library() -> GlobalLibrary:
    """Get or create the global library instance."""
    global _library
    if _library is None:
        _library = GlobalLibrary()
    return _library
