"""
Execution Engine - The deterministic executor of transformation plans.
This is NOT an LLM - it runs strictly defined functions from the registry.
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from ..schemas.transformation_plan import TransformationPlan, Transformation, ColumnMapping, Enrichment
from ..schemas.validation_report import ValidationReport, ValidationError
from .function_registry import get_registry, FunctionRegistry


class ExecutionEngine:
    """
    Executes transformation plans on DataFrames.
    Takes a JSON plan and applies all transformations deterministically.
    """
    
    def __init__(self, registry: Optional[FunctionRegistry] = None):
        """Initialize with a function registry."""
        self.registry = registry or get_registry()
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []
    
    def execute(
        self,
        df: pd.DataFrame,
        plan: TransformationPlan,
    ) -> Tuple[pd.DataFrame, List[ValidationError]]:
        """
        Execute a transformation plan on a DataFrame.
        
        Args:
            df: Source DataFrame
            plan: TransformationPlan to execute
            
        Returns:
            Tuple of (transformed DataFrame, list of errors)
        """
        self.errors = []
        self.warnings = []
        
        # Create a copy to avoid modifying original
        result_df = df.copy()
        
        # Step 1: Apply all transformations
        result_df = self._apply_transformations(result_df, plan)
        
        # Step 2: Apply enrichments
        result_df = self._apply_enrichments(result_df, plan)
        
        # Step 3: Apply column mappings (create target columns)
        result_df = self._apply_column_mappings(result_df, plan)
        
        return result_df, self.errors
    
    def _apply_transformations(
        self,
        df: pd.DataFrame,
        plan: TransformationPlan
    ) -> pd.DataFrame:
        """Apply all transformation steps."""
        for transform in plan.transformations:
            try:
                df = self._apply_single_transformation(df, transform)
            except Exception as e:
                self.warnings.append(f"Transformation {transform.id} failed: {str(e)}")
        return df
    
    def _apply_single_transformation(
        self,
        df: pd.DataFrame,
        transform: Transformation
    ) -> pd.DataFrame:
        """Apply a single transformation."""
        func_name = transform.function
        params = transform.params.model_dump(exclude_none=True)
        
        # Handle different input/output patterns
        if transform.input_col and transform.input_col in df.columns:
            input_col = transform.input_col
            
            # Functions that return dictionaries (split to multiple columns)
            if func_name in ["SPLIT_FULL_NAME", "VALIDATE_GSTIN", "VALIDATE_EMAIL", "LOOKUP_PINCODE"]:
                results = df[input_col].apply(
                    lambda x: self.registry.execute(func_name, x, params)
                )
                
                # Expand dictionary results to columns
                if transform.output_cols:
                    for col in transform.output_cols:
                        df[col] = results.apply(lambda x: x.get(col, "") if isinstance(x, dict) else "")
                elif transform.output_col:
                    # If single output col specified, use first value
                    df[transform.output_col] = results.apply(
                        lambda x: list(x.values())[0] if isinstance(x, dict) else x
                    )
            else:
                # Functions that return single values
                output_col = transform.output_col or input_col
                
                # For conditional fill, we need to pass the row
                if func_name == "CONDITIONAL_FILL":
                    df[output_col] = df.apply(
                        lambda row: self.registry.execute(
                            func_name, 
                            row[input_col], 
                            params,
                            row=row
                        ),
                        axis=1
                    )
                else:
                    df[output_col] = df[input_col].apply(
                        lambda x: self.registry.execute(func_name, x, params)
                    )
        
        
        elif transform.input_cols:
            # Multiple input columns (e.g., CONCATENATE, COMPUTE_DATE_DIFF)
            if transform.output_col:
                df[transform.output_col] = df.apply(
                    lambda row: self.registry.execute(
                        func_name,
                        None,  # 'value' is None for multi-col, data passed in 'values' or 'row'
                        params,
                        values=[row[c] for c in transform.input_cols if c in row],
                        row=row  # Some functions might need the full row
                    ),
                    axis=1
                )
        
        return df
    
    def _apply_enrichments(
        self,
        df: pd.DataFrame,
        plan: TransformationPlan
    ) -> pd.DataFrame:
        """Apply all enrichment steps."""
        for enrichment in plan.enrichments:
            try:
                df = self._apply_single_enrichment(df, enrichment)
            except Exception as e:
                self.warnings.append(f"Enrichment {enrichment.id} failed: {str(e)}")
        return df
    
    def _apply_single_enrichment(
        self,
        df: pd.DataFrame,
        enrichment: Enrichment
    ) -> pd.DataFrame:
        """Apply a single enrichment step."""
        trigger_col = enrichment.trigger_col
        
        if trigger_col not in df.columns:
            return df
        
        # Map API service to registry function
        func_map = {
            "postal_code_lookup": "LOOKUP_PINCODE",
            "pincode_lookup": "LOOKUP_PINCODE",
        }
        
        func_name = func_map.get(enrichment.api_service, enrichment.api_service.upper())
        params = enrichment.params.model_dump(exclude_none=True)
        
        # Apply enrichment
        results = df[trigger_col].apply(
            lambda x: self.registry.execute(func_name, x, params)
        )
        
        # Expand results to target columns
        for col in enrichment.target_cols:
            col_lower = col.lower()
            df[col] = results.apply(
                lambda x: x.get(col_lower, x.get(col, "")) if isinstance(x, dict) else ""
            )
        
        return df
    
    def _apply_column_mappings(
        self,
        df: pd.DataFrame,
        plan: TransformationPlan
    ) -> pd.DataFrame:
        """Apply column mappings to create final target columns."""
        target_df = pd.DataFrame()
        
        for mapping in plan.column_mappings:
            if mapping.action == "skip":
                continue
            
            source_col = mapping.source_col
            target_col = mapping.target_col
            
            if mapping.action == "direct":
                if source_col in df.columns:
                    target_df[target_col] = df[source_col]
                elif target_col in df.columns:
                    # Already created by transformation
                    target_df[target_col] = df[target_col]
            
            elif mapping.action == "transform":
                # The transformation should have already created the target column
                if target_col in df.columns:
                    target_df[target_col] = df[target_col]
                elif source_col in df.columns:
                    # Fallback to direct copy if transformation didn't create it
                    target_df[target_col] = df[source_col]
        
        # Also include any columns created by enrichments that aren't in mappings
        mapping_targets = {m.target_col for m in plan.column_mappings}
        for col in df.columns:
            if col not in mapping_targets and col not in target_df.columns:
                # Check if it's a target column created by enrichment
                for enrichment in plan.enrichments:
                    if col in enrichment.target_cols:
                        target_df[col] = df[col]
                        break
        
        return target_df if not target_df.empty else df


def execute_plan(
    df: pd.DataFrame,
    plan: TransformationPlan,
    registry: Optional[FunctionRegistry] = None
) -> Tuple[pd.DataFrame, List[ValidationError]]:
    """
    Convenience function to execute a transformation plan.
    
    Args:
        df: Source DataFrame
        plan: TransformationPlan to execute
        registry: Optional custom function registry
        
    Returns:
        Tuple of (transformed DataFrame, list of errors)
    """
    engine = ExecutionEngine(registry)
    return engine.execute(df, plan)
