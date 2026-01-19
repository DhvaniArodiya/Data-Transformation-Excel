import sys
import os
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.excel_loader import ExcelLoader
from src.agents.schema_analyst import SchemaAnalystAgent
from src.agents.code_generation_agent import CodeGenerationAgent

from unittest.mock import patch, MagicMock
from src.agents.base_agent import BaseAgent

def verify_fix():
    file_path = 'temp_uploads/Bill Receivable.xml'
    print(f"--- Verifying fix for {file_path} ---")
    
    # 1. Test ExcelLoader detected encoding
    loader = ExcelLoader(file_path)
    print(f"Detected encoding: {loader.encoding}")
    assert loader.encoding == 'utf-16', f"Expected utf-16, got {loader.encoding}"
    
    # 2. Test SchemaAnalystAgent populates encoding
    analyst = SchemaAnalystAgent()
    analysis = analyst.run(file_path)
    print(f"Analysis encoding: {analysis.encoding}")
    assert analysis.encoding == 'utf-16', f"Expected utf-16 in analysis, got {analysis.encoding}"
    
    # 3. Test CodeGenerationAgent generates encoding-aware prompt
    code_gen = CodeGenerationAgent()
    
    with patch.object(BaseAgent, '_call_api') as mock_call:
        # Mock the API response
        mock_call.return_value = "import pandas as pd\ndf = pd.read_xml(path, encoding='utf-16')"
        
        code = code_gen.run(
            source_path=file_path,
            target_schema=None,
            analysis=analysis,
            transformation_requirements="Convert to JSON",
            flexible_mode=True
        )
        
        # Get the prompt that was sent to the API
        sent_prompt = mock_call.call_args[0][0]
        
        print("\n--- Captured Prompt (Snippet) ---")
        prompt_lines = sent_prompt.splitlines()
        for line in prompt_lines:
            if "ENCODING" in line or "read_xml" in line or "read_csv" in line:
                print(f"  > {line}")
        
        # Verify prompt content
        assert "DETECTED ENCODING: utf-16" in sent_prompt
        assert "encoding='utf-16'" in sent_prompt or 'encoding="utf-16"' in sent_prompt
        print("\nSUCCESS: Prompt contains correct encoding information!")

    # 4. Test with standard CSV to ensure default encoding (utf-8) also works
    csv_path = 'temp_uploads/invoice_data (3).csv'
    if os.path.exists(csv_path):
        print(f"\n--- Verifying fix for {csv_path} ---")
        loader_csv = ExcelLoader(csv_path)
        print(f"Detected encoding: {loader_csv.encoding}")
        analysis_csv = analyst.run(csv_path)
        
        with patch.object(BaseAgent, '_call_api') as mock_call_csv:
            mock_call_csv.return_value = "mock code"
            code_gen.run(
                source_path=csv_path,
                target_schema=None,
                analysis=analysis_csv,
                transformation_requirements="Convert",
                flexible_mode=True
            )
            sent_prompt_csv = mock_call_csv.call_args[0][0]
            assert "DETECTED ENCODING: utf-8" in sent_prompt_csv
            print("SUCCESS: CSV (utf-8) prompt generated correctly!")

if __name__ == "__main__":
    verify_fix()
