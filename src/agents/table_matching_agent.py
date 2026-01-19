"""
Table Matching Agent - Matches detected tables to target schemas.
Scores similarity and identifies the best table for transformation.
"""

from typing import Dict, Any, List, Optional, Tuple
import re
from difflib import SequenceMatcher

from .base_agent import BaseAgent
from ..schemas.detected_table import (
    DetectedTable,
    TableMatch,
    TableMatchingResult,
)
from ..schemas.target_schema import TargetSchema, GENERIC_CUSTOMER_SCHEMA


class TableMatchingAgent(BaseAgent):
    """
    Matches detected tables against target schema requirements.
    
    Responsibilities:
    - Score each detected table against target schema
    - Match columns by name similarity and semantic type
    - Identify best matching table
    - Handle ambiguous cases (multiple good matches)
    """
    
    # Similarity thresholds
    HIGH_MATCH_THRESHOLD = 0.7
    MODERATE_MATCH_THRESHOLD = 0.4
    
    @property
    def name(self) -> str:
        return "Table Matching Agent"
    
    @property
    def system_prompt(self) -> str:
        return """You are a Schema Matching Agent. Your job is to match source table columns to target schema columns.

TASK: Given source columns and target schema, determine the best mapping.

Consider:
1. Column name similarity (exact match, partial match, abbreviations)
2. Semantic type matching (email→email, phone→phone_number)
3. Data type compatibility (string→string, number→number)
4. Sample values analysis

OUTPUT: Return ONLY valid JSON:
{
  "matched_columns": [
    {"source": "CustomerName", "target": "first_name", "confidence": 0.85, "reason": "name semantic match"}
  ],
  "unmatched_source": ["InternalID"],
  "unmatched_target": ["middle_name"],
  "match_score": 0.78,
  "notes": "Strong match on contact fields"
}"""
    
    def run(
        self,
        detected_tables: List[DetectedTable],
        target_schema: Optional[TargetSchema] = None,
    ) -> TableMatchingResult:
        """
        Match detected tables against target schema.
        
        Args:
            detected_tables: List of tables detected in the file
            target_schema: Target schema to match against
            
        Returns:
            TableMatchingResult with matches for each table
        """
        target_schema = target_schema or GENERIC_CUSTOMER_SCHEMA
        
        matches = []
        
        for table in detected_tables:
            match = self._match_table_to_schema(table, target_schema)
            matches.append(match)
        
        # Sort by match score descending
        matches.sort(key=lambda m: m.match_score, reverse=True)
        
        # Determine if user selection is needed
        good_matches = [m for m in matches if m.match_score >= self.HIGH_MATCH_THRESHOLD]
        best_match_id = matches[0].table_id if matches else None
        
        requires_selection = len(good_matches) > 1
        user_prompt = None
        
        if requires_selection:
            user_prompt = self._generate_selection_prompt(good_matches, detected_tables)
        
        return TableMatchingResult(
            target_schema_name=target_schema.name,
            matches=matches,
            best_match_table_id=best_match_id,
            requires_user_selection=requires_selection,
            user_prompt=user_prompt,
        )
    
    def _match_table_to_schema(
        self,
        table: DetectedTable,
        target_schema: TargetSchema
    ) -> TableMatch:
        """Match a single table to the target schema."""
        matched_columns: List[Tuple[str, str]] = []
        unmatched_source: List[str] = []
        source_matched_set = set()
        
        # Get target column info
        target_cols = {col.name: col for col in target_schema.columns}
        target_matched_set = set()
        
        # First pass: Try exact and close name matching
        for source_col in table.column_names:
            best_match = None
            best_score = 0.0
            
            for target_col_name, target_col in target_cols.items():
                if target_col_name in target_matched_set:
                    continue
                
                score = self._calculate_column_match_score(
                    source_col,
                    target_col_name,
                    target_col.common_source_names,
                    target_col.data_type,
                    table.sample_values.get(source_col, []),
                )
                
                if score > best_score:
                    best_score = score
                    best_match = target_col_name
            
            if best_match and best_score >= self.MODERATE_MATCH_THRESHOLD:
                matched_columns.append((source_col, best_match))
                source_matched_set.add(source_col)
                target_matched_set.add(best_match)
        
        # Identify unmatched columns
        for source_col in table.column_names:
            if source_col not in source_matched_set:
                unmatched_source.append(source_col)
        
        unmatched_target = [
            col.name for col in target_schema.columns 
            if col.name not in target_matched_set and col.required
        ]
        
        # Calculate overall match score
        total_target = len(target_schema.columns)
        matched_count = len(matched_columns)
        required_matched = len([
            col for col in target_schema.columns 
            if col.required and col.name in target_matched_set
        ])
        required_total = len(target_schema.required_columns)
        
        # Weighted score: required columns matter more
        required_weight = 0.6
        optional_weight = 0.4
        
        required_score = required_matched / required_total if required_total > 0 else 1.0
        optional_matched_count = matched_count - required_matched
        optional_total = total_target - required_total
        optional_score = optional_matched_count / optional_total if optional_total > 0 else 1.0
        
        match_score = (required_weight * required_score) + (optional_weight * optional_score)
        
        return TableMatch(
            table_id=table.table_id,
            target_schema_name=target_schema.name,
            match_score=match_score,
            matched_columns=matched_columns,
            unmatched_source_cols=unmatched_source,
            unmatched_target_cols=unmatched_target,
        )
    
    def _calculate_column_match_score(
        self,
        source_col: str,
        target_col: str,
        common_source_names: List[str],
        target_type: str,
        sample_values: List[str],
    ) -> float:
        """Calculate match score between source and target column."""
        score = 0.0
        
        # Normalize names for comparison
        source_norm = self._normalize_column_name(source_col)
        target_norm = self._normalize_column_name(target_col)
        
        # 1. Exact match (after normalization)
        if source_norm == target_norm:
            score = 1.0
            return score
        
        # 2. Check against common source names
        for common_name in common_source_names:
            common_norm = self._normalize_column_name(common_name)
            if source_norm == common_norm:
                score = 0.95
                return score
            # Partial match
            if common_norm in source_norm or source_norm in common_norm:
                score = max(score, 0.8)
        
        # 3. String similarity (Levenshtein-based)
        similarity = SequenceMatcher(None, source_norm, target_norm).ratio()
        score = max(score, similarity * 0.9)
        
        # 4. Semantic type matching based on sample values
        if sample_values:
            inferred_type = self._infer_semantic_type(sample_values)
            if inferred_type == target_type:
                score = max(score, 0.7)
            elif self._types_compatible(inferred_type, target_type):
                score = max(score, 0.5)
        
        # 5. Keyword matching
        source_keywords = set(self._extract_keywords(source_col))
        target_keywords = set(self._extract_keywords(target_col))
        
        if source_keywords & target_keywords:
            keyword_overlap = len(source_keywords & target_keywords) / max(len(source_keywords), len(target_keywords))
            score = max(score, 0.6 * keyword_overlap + 0.3)
        
        return score
    
    def _normalize_column_name(self, name: str) -> str:
        """Normalize column name for comparison."""
        # Lowercase
        name = name.lower()
        # Remove special characters
        name = re.sub(r'[^a-z0-9]', '', name)
        return name
    
    def _extract_keywords(self, name: str) -> List[str]:
        """Extract keywords from column name."""
        # Split by common separators
        words = re.split(r'[_\s\-\.]+', name.lower())
        # Also split camelCase
        words = sum([re.sub('([A-Z])', r' \1', w).split() for w in words], [])
        # Remove empty strings and short words
        return [w.lower() for w in words if len(w) > 1]
    
    def _infer_semantic_type(self, sample_values: List[str]) -> str:
        """Infer semantic type from sample values."""
        if not sample_values:
            return "string"
        
        # Check patterns
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        phone_pattern = r'^[\+\d\s\-\(\)]{8,}$'
        date_pattern = r'\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}'
        
        email_count = sum(1 for v in sample_values if re.match(email_pattern, str(v)))
        phone_count = sum(1 for v in sample_values if re.match(phone_pattern, re.sub(r'\s', '', str(v))))
        date_count = sum(1 for v in sample_values if re.search(date_pattern, str(v)))
        
        n = len(sample_values)
        threshold = 0.5
        
        if email_count / n >= threshold:
            return "email"
        if phone_count / n >= threshold:
            return "phone"
        if date_count / n >= threshold:
            return "date"
        
        # Check if numeric
        numeric_count = 0
        for v in sample_values:
            try:
                float(str(v).replace(',', '').replace('$', '').replace('₹', ''))
                numeric_count += 1
            except:
                pass
        
        if numeric_count / n >= threshold:
            return "float" if any('.' in str(v) for v in sample_values) else "integer"
        
        return "string"
    
    def _types_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if two types are compatible."""
        compatible_groups = [
            {"string", "name", "first_name", "last_name", "full_name", "address", "city", "state", "country"},
            {"integer", "float", "number", "currency", "quantity"},
            {"phone", "phone_number", "mobile"},
            {"email", "email_address"},
            {"date", "datetime", "timestamp"},
        ]
        
        for group in compatible_groups:
            if source_type in group and target_type in group:
                return True
        
        return False
    
    def _generate_selection_prompt(
        self,
        good_matches: List[TableMatch],
        detected_tables: List[DetectedTable]
    ) -> str:
        """Generate a prompt for user to select among multiple matching tables."""
        lines = ["Multiple tables match the target schema. Please select one:"]
        lines.append("")
        
        table_map = {t.table_id: t for t in detected_tables}
        
        for idx, match in enumerate(good_matches, 1):
            table = table_map.get(match.table_id)
            if table:
                title = table.title or f"Table at row {table.boundary.start_row + 1}"
                cols = ", ".join(table.column_names[:4])
                if len(table.column_names) > 4:
                    cols += f" (+{len(table.column_names) - 4} more)"
                
                lines.append(f"{idx}. {title}")
                lines.append(f"   Columns: {cols}")
                lines.append(f"   Rows: {table.row_count}")
                lines.append(f"   Match Score: {match.match_score:.0%}")
                lines.append("")
        
        lines.append("Enter the number of the table you want to transform:")
        
        return "\n".join(lines)
