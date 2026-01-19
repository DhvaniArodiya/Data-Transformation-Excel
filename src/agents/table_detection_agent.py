"""
Table Detection Agent - Detects multiple tables in Excel files.
Uses hybrid AI + heuristic approach to identify table boundaries.
"""

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import re

from .base_agent import BaseAgent
from ..schemas.detected_table import (
    TableBoundary,
    DetectedTable,
    MetadataSection,
    MultiTableAnalysis,
)
from ..utils.excel_loader import ExcelLoader


class TableDetectionAgent(BaseAgent):
    """
    Detects table boundaries in Excel files with complex layouts.
    
    Handles:
    - Multiple vertical tables (separated by empty rows)
    - Multiple horizontal tables (side by side)
    - Metadata sections (key-value pairs)
    - Nested/hierarchical tables
    - Mixed content (tables + notes)
    """
    
    # Configuration
    MIN_TABLE_ROWS = 2  # Minimum rows to be considered a table
    MIN_TABLE_COLS = 2  # Minimum columns to be considered a table
    EMPTY_ROW_SEPARATOR = 2  # Number of consecutive empty rows to split tables
    
    @property
    def name(self) -> str:
        return "Table Detection Agent"
    
    @property
    def system_prompt(self) -> str:
        return """You are a Table Structure Detection Agent. Your job is to analyze raw Excel/CSV data and identify distinct tables within a single sheet.

TASK: Given a raw data dump from an Excel sheet, identify:
1. Table boundaries (start row, end row, start column, end column)
2. Table headers (which row contains column names)
3. Table types (data_table, summary, metadata)
4. Any metadata/title sections above tables

PATTERNS TO DETECT:
- Empty rows separating tables vertically
- Empty columns separating tables horizontally
- Title/heading rows before data tables
- Key-value metadata sections (e.g., "Company: ABC Corp")
- Summary rows at bottom of tables (e.g., "Total: 10000")

OUTPUT: Return ONLY valid JSON with this structure:
{
  "tables": [
    {
      "table_id": "table_001",
      "title": "Customer Details" or null,
      "start_row": 5,
      "end_row": 50,
      "start_col": 0,
      "end_col": 5,
      "header_row_offset": 0,
      "table_type": "data_table",
      "confidence": 0.95
    }
  ],
  "metadata_sections": [
    {
      "section_id": "meta_001",
      "start_row": 0,
      "end_row": 3,
      "entries": {"Company": "ABC Corp", "Date": "2024-01-15"}
    }
  ],
  "detection_notes": "Found 2 tables separated by empty rows"
}

Be precise with row/column indices (0-indexed). Do not include any text outside the JSON."""
    
    def run(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
    ) -> MultiTableAnalysis:
        """
        Detect all tables in the given Excel file/sheet.
        
        Args:
            file_path: Path to the Excel/CSV file
            sheet_name: Specific sheet to analyze (Excel only)
            
        Returns:
            MultiTableAnalysis with detected tables
        """
        # Load raw data without header assumptions
        loader = ExcelLoader(file_path)
        raw_df = self._load_raw_sheet(loader, sheet_name)
        
        # Step 1: Heuristic detection
        heuristic_tables = self._heuristic_detection(raw_df)
        
        # Step 2: If we found clear boundaries, use them
        if heuristic_tables and all(t.confidence >= 0.8 for t in heuristic_tables):
            tables = heuristic_tables
            detection_method = "heuristic"
        else:
            # Step 3: Use AI to refine detection
            ai_result = self._ai_detection(raw_df, heuristic_tables)
            tables = self._merge_detections(heuristic_tables, ai_result)
            detection_method = "hybrid"
        
        # Extract metadata sections
        metadata = self._detect_metadata_sections(raw_df, tables)
        
        # Add sample values to each table
        for table in tables:
            table.sample_values = self._extract_samples(raw_df, table)
        
        # Calculate overall confidence
        overall_confidence = sum(t.confidence for t in tables) / len(tables) if tables else 0.0
        
        return MultiTableAnalysis(
            file_name=loader.file_path.name,
            sheet_name=sheet_name or "Sheet1",
            tables=tables,
            metadata_sections=metadata,
            total_tables_detected=len(tables),
            total_rows_in_sheet=len(raw_df),
            total_cols_in_sheet=len(raw_df.columns),
            detection_method=detection_method,
            overall_confidence=overall_confidence,
        )
    
    def _load_raw_sheet(
        self,
        loader: ExcelLoader,
        sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """Load sheet without header assumptions."""
        if loader.is_csv:
            return pd.read_csv(
                loader.file_path,
                header=None,  # No header assumption
                dtype=str,
                na_values=[''],
            )
        else:
            return pd.read_excel(
                loader.file_path,
                sheet_name=sheet_name or 0,
                header=None,  # No header assumption
                dtype=str,
                na_values=[''],
            )
    
    def _heuristic_detection(self, df: pd.DataFrame) -> List[DetectedTable]:
        """
        Detect tables using heuristic rules.
        
        Strategy:
        1. Find empty row separators
        2. Find empty column separators
        3. Identify contiguous data blocks
        4. Detect headers based on patterns
        """
        tables = []
        
        # Find row-separated tables (vertical stacking)
        row_tables = self._find_vertical_tables(df)
        
        # For each horizontal slice, check for column-separated tables
        for row_table_boundary in row_tables:
            col_tables = self._find_horizontal_tables(df, row_table_boundary)
            tables.extend(col_tables)
        
        # Assign IDs and detect headers
        for idx, table in enumerate(tables):
            table.table_id = f"table_{idx+1:03d}"
            header_info = self._detect_header_row(df, table.boundary)
            table.header_row = header_info['row']
            table.column_names = header_info['names']
            table.column_count = len(table.column_names)
            table.row_count = table.boundary.row_count - table.header_row - 1
        
        return tables
    
    def _find_vertical_tables(self, df: pd.DataFrame) -> List[TableBoundary]:
        """Find tables separated by empty rows."""
        boundaries = []
        
        # Identify empty rows (all NaN or empty string)
        empty_rows = df.apply(
            lambda row: row.isna().all() or (row.astype(str).str.strip() == '').all(),
            axis=1
        )
        
        # Convert to list of indices
        empty_row_indices = empty_rows[empty_rows].index.tolist()
        
        # Find contiguous blocks
        start_row = 0
        for end_row in empty_row_indices:
            if end_row - start_row >= self.MIN_TABLE_ROWS:
                # Found a potential table block
                # Get the actual column range
                block = df.iloc[start_row:end_row]
                col_range = self._get_data_column_range(block)
                
                if col_range[1] - col_range[0] + 1 >= self.MIN_TABLE_COLS:
                    boundaries.append(TableBoundary(
                        start_row=start_row,
                        end_row=end_row - 1,
                        start_col=col_range[0],
                        end_col=col_range[1],
                    ))
            
            start_row = end_row + 1
        
        # Handle the last block
        if len(df) - start_row >= self.MIN_TABLE_ROWS:
            block = df.iloc[start_row:]
            col_range = self._get_data_column_range(block)
            
            if col_range[1] - col_range[0] + 1 >= self.MIN_TABLE_COLS:
                boundaries.append(TableBoundary(
                    start_row=start_row,
                    end_row=len(df) - 1,
                    start_col=col_range[0],
                    end_col=col_range[1],
                ))
        
        # If no separators found, treat entire sheet as one table
        if not boundaries and len(df) >= self.MIN_TABLE_ROWS:
            col_range = self._get_data_column_range(df)
            if col_range[1] - col_range[0] + 1 >= self.MIN_TABLE_COLS:
                boundaries.append(TableBoundary(
                    start_row=0,
                    end_row=len(df) - 1,
                    start_col=col_range[0],
                    end_col=col_range[1],
                ))
        
        return boundaries
    
    def _find_horizontal_tables(
        self,
        df: pd.DataFrame,
        row_boundary: TableBoundary
    ) -> List[DetectedTable]:
        """Find tables separated by empty columns within a row range."""
        tables = []
        
        # Extract the row slice
        row_slice = df.iloc[row_boundary.start_row:row_boundary.end_row + 1]
        
        # Find empty columns
        empty_cols = row_slice.apply(
            lambda col: col.isna().all() or (col.astype(str).str.strip() == '').all(),
            axis=0
        )
        
        empty_col_indices = empty_cols[empty_cols].index.tolist()
        
        # If no empty column separators, return single table
        if not empty_col_indices:
            tables.append(DetectedTable(
                table_id="",  # Will be assigned later
                boundary=row_boundary,
                confidence=0.9,
            ))
            return tables
        
        # Split by empty columns
        start_col = row_boundary.start_col
        for end_col_idx in empty_col_indices:
            end_col = end_col_idx
            if end_col - start_col >= self.MIN_TABLE_COLS:
                tables.append(DetectedTable(
                    table_id="",
                    boundary=TableBoundary(
                        start_row=row_boundary.start_row,
                        end_row=row_boundary.end_row,
                        start_col=start_col,
                        end_col=end_col - 1,
                    ),
                    confidence=0.85,
                ))
            start_col = end_col + 1
        
        # Handle last segment
        if row_boundary.end_col - start_col + 1 >= self.MIN_TABLE_COLS:
            tables.append(DetectedTable(
                table_id="",
                boundary=TableBoundary(
                    start_row=row_boundary.start_row,
                    end_row=row_boundary.end_row,
                    start_col=start_col,
                    end_col=row_boundary.end_col,
                ),
                confidence=0.85,
            ))
        
        return tables
    
    def _get_data_column_range(self, df: pd.DataFrame) -> Tuple[int, int]:
        """Get the range of columns that contain data."""
        non_empty_cols = df.apply(
            lambda col: not (col.isna().all() or (col.astype(str).str.strip() == '').all()),
            axis=0
        )
        
        col_indices = non_empty_cols[non_empty_cols].index.tolist()
        if not col_indices:
            return (0, 0)
        
        return (min(col_indices), max(col_indices))
    
    def _detect_header_row(
        self,
        df: pd.DataFrame,
        boundary: TableBoundary
    ) -> Dict[str, Any]:
        """
        Detect which row contains column headers.
        
        Heuristics:
        1. First row with mostly non-empty, non-numeric values
        2. Row with unique values (no duplicates)
        3. Row followed by data rows
        """
        # Extract the table region
        table_slice = df.iloc[
            boundary.start_row:boundary.end_row + 1,
            boundary.start_col:boundary.end_col + 1
        ]
        
        best_header_row = 0
        best_score = 0
        
        # Check first 5 rows for potential headers
        for row_idx in range(min(5, len(table_slice))):
            row = table_slice.iloc[row_idx]
            score = self._score_header_row(row, table_slice.iloc[row_idx + 1:] if row_idx + 1 < len(table_slice) else pd.DataFrame())
            
            if score > best_score:
                best_score = score
                best_header_row = row_idx
        
        # Extract column names from header row
        header_row = table_slice.iloc[best_header_row]
        column_names = []
        for idx, val in enumerate(header_row):
            if pd.isna(val) or str(val).strip() == '':
                column_names.append(f"Column_{idx + 1}")
            else:
                column_names.append(str(val).strip())
        
        return {
            'row': best_header_row,
            'names': column_names,
            'confidence': min(best_score / 100, 1.0),
        }
    
    def _score_header_row(self, row: pd.Series, data_below: pd.DataFrame) -> float:
        """Score how likely a row is to be a header."""
        score = 0.0
        
        # 1. Non-empty values
        non_empty = (~row.isna() & (row.astype(str).str.strip() != '')).sum()
        score += non_empty * 10
        
        # 2. Mostly non-numeric (headers are usually text)
        numeric_count = 0
        for val in row.dropna():
            try:
                float(str(val).replace(',', '').replace('$', '').replace('₹', ''))
                numeric_count += 1
            except:
                pass
        score += (len(row) - numeric_count) * 5
        
        # 3. Unique values (headers shouldn't repeat)
        if len(row.dropna().unique()) == len(row.dropna()):
            score += 20
        
        # 4. String-like values
        string_count = sum(1 for v in row.dropna() if isinstance(v, str) or not str(v).replace('.', '').isdigit())
        score += string_count * 3
        
        return score
    
    def _ai_detection(
        self,
        df: pd.DataFrame,
        heuristic_tables: List[DetectedTable]
    ) -> Dict[str, Any]:
        """Use AI to detect/refine table boundaries."""
        # Prepare raw data sample for AI
        # Take first 50 rows and first 20 columns to keep prompt reasonable
        sample_df = df.iloc[:50, :20]
        
        # Convert to string representation
        raw_repr = self._df_to_raw_string(sample_df)
        
        # Include heuristic results for context
        heuristic_context = []
        for t in heuristic_tables:
            heuristic_context.append({
                "start_row": t.boundary.start_row,
                "end_row": t.boundary.end_row,
                "start_col": t.boundary.start_col,
                "end_col": t.boundary.end_col,
                "confidence": t.confidence,
            })
        
        prompt = f"""Analyze this raw Excel data and identify distinct tables.

RAW DATA (showing row/column indices):
{raw_repr}

HEURISTIC DETECTION RESULTS (may need refinement):
{self._format_data_for_prompt(heuristic_context)}

Total rows in sheet: {len(df)}
Total columns in sheet: {len(df.columns)}

Identify the table boundaries, headers, and any metadata sections. Return JSON as specified."""
        
        try:
            result = self._call_api_json(prompt)
            return result
        except Exception as e:
            # Return empty on AI failure
            return {"tables": [], "metadata_sections": [], "detection_notes": f"AI detection failed: {str(e)}"}
    
    def _df_to_raw_string(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to raw string with row/column indices."""
        lines = []
        
        # Header line with column indices
        col_header = "     | " + " | ".join(f"C{i:02d}" for i in range(len(df.columns)))
        lines.append(col_header)
        lines.append("-" * len(col_header))
        
        for row_idx in range(len(df)):
            row_values = []
            for col_idx in range(len(df.columns)):
                val = df.iloc[row_idx, col_idx]
                if pd.isna(val) or str(val).strip() == '':
                    row_values.append("   ")
                else:
                    row_values.append(str(val)[:10].ljust(10))
            
            lines.append(f"R{row_idx:02d} | " + " | ".join(row_values))
        
        return "\n".join(lines)
    
    def _merge_detections(
        self,
        heuristic: List[DetectedTable],
        ai_result: Dict[str, Any]
    ) -> List[DetectedTable]:
        """Merge heuristic and AI detection results."""
        # Start with heuristic results
        tables = heuristic.copy()
        
        ai_tables = ai_result.get("tables", [])
        
        # For each AI table, check if it overlaps with heuristic
        for ai_table in ai_tables:
            ai_boundary = TableBoundary(
                start_row=ai_table.get("start_row", 0),
                end_row=ai_table.get("end_row", 0),
                start_col=ai_table.get("start_col", 0),
                end_col=ai_table.get("end_col", 0),
            )
            
            overlaps = False
            for h_table in heuristic:
                if self._boundaries_overlap(h_table.boundary, ai_boundary):
                    # Update heuristic table with AI info
                    if ai_table.get("title"):
                        h_table.title = ai_table["title"]
                    if ai_table.get("table_type"):
                        h_table.table_type = ai_table["table_type"]
                    # Boost confidence with AI confirmation
                    h_table.confidence = min(h_table.confidence + 0.1, 1.0)
                    overlaps = True
                    break
            
            # If no overlap, AI found a new table
            if not overlaps and ai_table.get("confidence", 0) > 0.7:
                tables.append(DetectedTable(
                    table_id=ai_table.get("table_id", f"ai_table_{len(tables)+1}"),
                    title=ai_table.get("title"),
                    boundary=ai_boundary,
                    header_row=ai_table.get("header_row_offset", 0),
                    table_type=ai_table.get("table_type", "data_table"),
                    confidence=ai_table.get("confidence", 0.8),
                ))
        
        return tables
    
    def _boundaries_overlap(self, b1: TableBoundary, b2: TableBoundary) -> bool:
        """Check if two boundaries overlap significantly."""
        # Check row overlap
        row_overlap = not (b1.end_row < b2.start_row or b2.end_row < b1.start_row)
        # Check column overlap
        col_overlap = not (b1.end_col < b2.start_col or b2.end_col < b1.start_col)
        
        return row_overlap and col_overlap
    
    def _detect_metadata_sections(
        self,
        df: pd.DataFrame,
        tables: List[DetectedTable]
    ) -> List[MetadataSection]:
        """Detect metadata/key-value sections not part of tables."""
        metadata = []
        
        # Find rows not covered by tables
        table_rows = set()
        for table in tables:
            for row in range(table.boundary.start_row, table.boundary.end_row + 1):
                table_rows.add(row)
        
        # Check non-table rows for metadata patterns
        current_section_start = None
        current_entries = {}
        
        for row_idx in range(len(df)):
            if row_idx in table_rows:
                # Save any pending metadata section
                if current_entries:
                    metadata.append(MetadataSection(
                        section_id=f"meta_{len(metadata)+1:03d}",
                        start_row=current_section_start,
                        end_row=row_idx - 1,
                        entries=current_entries,
                    ))
                    current_entries = {}
                    current_section_start = None
                continue
            
            # Check if this row is a key-value pair
            row = df.iloc[row_idx]
            kv_pair = self._extract_key_value(row)
            if kv_pair:
                if current_section_start is None:
                    current_section_start = row_idx
                current_entries[kv_pair[0]] = kv_pair[1]
        
        # Save final section
        if current_entries and current_section_start is not None:
            metadata.append(MetadataSection(
                section_id=f"meta_{len(metadata)+1:03d}",
                start_row=current_section_start,
                end_row=len(df) - 1,
                entries=current_entries,
            ))
        
        return metadata
    
    def _extract_key_value(self, row: pd.Series) -> Optional[Tuple[str, str]]:
        """Extract key-value pair from a row if it matches the pattern."""
        # Count non-empty cells
        non_empty = row.dropna()
        non_empty = non_empty[non_empty.astype(str).str.strip() != '']
        
        # Metadata rows typically have 1-2 values
        if len(non_empty) > 3:
            return None
        
        # Look for "Key: Value" pattern in first cell
        first_val = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else ""
        
        # Pattern: "Company: ABC Corp" or "Date: 2024-01-15"
        match = re.match(r'^([A-Za-z][A-Za-z0-9\s]*?):\s*(.+)$', first_val)
        if match:
            return (match.group(1).strip(), match.group(2).strip())
        
        # Pattern: Key in col 0, value in col 1
        if len(non_empty) == 2:
            key = str(row.iloc[0]).strip()
            value = str(row.iloc[1]).strip()
            if key and value and not key.replace(' ', '').isdigit():
                return (key, value)
        
        return None
    
    def _extract_samples(
        self,
        df: pd.DataFrame,
        table: DetectedTable
    ) -> Dict[str, List[str]]:
        """Extract sample values for each column of a detected table."""
        samples = {}
        
        # Get data rows (skip header)
        data_start = table.boundary.start_row + table.header_row + 1
        data_end = table.boundary.end_row + 1
        
        if data_start >= data_end:
            return samples
        
        table_data = df.iloc[
            data_start:data_end,
            table.boundary.start_col:table.boundary.end_col + 1
        ]
        
        for col_idx, col_name in enumerate(table.column_names):
            if col_idx < len(table_data.columns):
                col_values = table_data.iloc[:, col_idx].dropna()
                col_values = col_values[col_values.astype(str).str.strip() != '']
                samples[col_name] = [str(v) for v in col_values.head(5).tolist()]
        
        return samples
