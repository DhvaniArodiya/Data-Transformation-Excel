"""
Integration test for the complete transformation pipeline.
"""

import pytest
import sys
import os
from pathlib import Path
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engine.function_registry import get_registry
from src.engine.execution_engine import ExecutionEngine, execute_plan
from src.schemas.transformation_plan import (
    TransformationPlan,
    ColumnMapping,
    Transformation,
    TransformationParams,
    Enrichment,
)
from src.schemas.validation_report import ValidationReport
from src.utils.excel_loader import ExcelLoader


class TestExecutionEngine:
    """Test the ExecutionEngine with real transformation plans."""
    
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            "Name": ["John Doe", "Jane Smith", "Robert Johnson"],
            "Phone": ["9876543210", "+91-8765432109", "91 7654321098"],
            "Amount": ["₹ 15,000", "Rs.25000", "35,000"],
            "Date": ["25/12/2024", "2024-12-10", "12-Dec-2024"],
            "Pin": ["400001", "110001", "560001"],
        })
    
    @pytest.fixture
    def transformation_plan(self):
        """Create a sample transformation plan."""
        return TransformationPlan(
            transformation_id="test_001",
            confidence_score=0.9,
            column_mappings=[
                ColumnMapping(source_col="Name", target_col="first_name", action="transform", transform_id="tf_01"),
                ColumnMapping(source_col="Name", target_col="last_name", action="transform", transform_id="tf_01"),
                ColumnMapping(source_col="Phone", target_col="phone", action="transform", transform_id="tf_02"),
                ColumnMapping(source_col="Amount", target_col="amount", action="transform", transform_id="tf_03"),
                ColumnMapping(source_col="Date", target_col="date", action="transform", transform_id="tf_04"),
            ],
            transformations=[
                Transformation(
                    id="tf_01",
                    function="SPLIT_FULL_NAME",
                    input_col="Name",
                    output_cols=["first_name", "last_name"],
                    params=TransformationParams(delimiter="auto"),
                ),
                Transformation(
                    id="tf_02",
                    function="NORMALIZE_PHONE",
                    input_col="Phone",
                    output_col="phone",
                    params=TransformationParams(region="IN", format="E.164"),
                ),
                Transformation(
                    id="tf_03",
                    function="NORMALIZE_CURRENCY",
                    input_col="Amount",
                    output_col="amount",
                    params=TransformationParams(),
                ),
                Transformation(
                    id="tf_04",
                    function="FORMAT_DATE",
                    input_col="Date",
                    output_col="date",
                    params=TransformationParams(target_format="%Y-%m-%d"),
                ),
            ],
            enrichments=[
                Enrichment(
                    id="en_01",
                    trigger_col="Pin",
                    target_cols=["city", "state"],
                    api_service="postal_code_lookup",
                    strategy="cache_first_then_api",
                ),
            ],
        )
    
    def test_engine_execution(self, sample_df, transformation_plan):
        """Test complete engine execution."""
        engine = ExecutionEngine()
        result_df, errors = engine.execute(sample_df, transformation_plan)
        
        assert len(result_df) == 3
        assert "first_name" in result_df.columns
        assert result_df["first_name"].iloc[0] == "John"
    
    def test_phone_normalization(self, sample_df, transformation_plan):
        """Test phone numbers are normalized."""
        result_df, _ = execute_plan(sample_df, transformation_plan)
        
        phones = result_df["phone"].tolist()
        assert all(p.startswith("+91") for p in phones if p)
    
    def test_currency_normalization(self, sample_df, transformation_plan):
        """Test currency values are normalized."""
        result_df, _ = execute_plan(sample_df, transformation_plan)
        
        amounts = result_df["amount"].tolist()
        assert 15000.0 in amounts
        assert 25000.0 in amounts
    
    def test_enrichment(self, sample_df, transformation_plan):
        """Test enrichment adds city/state."""
        result_df, _ = execute_plan(sample_df, transformation_plan)
        
        assert "city" in result_df.columns
        assert "Mumbai" in result_df["city"].values


class TestExcelLoader:
    """Test Excel/CSV loading functionality."""
    
    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        """Create a temporary CSV file for testing."""
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({
            "Name": ["John", "Jane", "Bob"],
            "Email": ["john@test.com", "jane@test.com", "bob@test.com"],
        })
        df.to_csv(csv_path, index=False)
        return str(csv_path)
    
    def test_load_csv(self, sample_csv_path):
        """Test loading a CSV file."""
        loader = ExcelLoader(sample_csv_path)
        df = loader.load_full()
        
        assert len(df) == 3
        assert "Name" in df.columns
    
    def test_load_sample(self, sample_csv_path):
        """Test loading a sample of rows."""
        loader = ExcelLoader(sample_csv_path)
        df = loader.load_sample(n_rows=2)
        
        assert len(df) == 2
    
    def test_column_samples(self, sample_csv_path):
        """Test getting column samples."""
        loader = ExcelLoader(sample_csv_path)
        loader.load_sample()
        samples = loader.get_column_samples()
        
        assert "Name" in samples
        assert len(samples["Name"]) <= 5
    
    def test_invalid_file(self):
        """Test error handling for invalid file."""
        with pytest.raises(FileNotFoundError):
            ExcelLoader("nonexistent.xlsx")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
