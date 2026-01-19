import sys
from pathlib import Path
import json
import pandas as pd
import unittest
from unittest.mock import MagicMock

# Add src to path
sys.path.insert(0, str(Path.cwd()))

from src.agents.file_router import FileRouterAgent
from src.utils.excel_loader import ExcelLoader

# Mock get_ai_client locally to avoid initializing real Anthropic client which might hang/fail
from unittest.mock import patch

class TestIntelligentRouting(unittest.TestCase):
    def setUp(self):
        # Create dummy files for testing schema extraction
        self.test_dir = Path("temp_test_routing")
        self.test_dir.mkdir(exist_ok=True)
        
        # 1. Excel with specific sheets
        self.excel_path = self.test_dir / "test_data.xlsx"
        with pd.ExcelWriter(self.excel_path) as writer:
            df1 = pd.DataFrame({'id': [1], 'value': [100]})
            df1.to_excel(writer, sheet_name='report_metadata', index=False)
            df2 = pd.DataFrame({'tx_id': [1], 'period_start': ['2024-01-01']})
            df2.to_excel(writer, sheet_name='ledger_master', index=False)
            
        # 2. CSV file
        self.csv_path = self.test_dir / "test_data.csv"
        df_csv = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        df_csv.to_csv(self.csv_path, index=False)

    def tearDown(self):
        # Cleanup
        try:
            import shutil
            shutil.rmtree(self.test_dir)
        except:
            pass

    def test_schema_extraction(self):
        print("\nTesting Schema Extraction...")
        
        # Test Excel
        loader = ExcelLoader(str(self.excel_path))
        self.assertTrue(loader.is_excel)
        sheets = loader.get_sheet_names()
        print(f"Detected sheets: {sheets}")
        self.assertIn("report_metadata", sheets)
        self.assertIn("ledger_master", sheets)
        
        # Test CSV columns
        loader_csv = ExcelLoader(str(self.csv_path))
        df_sample = loader_csv.load_sample(n_rows=5)
        columns = list(df_sample.columns)
        print(f"Detected CSV columns: {columns}")
        self.assertIn("col1", columns)

    @patch('src.agents.base_agent.get_ai_client')
    def test_router_prompt_construction(self, mock_get_client):
        print("\nTesting Router Prompt Construction...")
        # Configure mock client
        mock_client_instance = MagicMock()
        mock_get_client.return_value = mock_client_instance
        
        # Mock the API call to inspect the prompt
        agent = FileRouterAgent()
        # We need to mock _call_api_json explicitly on the agent instance
        # typically agent.run or agent.select_files calls _call_api_json
        # But _call_api_json calls client.get_json_response. 
        # Since we mock client, we can mock that response return value.
        
        # However, to easily inspect the prompt sent to _call_api_json (which constructs the prompt),
        # we can mock _call_api_json itself as before.
        agent._call_api_json = MagicMock(return_value={"selected_files": ["test_data.xlsx"]})
        
        files = [self.excel_path, self.csv_path]
        prompt_text = "Extract from report_metadata sheet"
        
        # Simulate the logic in app.py where we build schemas
        schemas = {
            self.excel_path.name: {
                "sheet_names": ["report_metadata", "ledger_master"],
                "columns": ["id", "value"] # Sample from first sheet
            },
            self.csv_path.name: {
                "columns": ["col1", "col2"]
            }
        }
        
        # Run selection
        selected = agent.select_files(files, prompt_text, schemas=schemas)
        
        # Check what was sent to LLM
        call_args = agent._call_api_json.call_args
        prompt_sent = call_args[0][0]
        
        print(f"Prompt sent to LLM:\n{prompt_sent}")
        
        # Verify schema info is in the prompt
        self.assertIn("report_metadata", prompt_sent)
        self.assertIn("ledger_master", prompt_sent)
        self.assertIn("col1", prompt_sent)
        
        # Verify logic returns the mocked selection
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].name, "test_data.xlsx")

    def test_router_fallback(self):
        print("\nTesting Router Fallback...")
        agent = FileRouterAgent()
        # Mock API to raise an exception
        agent._call_api_json = MagicMock(side_effect=Exception("API Error"))
        
        files = [self.excel_path, self.csv_path]
        selected = agent.select_files(files, "prompt")
        
        # Should now return EMPTY list, not ALL files
        self.assertEqual(selected, [])
        print("Fallback correctly returned empty list.")

if __name__ == '__main__':
    unittest.main()
