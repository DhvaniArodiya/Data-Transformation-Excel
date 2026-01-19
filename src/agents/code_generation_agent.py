"""
Code Generation Agent - The "Fallback Engineer"
Generates standalone Python scripts when the standard pipeline isn't enough.
"""

from typing import Optional
from .base_agent import BaseAgent
from ..schemas.source_schema import SourceSchemaAnalysis
from ..schemas.target_schema import TargetSchema

class CodeGenerationAgent(BaseAgent):
    """
    Generates specific Python code to transform data.
    Used as valid "Plan B" when the main pipeline (Planner -> ExecutionEngine) 
    has low confidence or fails.
    """
    
    @property
    def name(self) -> str:
        return "Code Generator"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert Python Data Engineer. Your task is to write a complete, standalone Python script to transform an Excel file.
        
        REQUIREMENTS:
        1. Use 'pandas' for data manipulation.
        2. Use 'sys.argv' or hardcoded paths as instructed.
        3. The script must be complete, runnable, and error-free.
        4. Handle edge cases (missing columns, nulls) gracefully.
        5. Output the result to 'output/' directory. If the input is XML or the user asks for JSON, use '.json' format. Otherwise default to '.xlsx'.
        6. PRINT CLEAR LOGS to stdout so the user knows what's happening.

        **PREBUILT LIBRARY AVAILABILITY:**
        You have access to a local library `src.utils.transformations` with ready-to-use functions. 
        PREFER using these over writing your own regex/logic where possible.
        
        Run this setup code at the top of your script to enable imports:
        ```python
        import sys
        from pathlib import Path
        # Add project root to sys.path (assuming script runs in 'output/' or root)
        sys.path.append(str(Path(__file__).resolve().parent.parent)) 
        
        try:
            from src.utils.transformations import (
                split_name, merge_name, to_uppercase, to_titlecase, 
                parse_date, calculate_age, days_between, 
                to_float, round_number, normalize_phone, validate_email
            )
        except ImportError:
            # Fallback if running from a different location
            pass
        ```

        **Available Functions:**
        - Strings: split_name(full_name), to_uppercase(text), to_titlecase(text), remove_special_chars(text)
        - Dates: parse_date(val), calculate_age(dob), days_between(d1, d2)
        - Numbers: to_float(val), round_number(val, decimals)
        - Contact: normalize_phone(phone), validate_email(email)

        OUTPUT FORMAT:
        Return ONLY the Python code block. No markdown fencing (```python) or explanations outside the code.
        """
    
    def run(
        self,
        source_path: str,
        target_schema: Optional[TargetSchema],
        analysis: SourceSchemaAnalysis,
        transformation_requirements: Optional[str] = None,
        flexible_mode: bool = False,
        normalization_mode: bool = False
    ) -> str:
        """
        Generate a transformation script.
        
        Args:
            source_path: Path to input file
            target_schema: Desired output schema (optional in flexible/normalization mode)
            analysis: Source file analysis
            transformation_requirements: Optional text describing specific needs
            flexible_mode: If True, allows arbitrary transformations
            normalization_mode: If True, focuses on structure normalization (flattening, unpivoting)
            
        Returns:
            String containing the Python code
        """
        source_columns = ", ".join([col.column_name for col in analysis.columns])
        
        if normalization_mode:
             prompt = f"""Write a Python script to NORMALIZE and FLATTEN the unstructured hierarchical data in '{source_path}'.

SOURCE SCHEMA (Raw):
Columns: {source_columns}
Total Rows: {analysis.total_rows}

THE TASK:
The input file contains unstructured or grouped data (e.g., Ledger headers, merged cells, or parent-child relationships).
Your goal is to convert this into a flat, structured table suitable for database import.

SPECIFIC INSTRUCTIONS:
- Load the source Excel file using pandas (header=None usually helps for unstructured data).
- Identify "parent" rows (e.g., rows containing "Ledger:", "Group:", or bold headers) and "child" transaction rows.
- Create a new column for the parent entity (e.g., "Ledger Name") and fill it down for all valid transaction rows.
- Remove the original header/separator rows.
- Ensure the final output has a single header row and consistent columns.
- Save result to 'output/normalized_data.xlsx'.
- PRINT CLEAR LOGS to stdout explaining what structure was detected and determining the new columns.

USER HINT:
{transformation_requirements or "Look for grouped headers and flatten them."}
"""
        elif flexible_mode:
            prompt = f"""Write a Python script to transform '{source_path}' based on the user's request.

SOURCE SCHEMA:
Columns: {source_columns}
Total Rows: {analysis.total_rows}
DETECTED ENCODING: {analysis.encoding or 'utf-8'}

THE TASK:
{transformation_requirements}

SPECIFIC INSTRUCTIONS:
- Load the source file using pandas.
- IMPORTANT: For XML and CSV files, use the detected encoding: '{analysis.encoding or 'utf-8'}'.
  - For XML: pd.read_xml(path, encoding='{analysis.encoding or 'utf-8'}')
  - For CSV: pd.read_csv(path, encoding='{analysis.encoding or 'utf-8'}')

- **FOR EXCEL FILES:**
  - You **MUST** use the following pattern to ensure NO sheets are lost:
  ```python
  # 1. Load ALL sheets
  all_sheets = pd.read_excel(source_path, sheet_name=None) 
  
  # 2. Modify specific sheets
  if 'target_sheet' in all_sheets:
      all_sheets['target_sheet'] = ... # apply changes
      
  # 3. Save ALL sheets to output
  with pd.ExcelWriter('output/flexible_transform_result.xlsx') as writer:
      for sheet_name, df in all_sheets.items():
          df.to_excel(writer, sheet_name=sheet_name, index=False)
  ```
  - **CRITICAL**: Do NOT just save one dataframe with `df.to_excel()`. You MUST iterate through `all_sheets` and save them all.

- Implement the logic described in THE TASK. If it's empty or just says 'convert', perform a standard conversion of all data.
- If the request implies keeping all original columns, do so.
- If the request implies filtering or aggregation, the output should reflect that.
- Save result to 'output/flexible_transform_result.xlsx' AND 'output/flexible_transform_result.json' unless specifically asked for only one format.
- PRINT CLEAR LOGS to stdout.
"""
        else:
            # Standard Strict Mode
            if not target_schema:
                raise ValueError("Target schema is required for standard mode")
                
            # Format schema info
            target_columns = "\n".join([
                f"- {col.name} ({col.data_type}): {col.description or ''} {f'(Hint: {col.transformation_hint})' if col.transformation_hint else ''}" 
                for col in target_schema.columns
            ])
            
            prompt = f"""Write a Python script to transform '{source_path}'.

SOURCE SCHEMA:
Columns: {source_columns}
Total Rows: {analysis.total_rows}

TARGET SCHEMA (Create these columns):
{target_columns}

SPECIFIC INSTRUCTIONS:
- Load the source Excel file.
- Perform necessary transformations to create target columns.
- If transformation hint is provided (e.g., CONCATENATE, COMPUTE), implement that logic.
- Select ONLY the target columns for the final output.
- Save result to 'output/{target_schema.name}_fallback.xlsx'.
"""
            if transformation_requirements:
                prompt += f"\nADDITIONAL REQUIREMENTS:\n{transformation_requirements}"

        # Get code from AI
        response = self._call_api(prompt, max_tokens=4096)
        
        # Clean up markdown if present
        return self._clean_code(response)

    def _clean_code(self, text: str) -> str:
        """Remove markdown fencing if present."""
        text = text.strip()
        if text.startswith("```python"):
            text = text[9:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
