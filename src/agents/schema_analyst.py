"""
Schema Analyst Agent - The "Data Detective"
Analyzes source files to infer structure, types, and issues.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import re

from .base_agent import BaseAgent
from ..schemas.source_schema import SourceSchemaAnalysis, ColumnAnalysis, StructuralIssue
from ..utils.excel_loader import ExcelLoader


class SchemaAnalystAgent(BaseAgent):
    """
    Analyzes source Excel/CSV files to understand their structure.
    
    Responsibilities:
    - Infer data types (int, float, date, string)
    - Infer semantic types (phone, email, name, address, GSTIN)
    - Identify structural issues (merged cells, multi-row headers)
    - Generate sample data for the Planner Agent
    """
    
    @property
    def name(self) -> str:
        return "Schema Analyst"
    
    @property
    def system_prompt(self) -> str:
        return """You are a Data Inspector Agent. Your job is to analyze sample data from Excel/CSV files and produce a structured analysis.

TASK: Analyze the provided sample data and return a JSON object with your findings.

For each column, determine:
1. **inferred_type**: The data type - one of: "string", "integer", "float", "date", "boolean", "mixed", "empty"
2. **semantic_type**: What the data represents - one of: "name", "first_name", "last_name", "full_name", "email", "phone", "address", "city", "state", "pincode", "country", "gstin", "pan", "date", "currency", "id", "quantity", "description", "unknown"
3. **issues**: Any problems detected like "mixed formats", "inconsistent types", "special characters"
4. **suggested_functions**: Functions from the registry that might help transform this column:
   - SPLIT_FULL_NAME (for full names)
   - NORMALIZE_PHONE (for phone numbers)
   - SMART_DATE_PARSE (for dates)
   - VALIDATE_EMAIL (for emails)
   - VALIDATE_GSTIN (for GSTIN)
   - CLEAN_WHITESPACE (for dirty text)
   - MAP_VALUES (for categorical data)

OUTPUT: Return ONLY valid JSON matching this structure:
{
  "columns": [
    {
      "column_name": "string",
      "inferred_type": "string",
      "semantic_type": "string or null",
      "issues": ["list of issues"],
      "suggested_functions": ["list of function names"]
    }
  ],
  "structural_issues": [
    {
      "issue_type": "merged_cells|multi_row_header|empty_rows|inconsistent_types",
      "description": "string",
      "severity": "critical|warning|info"
    }
  ],
  "overall_quality": "good|fair|poor",
  "preprocessing_steps": ["list of recommended steps"]
}

