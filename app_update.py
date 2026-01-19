import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.orchestrator import Orchestrator, JobStatus
from src.agents.code_generation_agent import CodeGenerationAgent
from src.schemas.additional_schemas import SCHEMA_REGISTRY
from src.schemas.target_schema import get_schema, GENERIC_CUSTOMER_SCHEMA
from custom_customer_schema import CUSTOM_CUSTOMER_SCHEMA

# Register Custom Schema
SCHEMA_REGISTRY["custom_customer"] = CUSTOM_CUSTOMER_SCHEMA
SCHEMA_REGISTRY["csv"] = GENERIC_CUSTOMER_SCHEMA
SCHEMA_REGISTRY["json"] = GENERIC_CUSTOMER_SCHEMA

st.set_page_config(page_title="AI Data Transformer", page_icon="🤖", layout="wide")

def main():
    st.title("🤖 AI Data Transformation Agent")
    
    # Sidebar
    st.sidebar.header("Configuration")
    
    # API Key Handling
    from src.config import settings
    
    if not settings.anthropic_api_key:
        api_key = st.sidebar.text_input("Enter Azure/Anthropic API Key", type="password")
        if api_key:
            settings.anthropic_api_key = api_key
            os.environ["API_KEY"] = api_key
            # Reset client to pick up new key
            from src.client import _ai_client
            import src.client
            src.client._ai_client = None
            st.sidebar.success("API Key set!")
        else:
            st.sidebar.warning("API Key required for Flexible Mode")
            
    mode = st.sidebar.radio("Transformation Mode", ["Standard (Predefined Schema)", "Flexible (Natural Language)", "Intelligent Normalization (Unstructured Data)"])
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload Excel, CSV or XML file", type=['xlsx', 'csv', 'xml'])
    
    if uploaded_file:
        # Save uploaded file temporarily
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        file_path = temp_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.success(f"File uploaded: {uploaded_file.name}")
        
        # Display preview
        try:
            from src.utils.excel_loader import ExcelLoader
            loader = ExcelLoader(str(file_path))
            df = loader.load_sample(n_rows=15)
            st.subheader("Data Preview")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return

        # Transformation Options
        if mode == "Standard (Predefined Schema)":
            st.subheader("Standard Transformation")
            schema_names = list(SCHEMA_REGISTRY.keys())
            selected_schema = st.selectbox("Select Target Schema", schema_names, index=schema_names.index("custom_customer") if "custom_customer" in schema_names else 0)
            
            if st.button("Run Transformation"):
                run_standard_transform(str(file_path), selected_schema)
                
        elif mode == "Flexible (Natural Language)":
            st.subheader("Flexible Transformation")
            user_instruction = st.text_area("Describe the transformation you want:", placeholder="Example: Add a column called 'Premium' that is True if Age > 30, and filter only Premium users.")
            
            if st.button("Run Agent"):
                run_flexible_transform(str(file_path), user_instruction or "Convert the data into JSON and Excel formats.")
                    
        else: # Intelligent Normalization
            st.subheader("Intelligent Normalization")
            st.info("This mode uses AI to detect merged cells, grouped headers, and nested structures (like Ledgers) and converts them into a flat table.")
            user_hint = st.text_area("Optional Hint (e.g., 'Look for Ledger names in bold'):", height=70)
            
            if st.button("Normalize Data"):
                run_normalization(str(file_path), user_hint)

def run_normalization(file_path, hint):
    st.info("Starting Normalization Agent...")
    
    from src.agents.schema_analyst import SchemaAnalystAgent
    
    analyst = SchemaAnalystAgent()
    code_gen = CodeGenerationAgent()
    
    with st.spinner("Analyzing structure and generating cleaning script..."):
        try:
            # 1. Analyze
            analysis = analyst.run(file_path)
            
            # 2. Generate Code (Normalization Mode)
            code = code_gen.run(
                source_path=file_path,
                target_schema=None,
                analysis=analysis,
                transformation_requirements=hint,
                normalization_mode=True
            )
            
            # 3. Save and Execute Script
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            script_path = output_dir / f"normalize_script_{int(time.time())}.py"
            
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
                
            st.code(code, language='python')
            st.write("Executing cleaning script...")
            
            # Execute
            import subprocess
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=str(Path.cwd())
            )
            
            if result.returncode == 0:
                st.success("Normalization Successful!")
                st.text(result.stdout)
                
                expected_output = Path("output/normalized_data.xlsx")
                if expected_output.exists():
                    show_download_button(str(expected_output))
                else:
                    st.warning("Script ran but 'output/normalized_data.xlsx' was not found.")
            else:
                st.error("Execution Failed")
                st.text(result.stderr)
                
        except Exception as e:
            st.error(f"Error details: {e}")

