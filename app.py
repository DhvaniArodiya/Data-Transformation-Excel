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
from src.schemas.target_schema import get_schema
from custom_customer_schema import CUSTOM_CUSTOMER_SCHEMA

# Register Custom Schema
SCHEMA_REGISTRY["custom_customer"] = CUSTOM_CUSTOMER_SCHEMA

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
    uploaded_files = st.file_uploader("Upload Excel, CSV or XML file", type=['xlsx', 'csv', 'xml'], accept_multiple_files=True)
    
    if uploaded_files:
        # Save uploaded files temporarily
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        for uploaded_file in uploaded_files:
            file_path = temp_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        st.success(f"Uploaded {len(uploaded_files)} file(s).")
        
        # Global Transformation Inputs
        selected_schema = None
        user_instruction = None
        user_hint = None
        
        if mode == "Standard (Predefined Schema)":
            st.subheader("Standard Transformation")
            schema_names = list(SCHEMA_REGISTRY.keys())
            selected_schema = st.selectbox("Select Target Schema", schema_names, index=schema_names.index("custom_customer") if "custom_customer" in schema_names else 0)
            
        elif mode == "Flexible (Natural Language)":
            st.subheader("Flexible Transformation")
            user_instruction = st.text_area("Describe the transformation you want:", placeholder="Example: Add a column called 'Premium' that is True if Age > 30, and filter only Premium users.")
            
        else: # Intelligent Normalization
            st.subheader("Intelligent Normalization")
            st.info("This mode uses AI to detect merged cells, grouped headers, and nested structures (like Ledgers) and converts them into a flat table.")
            user_hint = st.text_area("Optional Hint (e.g., 'Look for Ledger names in bold'):", height=70)
            
        # Global Execution Button (Intelligent Routing)
        start_processing = False
        if st.button("🚀 Run Agent on Relevant Files", type="primary"):
            start_processing = True

        st.divider()

        if start_processing and uploaded_files:
            # Determine which files to process
            files_to_process = []
            
            # For Standard/Normalization, user might expect all or specific files. 
            # For Flexible, we definitely use the router.
            # Let's use router for Flexible, and maybe all/router for others depending on context.
            # To keep it simple and smart: Always try routing if there's a prompt, else all?
            # User request specifically mentioned "write a prompt... applicable to respective file".
            
            from src.agents.file_router import FileRouterAgent
            router = FileRouterAgent()
            
            with st.spinner("🤖 Identifying relevant files..."):
                # Use the instruction/hint/schema as the 'prompt' context
                context_prompt = ""
                if mode == "Flexible (Natural Language)":
                    context_prompt = user_instruction or "Process data"
                elif mode == "Intelligent Normalization":
                    context_prompt = f"Normalize data. Hint: {user_hint}"
                else: 
                    context_prompt = f"Transform using schema: {selected_schema}"
                
                # Get list of Path objects from temp_dir
                available_paths = [temp_dir / f.name for f in uploaded_files]
                
                # Extract schema info for context-aware routing
                file_schemas = {}
                from src.utils.excel_loader import ExcelLoader
                
                for path in available_paths:
                    try:
                        loader = ExcelLoader(str(path))
                        schema_info = {}
                        
                        if loader.is_excel:
                            schema_info["sheet_names"] = loader.get_sheet_names()
                            # Optional: Extract columns from the first sheet or all sheets?
                            # For speed, let's just get columns from the first sheet for now, 
                            # or strictly rely on sheet names if that's the user's focus.
                            # But better to get columns from at least the first sheet.
                            df_sample = loader.load_sample(n_rows=5)
                            schema_info["columns"] = list(df_sample.columns)[:50] # Truncate to avoid huge prompts
                        else:
                            # CSV/XML
                            df_sample = loader.load_sample(n_rows=5)
                            schema_info["columns"] = list(df_sample.columns)[:50] # Truncate to avoid huge prompts
                            
                        file_schemas[path.name] = schema_info
                    except Exception as e:
                        # If loading fails, just skip schema info for this file
                        print(f"Schema extraction failed for {path.name}: {e}")
                
                relevant_paths = router.select_files(available_paths, context_prompt, schemas=file_schemas)
                
                if not relevant_paths:
                    st.warning("No relevant files found for your request.")
                    st.session_state.relevant_files = [] # Clear if none found
                else:
                    st.session_state.relevant_files = [p.name for p in relevant_paths]
                    st.success(f"Selected {len(relevant_paths)} file(s): {', '.join([p.name for p in relevant_paths])}")
                    
                    # Execution Loop
                    progress_bar = st.progress(0)
                    for i, file_path in enumerate(relevant_paths):
                        st.write(f"### Processing: `{file_path.name}`...")
                        
                        try:
                            if mode == "Standard (Predefined Schema)":
                                run_standard_transform(str(file_path), selected_schema)
                            elif mode == "Flexible (Natural Language)":
                                run_flexible_transform(str(file_path), user_instruction or "Convert the data into JSON and Excel formats.")
                            else:
                                run_normalization(str(file_path), user_hint)
                        except Exception as e:
                            st.error(f"Failed to process {file_path.name}: {e}")
                            
                        progress_bar.progress((i + 1) / len(relevant_paths))
                    
                    st.success("All tasks completed!")

        # Create tabs for each file
        # Use session state to filter files if a selection has been made
        displayed_files = uploaded_files
        if 'relevant_files' in st.session_state and st.session_state.relevant_files:
            # Filter uploaded_files to only those in relevant_files
            displayed_files = [f for f in uploaded_files if f.name in st.session_state.relevant_files]
            
            if len(displayed_files) < len(uploaded_files):
                st.info(f"Showing {len(displayed_files)} relevant file(s) out of {len(uploaded_files)} uploaded.")

        file_tabs = st.tabs([f.name for f in displayed_files])
        
        for idx, uploaded_file in enumerate(displayed_files):
            with file_tabs[idx]:
                file_path = temp_dir / uploaded_file.name
                
                # Preview Section
                try:
                    from src.utils.excel_loader import ExcelLoader
                    loader = ExcelLoader(str(file_path))
                    
                    st.subheader("Data Preview")
                    
                    # Sheet selection for Excel
                    if loader.is_excel:
                        sheet_names = loader.get_sheet_names()
                        for sheet in sheet_names:
                            st.markdown(f"**Sheet:** `{sheet}`")
                            df = loader.load_sample(n_rows=10, sheet_name=sheet)
                            st.dataframe(df)
                            st.write("---")
                    else:
                        df = loader.load_sample(n_rows=15)
                        st.dataframe(df.head())
                    
                except Exception as e:
                    st.error(f"Error reading file: {e}")
                    continue

                st.divider()
                
                # Preview Only - Manual Execution Removed per user request
                pass

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
    
    href = f'<a href="data:{mime};base64,{b64}" download="{path.name}" style="button">Download Transformed File</a>'
    st.markdown(href, unsafe_allow_html=True)
    
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