Do not include any text outside the JSON object."""
    
    def run(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        sample_rows: int = 50,
    ) -> SourceSchemaAnalysis:
        """
        Analyze a source file.
        
        Args:
            file_path: Path to the Excel/CSV file
            sheet_name: Sheet name (Excel only)
            sample_rows: Number of rows to sample
            
        Returns:
            SourceSchemaAnalysis with findings
        """
        # Load sample data
        loader = ExcelLoader(file_path)
        sample_df = loader.load_sample(n_rows=sample_rows, sheet_name=sheet_name)
        
        # Get basic analysis from local methods
        local_analysis = self._local_analysis(sample_df, loader)
        
        # Get AI-enhanced analysis
        ai_analysis = self._ai_analysis(sample_df, loader)
        
        # Merge analyses
        return self._merge_analyses(local_analysis, ai_analysis, loader)
    
    def _local_analysis(
        self,
        df: pd.DataFrame,
        loader: ExcelLoader
    ) -> Dict[str, Any]:
        """
        Perform local (non-AI) analysis for basic statistics.
        """
        columns = []
        samples = loader.get_column_samples(n_samples=5)
        stats = loader.get_column_stats()
        
        for idx, col in enumerate(df.columns):
            col_data = df[col]
            
            # Infer basic type
            inferred_type = self._infer_type(col_data)
            
            # Get completeness
            completeness = stats.get(col, {}).get('completeness', 0.0)
            
            columns.append(ColumnAnalysis(
                column_name=str(col),
                column_index=idx,
                inferred_type=inferred_type,
                total_values=len(col_data),
                null_count=col_data.isna().sum(),
                unique_count=col_data.nunique(),
                completeness=completeness,
                sample_values=samples.get(col, []),
            ))
        
        return {
            "columns": columns,
            "total_rows": len(df),
            "total_columns": len(df.columns),
        }
    
    def _infer_type(self, series: pd.Series) -> str:
        """Infer the data type of a pandas Series."""
        non_null = series.dropna()
        if len(non_null) == 0:
            return "empty"
        
        # Try numeric
        try:
            numeric = pd.to_numeric(non_null, errors='coerce')
            if numeric.notna().sum() > len(non_null) * 0.8:
                valid_numeric = numeric.dropna()
                # Check if all represent integers
                if (valid_numeric % 1 == 0).all():
                    return "integer"
                return "float"
        except:
            pass
        
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, message=".*Could not infer format.*")
                dates = pd.to_datetime(non_null, errors='coerce')
            if dates.notna().sum() > len(non_null) * 0.5:
                return "date"
        except:
            pass
        
        # Check for boolean
        bool_values = {'true', 'false', 'yes', 'no', '1', '0', 'y', 'n'}
        if all(str(v).lower().strip() in bool_values for v in non_null):
            return "boolean"
        
        return "string"
    
    def _ai_analysis(
        self,
        df: pd.DataFrame,
        loader: ExcelLoader
    ) -> Dict[str, Any]:
        """
        Get AI-enhanced semantic analysis.
        """
        # Prepare data for prompt
        csv_sample = loader.to_csv_string(df, max_rows=20)
        column_info = []
        samples = loader.get_column_samples(n_samples=5)
        
        for col in df.columns:
            column_info.append({
                "name": str(col),
                "samples": samples.get(col, [])
            })
        
        prompt = f"""Analyze this data sample and provide your findings as JSON.

COLUMN INFORMATION:
{self._format_data_for_prompt(column_info)}

DATA SAMPLE (CSV format):
```csv
{csv_sample}
```

Analyze each column and return your findings as specified in your instructions."""
        
        try:
            result = self._call_api_json(prompt)
            return result
        except Exception as e:
            # Return empty if AI fails
            return {"columns": [], "structural_issues": [], "overall_quality": "fair"}
    
    def _merge_analyses(
        self,
        local: Dict[str, Any],
        ai: Dict[str, Any],
        loader: ExcelLoader
    ) -> SourceSchemaAnalysis:
        """
        Merge local and AI analyses into final result.
        """
        columns = local.get("columns", [])
        ai_columns = {c.get("column_name", ""): c for c in ai.get("columns", [])}
        
        # Enhance local columns with AI insights
        for col in columns:
            ai_col = ai_columns.get(col.column_name, {})
            
            # Use AI semantic type if available
            if ai_col.get("semantic_type"):
                col.semantic_type = ai_col["semantic_type"]
            
            # Add AI-detected issues
            col.issues = ai_col.get("issues", [])
            
            # Add suggested functions
            col.suggested_functions = ai_col.get("suggested_functions", [])
        
        # Parse structural issues
        structural_issues = []
        for issue in ai.get("structural_issues", []):
            try:
                structural_issues.append(StructuralIssue(
                    issue_type=issue.get("issue_type", "inconsistent_types"),
                    description=issue.get("description", ""),
                    severity=issue.get("severity", "warning")
                ))
            except:
                pass
        
        return SourceSchemaAnalysis(
            file_name=loader.file_path.name,
            total_rows=local.get("total_rows", 0),
            total_columns=local.get("total_columns", 0),
            sample_rows_analyzed=min(50, local.get("total_rows", 0)),
            columns=columns,
            structural_issues=structural_issues,
            encoding=loader.encoding,
            overall_quality=ai.get("overall_quality", "fair"),
            preprocessing_steps=ai.get("preprocessing_steps", []),
        )