def run_standard_transform(file_path, schema_name):
    # Direct Conversion for JSON/CSV (No Orchestrator/Planning/Validation)
    if schema_name in ["csv", "json"]:
        st.info(f"Directly converting to {schema_name.upper()}...")
        try:
            # 1. Load Data
            path = Path(file_path)
            if path.suffix == '.csv':
                df = pd.read_csv(path)
            elif path.suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(path)
            elif path.suffix == '.xml':
                df = pd.read_xml(path)
            else:
                st.error("Unsupported file format for direct conversion.")
                return

            # 2. Check for NaNs and Notify
            nan_counts = df.isna().sum().sum()
            if nan_counts > 0:
                nan_rows = df.isna().any(axis=1).sum()
                st.warning(f"⚠️ Found {nan_counts} missing values across {nan_rows} rows. These will be converted as empty strings.")
            
            # 3. Preview
            st.subheader(f"Data Preview ({schema_name.upper()})")
            st.dataframe(df.head())

            # 4. Save and Download
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_filename = f"direct_export_{int(time.time())}.{schema_name}"
            output_path = output_dir / output_filename
            
            if schema_name == "csv":
                df.to_csv(output_path, index=False)
            else:
                # Handle NaNs for JSON
                df.fillna("").to_json(output_path, orient="records", indent=4)
            
            st.success(f"Conversion to {schema_name.upper()} successful!")
            show_download_button(str(output_path))
            return
            
        except Exception as e:
            st.error(f"Direct conversion failed: {e}")
            return

    # Regular Orchestrator Flow (for Tally, Zoho, Employee, etc.)
    orchestrator = Orchestrator()
    placeholder = st.empty()
    
    with placeholder.container():
        st.info("Starting Orchestrator...")
        
        job = orchestrator.create_job(file_path, schema_name)
        st.write(f"Job ID: {job.job_id}")
        
        # Run job
        with st.spinner("Processing..."):
            job = orchestrator.run_job(job)
            
        if job.status == JobStatus.COMPLETED:
            st.success("Transformation Completed!")
            
            # Fix AttributeError: check if validation_report exists
            if job.validation_report:
                st.write(f"Quality Score: {job.validation_report.quality_score:.1f}%")
            
            if job.output_file and os.path.exists(job.output_file):
                show_download_button(job.output_file)
            else:
                st.error("Output file not found.")
        else:
            st.error(f"Transformation Failed: {job.error_message}")
            if job.pending_questions:
                st.warning(f"Pending Questions: {job.pending_questions}")

def run_flexible_transform(file_path, instruction):
    st.info("Starting Flexible Agent...")
    
    # We use the CodeGenerationAgent directly for flexible tasks
    # But we need basic analysis first
    from src.agents.schema_analyst import SchemaAnalystAgent
    
    analyst = SchemaAnalystAgent()
    code_gen = CodeGenerationAgent()
    
    with st.spinner("Analyzing and Generating Code..."):
        try:
            # 1. Analyze
            analysis = analyst.run(file_path)
            
            # 2. Generate Code (Flexible Mode)
            code = code_gen.run(
                source_path=file_path,
                target_schema=None,
                analysis=analysis,
                transformation_requirements=instruction,
                flexible_mode=True
            )
            
            # 3. Save and Execute Script
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            script_path = output_dir / f"flexible_script_{int(time.time())}.py"
            
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
                
            st.code(code, language='python')
            st.write("Executing generated script...")
            
            # Execute
            import subprocess
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=str(Path.cwd())
            )
            
            if result.returncode == 0:
                st.success("Execution Successful!")
                st.text(result.stdout)
                
                # Look for all expected output files
                expected_outputs = [
                    Path("output/flexible_transform_result.xlsx"),
                    Path("output/flexible_transform_result.json")
                ]
                
                found_any = False
                for output_path in expected_outputs:
                    if output_path.exists():
                        show_download_button(str(output_path))
                        found_any = True
                
                if not found_any:
                    st.warning("Script ran successfully but no output files were found.")
            else:
                st.error("Execution Failed")
                st.text(result.stderr)
                
        except Exception as e:
            st.error(f"Error details: {e}")

def show_download_button(file_path):
    import base64
    
    path = Path(file_path)
    if not path.exists():
        st.error("File not found.")
        return

    with open(path, "rb") as f:
        bytes_data = f.read()
        
    b64 = base64.b64encode(bytes_data).decode()
    mime_map = {
        '.xlsx': "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        '.csv': "text/csv",
        '.json': "application/json",
        '.xml': "application/xml"
    }
    mime = mime_map.get(path.suffix, "application/octet-stream")
    
    href = f'<a href="data:{mime};base64,{b64}" download="{path.name}" id="download_link" style="text-decoration:none;"><button style="background-color:#4CAF50; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer;">Download Transformed File</button></a>'
    st.markdown(href, unsafe_allow_html=True)
    
    # Auto-trigger download
    import streamlit.components.v1 as components
    components.html(f"""
        <script>
            setTimeout(function() {{
                var link = document.createElement('a');
                link.href = 'data:{mime};base64,{b64}';
                link.download = '{path.name}';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }}, 100);
        </script>
    """, height=0)
    
    # Also show preview of result
    st.subheader("Result Preview")
    try:
        if path.suffix == '.csv':
            df = pd.read_csv(path)
            st.dataframe(df.head())
        elif path.suffix == '.json':
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            st.json(data)
        elif path.suffix == '.xml':
            df = pd.read_xml(path)
            st.dataframe(df.head())
        else:
            df = pd.read_excel(path)
            st.dataframe(df.head())
    except Exception as e:
        st.info(f"Could not preview result: {e}")

if __name__ == "__main__":
    main()
