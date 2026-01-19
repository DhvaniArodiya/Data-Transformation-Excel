"""
Excel/CSV Loader Utilities.
Handles loading, sampling, and initial analysis of source files.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from ..config import get_settings


class ExcelLoader:
    """
    Utility class for loading Excel and CSV files.
    Handles sampling for AI analysis and full data loading.
    """
    
    SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.xlsm', '.csv', '.xml'}
    
    def __init__(self, file_path: str):
        """
        Initialize loader with file path.
        
        Args:
            file_path: Path to the Excel or CSV file
        """
        self.file_path = Path(file_path)
        self._validate_file()
        self._df: Optional[pd.DataFrame] = None
        self._sample_df: Optional[pd.DataFrame] = None
        self._metadata: Dict[str, Any] = {}
    
    def _validate_file(self):
        """Validate that the file exists and is supported."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {self.file_path.suffix}. "
                f"Supported: {self.SUPPORTED_EXTENSIONS}"
            )

    def _detect_encoding(self) -> str:
        """Detect file encoding, handling common BOMs."""
        try:
            with open(self.file_path, "rb") as f:
                raw = f.read(4)
                if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
                    return "utf-16"
                if raw.startswith(b'\xef\xbb\xbf'):
                    return "utf-8-sig"
            
            # Fallback attempts
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(self.file_path, "r", encoding=enc) as f:
                        f.read(1024)
                    return enc
                except:
                    continue
            return "utf-8"
        except:
            return "utf-8"

    @property
    def encoding(self) -> str:
        """Get the detected encoding for the file."""
        return self._detect_encoding()
    
    @property
    def is_excel(self) -> bool:
        """Check if file is an Excel file."""
        return self.file_path.suffix.lower() in {'.xlsx', '.xls', '.xlsm'}
    
    @property
    def is_csv(self) -> bool:
        """Check if file is a CSV file."""
        return self.file_path.suffix.lower() == '.csv'
    
    @property
    def is_xml(self) -> bool:
        """Check if file is an XML file."""
        return self.file_path.suffix.lower() == '.xml'
    
    def get_sheet_names(self) -> List[str]:
        """Get list of sheet names (Excel only)."""
        if not self.is_excel:
            return ["Sheet1"]  # CSV has single implicit sheet
        
        try:
            xlsx = pd.ExcelFile(self.file_path)
            return xlsx.sheet_names
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {e}")
    
    def load_full(
        self,
        sheet_name: Optional[str] = None,
        header_row: int = 0,
    ) -> pd.DataFrame:
        """
        Load the complete file into a DataFrame.
        
        Args:
            sheet_name: Sheet to load (Excel only, defaults to first sheet)
            header_row: Row index containing headers (0-indexed)
            
        Returns:
            Complete DataFrame
        """
        if self.is_csv:
            encoding = self._detect_encoding()
            self._df = pd.read_csv(
                self.file_path,
                header=header_row,
                dtype=str,
                encoding=encoding,
                na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'none'],
            )
        elif self.is_xml:
            encoding = self._detect_encoding()
            with open(self.file_path, "r", encoding=encoding) as f:
                self._df = pd.read_xml(f, dtype=str)
        else:
            self._df = pd.read_excel(
                self.file_path,
                sheet_name=sheet_name or 0,
                header=header_row,
                dtype=str,
                na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'none'],
            )
        
        self._update_metadata()
        return self._df
    
    def load_sample(
        self,
        n_rows: Optional[int] = None,
        sheet_name: Optional[str] = None,
        header_row: int = 0,
    ) -> pd.DataFrame:
        """
        Load a sample of rows for AI analysis.
        
        Args:
            n_rows: Number of rows to sample (defaults to settings.sample_rows)
            sheet_name: Sheet to load (Excel only)
            header_row: Row index containing headers
            
        Returns:
            Sample DataFrame
        """
        settings = get_settings()
        n_rows = n_rows or settings.sample_rows
        
        if self.is_csv:
            encoding = self._detect_encoding()
            self._sample_df = pd.read_csv(
                self.file_path,
                header=header_row,
                nrows=n_rows,
                dtype=str,
                encoding=encoding,
                na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'none'],
            )
        elif self.is_xml:
            encoding = self._detect_encoding()
            with open(self.file_path, "r", encoding=encoding) as f:
                self._sample_df = pd.read_xml(f).head(n_rows).astype(str)
        else:
            self._sample_df = pd.read_excel(
                self.file_path,
                sheet_name=sheet_name or 0,
                header=header_row,
                nrows=n_rows,
                dtype=str,
                na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', 'none'],
            )
        
        self._update_metadata(is_sample=True)
        return self._sample_df
    
    def _update_metadata(self, is_sample: bool = False):
        """Update internal metadata about the loaded data."""
        # Use simple if/else to avoid DataFrame truth value ambiguity
        df = None
        if is_sample:
            df = self._sample_df
        else:
            df = self._df
            
        if df is None:
            return
        
        self._metadata = {
            "file_name": self.file_path.name,
            "file_type": "csv" if self.is_csv else ("xml" if self.is_xml else "excel"),
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "column_names": list(df.columns),
            "is_sample": is_sample,
        }
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get file metadata."""
        return self._metadata
    
    def get_column_samples(
        self,
        n_samples: int = 5,
        df: Optional[pd.DataFrame] = None
    ) -> Dict[str, List[str]]:
        """
        Get sample values for each column.
        
        Args:
            n_samples: Number of sample values per column
            df: DataFrame to sample from (defaults to loaded sample)
            
        Returns:
            Dict mapping column names to sample values
        """
        # Proper fallback logic to avoid boolean ambiguity
        if df is None:
            df = self._sample_df
        if df is None:
            df = self._df
            
        if df is None:
            return {}
        
        samples = {}
        for col in df.columns:
            # Get non-null unique values
            non_null = df[col].dropna().unique()
            sample_values = non_null[:n_samples].tolist()
            samples[col] = [str(v) for v in sample_values]
        
        return samples
    
    def get_column_stats(
        self,
        df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for each column.
        
        Args:
            df: DataFrame to analyze (defaults to loaded sample)
            
        Returns:
            Dict mapping column names to statistics
        """
        if df is None:
            df = self._sample_df
        if df is None:
            df = self._df
            
        if df is None:
            return {}
        
        stats = {}
        for col in df.columns:
            col_data = df[col]
            stats[col] = {
                "total_values": len(col_data),
                "null_count": col_data.isna().sum(),
                "unique_count": col_data.nunique(),
                "completeness": 1 - (col_data.isna().sum() / len(col_data)),
            }
        
        return stats
    
    def to_csv_string(
        self,
        df: Optional[pd.DataFrame] = None,
        max_rows: int = 20
    ) -> str:
        """
        Convert DataFrame to CSV string for AI analysis.
        
        Args:
            df: DataFrame to convert
            max_rows: Maximum rows to include
            
        Returns:
            CSV string representation
        """
        if df is None:
            df = self._sample_df
        if df is None:
            df = self._df
            
        if df is None:
            return ""
        
        return df.head(max_rows).to_csv(index=False)
    
    def load_raw(
        self,
        sheet_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Load entire sheet as-is without header assumptions.
        Used for table detection scanning.
        
        Args:
            sheet_name: Sheet to load (Excel only)
            
        Returns:
            Raw DataFrame with no header row set
        """
        if self.is_csv:
            encoding = self._detect_encoding()
            return pd.read_csv(
                self.file_path,
                header=None,
                dtype=str,
                encoding=encoding,
                na_values=[''],
            )
        elif self.is_xml:
            encoding = self._detect_encoding()
            with open(self.file_path, "r", encoding=encoding) as f:
                return pd.read_xml(f).astype(str)
        else:
            return pd.read_excel(
                self.file_path,
                sheet_name=sheet_name or 0,
                header=None,
                dtype=str,
                na_values=[''],
            )
    
    def extract_table(
        self,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        header_row_offset: int = 0,
        sheet_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Extract a specific table region as DataFrame.
        
        Args:
            start_row: Starting row index (0-indexed, inclusive)
            end_row: Ending row index (0-indexed, inclusive)
            start_col: Starting column index (0-indexed, inclusive)
            end_col: Ending column index (0-indexed, inclusive)
            header_row_offset: Offset from start_row where headers are
            sheet_name: Sheet to load (Excel only)
            
        Returns:
            DataFrame with the extracted table data
        """
        # Load raw first
        raw_df = self.load_raw(sheet_name)
        
        # Extract the region
        table_slice = raw_df.iloc[
            start_row:end_row + 1,
            start_col:end_col + 1
        ].copy()
        
        # Get headers from the header row
        header_row = table_slice.iloc[header_row_offset]
        column_names = []
        for idx, val in enumerate(header_row):
            if pd.isna(val) or str(val).strip() == '':
                column_names.append(f"Column_{idx + 1}")
            else:
                column_names.append(str(val).strip())
        
        # Extract data rows (after header)
        data_df = table_slice.iloc[header_row_offset + 1:].copy()
        data_df.columns = column_names
        data_df = data_df.reset_index(drop=True)
        
        # Clean up - remove completely empty rows
        data_df = data_df.dropna(how='all')
        
        return data_df
    
    def extract_table_from_boundary(
        self,
        boundary: Any,  # TableBoundary type
        header_row_offset: int = 0,
        sheet_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Extract a table using a TableBoundary object.
        
        Args:
            boundary: TableBoundary with start_row, end_row, start_col, end_col
            header_row_offset: Offset from start_row where headers are
            sheet_name: Sheet to load (Excel only)
            
        Returns:
            DataFrame with the extracted table data
        """
        return self.extract_table(
            start_row=boundary.start_row,
            end_row=boundary.end_row,
            start_col=boundary.start_col,
            end_col=boundary.end_col,
            header_row_offset=header_row_offset,
            sheet_name=sheet_name,
        )


def load_file(file_path: str, sample_only: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Convenience function to load a file.
    
    Args:
        file_path: Path to the file
        sample_only: If True, load only sample rows
        
    Returns:
        Tuple of (DataFrame, metadata dict)
    """
    loader = ExcelLoader(file_path)
    
    if sample_only:
        df = loader.load_sample()
    else:
        df = loader.load_full()
    
    return df, loader.metadata
