"""
Transformation Planner Agent - The "Architect"
Generates JSON transformation plans to map source to target schemas.
"""

from typing import Dict, Any, List, Optional
import json

from .base_agent import BaseAgent
from ..schemas.source_schema import SourceSchemaAnalysis
from ..schemas.target_schema import TargetSchema, GENERIC_CUSTOMER_SCHEMA
from ..schemas.transformation_plan import (
    TransformationPlan,
    ColumnMapping,
    Transformation,
    Enrichment,
    TransformationParams,
    EnrichmentParams,
)
from ..engine.function_registry import FunctionRegistry, get_registry


class TransformationPlannerAgent(BaseAgent):
    """
    Creates transformation plans to convert source data to target schemas.
    
    Responsibilities:
    - Map source columns to target columns
    - Select appropriate transformation functions
    - Configure enrichment steps
    - Handle ambiguities by asking user questions
    """
    
    @property
    def name(self) -> str:
        return "Transformation Planner"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert Data Engineer Agent. Your goal is to create a transformation plan that maps source columns to target columns.

FUNCTION REGISTRY (available functions):
- SPLIT_FULL_NAME: Split full name into first/middle/last. Params: delimiter (auto|space|comma), culture (western|eastern), handle_single_name (first_name_only|last_name_only)
- REGEX_EXTRACT: Extract via regex. Params: pattern (regex string), group_index (int)
- CLEAN_WHITESPACE: Remove extra spaces. No params.
- SMART_DATE_PARSE: Parse dates. Params: ambiguity_preference (US|UK|ISO)
- FORMAT_DATE: Format dates. Params: target_format (strftime format)
- NORMALIZE_CURRENCY: Clean currency values. Params: currency_symbol (optional)
- MAP_VALUES: Map categories. Params: mapping_dict (object), default (string)
- CONDITIONAL_FILL: Fill empty with fallback. Params: fallback_col (string)
- NORMALIZE_PHONE: Normalize phone numbers. Params: region (IN|US|etc), format (E.164|NATIONAL|INTERNATIONAL)
- VALIDATE_EMAIL: Validate email format. No params (validation only).
- VALIDATE_GSTIN: Validate Indian GSTIN. No params (validation only).
- LOOKUP_PINCODE: Enrich pincode to city/state. Params: provider (optional)
- UPPERCASE, LOWERCASE, TITLECASE: Case conversion. No params.
- CONCATENATE: Join columns. Params: separator (string). Use input_cols for multiple columns.
- COMPUTE_DATE_DIFF: Difference in days (date1 - date2). Params: date2_col (string) OR use input_cols=[date1, date2].

RULES:
1. PREFER PREBUILT: Always use registry functions. Only mark "requires_user_input" for truly ambiguous cases.
2. BE EXPLICIT: For REGEX_EXTRACT, write the actual regex pattern.
3. DATA ENRICHMENT: If target needs City/State and source has Pincode, add enrichment.
4. COMPUTED COLUMNS: Check 'transformation_hint' in target schema.
   - For 'CONCATENATE', use action="transform", function="CONCATENATE", and input_cols=[col1, col2...].
   - For 'COMPUTE', use action="transform", function="COMPUTE_DATE_DIFF", input_cols=[date1, date2].
5. COLUMN MATCHING: Match columns by name similarity AND semantic type.
5. CONFIDENCE: Set confidence_score based on match quality (0.0-1.0).

OUTPUT: Return ONLY valid JSON with this structure:
{
  "transformation_id": "uuid",
  "confidence_score": 0.95,
  "column_mappings": [
    {"source_col": "Name", "target_col": "first_name", "action": "transform", "transform_id": "tf_01"}
  ],
  "transformations": [
    {"id": "tf_01", "function": "SPLIT_FULL_NAME", "input_col": "Name", "output_cols": ["first_name", "last_name"], "params": {"delimiter": "auto"}}
  ],
  "enrichments": [
    {"id": "en_01", "trigger_col": "Pincode", "target_cols": ["city", "state"], "api_service": "postal_code_lookup", "strategy": "cache_first_then_api"}
  ],
  "unmapped_source_cols": ["Column_X"],
  "unmapped_target_cols": ["middle_name"],
  "warnings": ["Phone numbers have mixed formats"],
  "requires_user_input": false,
  "user_questions": []
}

Do not include markdown or text outside the JSON."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry = get_registry()
    
    def run(
        self,
        source_schema: SourceSchemaAnalysis,
        target_schema: Optional[TargetSchema] = None,
    ) -> TransformationPlan:
        """
        Generate a transformation plan.
        
        Args:
            source_schema: Analysis of the source file
            target_schema: Target schema to transform to (defaults to generic customer)
            
        Returns:
            TransformationPlan with mappings and transformations
        """
        target_schema = target_schema or GENERIC_CUSTOMER_SCHEMA
        
        # Prepare context for AI
        source_info = self._format_source_schema(source_schema)
        target_info = self._format_target_schema(target_schema)
        
        prompt = f"""Create a transformation plan to convert the source data to the target schema.

SOURCE SCHEMA ANALYSIS:
{source_info}

TARGET SCHEMA:
{target_info}

CRITICAL INSTRUCTIONS:
1. Look for 'transformation_hint' in the TARGET SCHEMA columns.
2. If a hint exists (e.g., CONCATENATE, COMPUTE), you MUST create a 'transformations' entry for it.
3. Do not just map columns directly if a transformation is required.
4. For computed columns, set action="transform" in column_mappings.

Generate the transformation plan as JSON."""

        # DEBUG: Save prompt to file
        with open("debug_prompt.txt", "w", encoding="utf-8") as f:
            f.write(self.system_prompt + "\n\n" + prompt)
        
        try:
            result = self._call_api_json(prompt)
            return self._parse_plan(result)
        except Exception as e:
            # Return a basic direct mapping plan on failure
            return self._create_fallback_plan(source_schema, target_schema)
    
    def _format_source_schema(self, schema: SourceSchemaAnalysis) -> str:
        """Format source schema for the prompt."""
        columns_info = []
        for col in schema.columns:
            columns_info.append({
                "name": col.column_name,
                "type": col.inferred_type,
                "semantic": col.semantic_type,
                "samples": col.sample_values[:3],
                "completeness": f"{col.completeness:.0%}",
                "suggested_functions": col.suggested_functions,
            })
        
        return json.dumps({
            "file_name": schema.file_name,
            "total_rows": schema.total_rows,
            "columns": columns_info,
            "issues": [{"type": i.issue_type, "desc": i.description} for i in schema.structural_issues],
        }, indent=2)
    
    def _format_target_schema(self, schema: TargetSchema) -> str:
        """Format target schema for the prompt."""
        columns_info = []
        for col in schema.columns:
            columns_info.append({
                "name": col.name,
                "type": col.data_type,
                "required": col.required,
                "pattern": col.pattern,
                "common_names": col.common_source_names[:5],
                "transformation_hint": col.transformation_hint,
            })
        
        return json.dumps({
            "name": schema.name,
            "columns": columns_info,
            "required_columns": schema.required_columns,
        }, indent=2)
    
    def _parse_plan(self, result: Dict[str, Any]) -> TransformationPlan:
        """Parse AI response into TransformationPlan."""
        # Parse column mappings
        mappings = []
        for m in result.get("column_mappings", []):
            mappings.append(ColumnMapping(
                source_col=m.get("source_col", ""),
                target_col=m.get("target_col", ""),
                action=m.get("action", "direct"),
                transform_id=m.get("transform_id"),
            ))
        
        # Parse transformations
        transformations = []
        for t in result.get("transformations", []):
            params = TransformationParams(**t.get("params", {}))
            transformations.append(Transformation(
                id=t.get("id", ""),
                function=t.get("function", ""),
                input_col=t.get("input_col"),
                input_cols=t.get("input_cols"),
                output_col=t.get("output_col"),
                output_cols=t.get("output_cols"),
                params=params,
            ))
        
        # Parse enrichments
        enrichments = []
        for e in result.get("enrichments", []):
            enrichments.append(Enrichment(
                id=e.get("id", ""),
                trigger_col=e.get("trigger_col", ""),
                target_cols=e.get("target_cols", []),
                api_service=e.get("api_service", ""),
                strategy=e.get("strategy", "cache_first_then_api"),
            ))
        
        return TransformationPlan(
            transformation_id=result.get("transformation_id", ""),
            confidence_score=result.get("confidence_score", 0.5),
            column_mappings=mappings,
            transformations=transformations,
            enrichments=enrichments,
            unmapped_source_cols=result.get("unmapped_source_cols", []),
            unmapped_target_cols=result.get("unmapped_target_cols", []),
            warnings=result.get("warnings", []),
            requires_user_input=result.get("requires_user_input", False),
            user_questions=result.get("user_questions", []),
        )
    
    def _create_fallback_plan(
        self,
        source_schema: SourceSchemaAnalysis,
        target_schema: TargetSchema
    ) -> TransformationPlan:
        """Create a basic plan when AI fails."""
        mappings = []
        
        # Simple name matching
        for source_col in source_schema.columns:
            for target_col in target_schema.columns:
                # Check if names match
                source_name = source_col.column_name.lower().replace("_", "").replace(" ", "")
                target_name = target_col.name.lower().replace("_", "")
                
                if source_name == target_name or source_name in [n.lower().replace("_", "") for n in target_col.common_source_names]:
                    mappings.append(ColumnMapping(
                        source_col=source_col.column_name,
                        target_col=target_col.name,
                        action="direct",
                    ))
                    break
        
        return TransformationPlan(
            confidence_score=0.3,
            column_mappings=mappings,
            warnings=["AI planning failed - using basic name matching"],
        )
