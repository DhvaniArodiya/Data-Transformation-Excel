import streamlit as st
import pandas as pd
import numpy as np
import re
import io
import sys
import os
from pathlib import Path
from datetime import datetime
import base64
import subprocess
import time
import anthropic
import json

# Add parent directory to sys.path to import src
current_dir = Path(__file__).parent.absolute()
if str(current_dir.parent) not in sys.path:
    sys.path.insert(0, str(current_dir.parent))

try:
    from src.config import settings
except ImportError:
    settings = None

# Page configuration
st.set_page_config(
    page_title="AI Ledger Normalizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        margin: 1rem 0;
    }
    .ai-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e7f3ff;
        border: 2px solid #0066cc;
        color: #004085;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.environ.get("API_KEY") or (settings.anthropic_api_key if settings else None)
if 'endpoint' not in st.session_state:
    st.session_state.endpoint = os.environ.get("ENDPOINT") or (settings.anthropic_endpoint if settings else "https://api.anthropic.com")
if 'deployment_name' not in st.session_state:
    st.session_state.deployment_name = os.environ.get("DEPLOYMENT_NAME") or (settings.deployment_name if settings else "claude-3-5-sonnet-20240620")
if 'ai_client' not in st.session_state or st.session_state.ai_client is None:
    if st.session_state.api_key:
        try:
            client_kwargs = {"api_key": st.session_state.api_key}
            if st.session_state.endpoint and "api.anthropic.com" not in st.session_state.endpoint:
                client_kwargs["base_url"] = st.session_state.endpoint
            st.session_state.ai_client = anthropic.Anthropic(**client_kwargs)
        except:
            st.session_state.ai_client = None


def parse_date(date_str):
    """Convert various date formats to ISO format YYYY-MM-DD"""
    if pd.isna(date_str) or date_str == '' or date_str == 'nan':
        return None
    
    try:
        # Try DD-MMM-YY format (e.g., 01-Apr-25)
        date_obj = datetime.strptime(str(date_str), '%d-%b-%y')
        return date_obj.strftime('%Y-%m-%d')
    except:
        try:
            # Try DD-MMM-YYYY format
            date_obj = datetime.strptime(str(date_str), '%d-%b-%Y')
            return date_obj.strftime('%Y-%m-%d')
        except:
            try:
                # Try standard date parsing
                date_obj = pd.to_datetime(date_str)
                return date_obj.strftime('%Y-%m-%d')
            except:
                return None


def clean_numeric(value):
    """Remove commas, Dr/Cr text and convert to float"""
    if pd.isna(value) or value == '' or value == 'nan':
        return None
    
    try:
        # Remove commas, spaces, Dr, Cr
        cleaned = str(value).replace(',', '').replace(' ', '')
        cleaned = cleaned.replace('Dr', '').replace('Cr', '').strip()
        return float(cleaned) if cleaned else None
    except:
        return None


def normalize_ledger_to_3sheets(uploaded_file):
    """
    Normalize ledger data into 3 structured sheets:
    1. ledger_master (static data)
    2. ledger_transactions (dynamic data)
    3. report_metadata (report context)
    """
    
    # Load raw data
    # Read with header=None to handle arbitrary starting rows
    df_raw = pd.read_excel(uploaded_file, header=None)
    
    # Initialize output lists
    ledger_master_data = []
    transaction_data = []
    metadata_data = []
    
    # Counters
    current_ledger_id_counter = 1
    transaction_id_counter = 1
    report_id_counter = 1
    
    # Global Metadata extraction placeholders
    period_start = None
    period_end = None
    
    # Patterns
    date_pattern = re.compile(r'\d{1,2}-[A-Za-z]{3}-\d{2,4}') # e.g. 01-Apr-2023
    gst_pattern = re.compile(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}')
    
    # State tracking
    current_ledger_name = None
    ledger_name_to_id_map = {}
    
    # Iterate through rows
    i = 0
    max_rows = len(df_raw)
    
    while i < max_rows:
        row = df_raw.iloc[i]
        # Convert row to list of strings, handling NaN
        row_values = [str(v).strip() if pd.notna(v) and str(v).lower() != 'nan' else '' for v in row]
        first_cell = row_values[0] if row_values else ''
        combined_row = ' '.join(row_values).strip()
        
        # 1. Skip strictly empty rows
        if not combined_row:
            i += 1
            continue
            
        # 2. Extract Report Metadata (Date Range) from headers
        # Look for "From ... To ..." pattern usually at top or matching date pattern twice
        if not period_start and i < 20: 
            dates_found = date_pattern.findall(combined_row)
            if len(dates_found) >= 2 and ('to' in combined_row.lower() or '-' in combined_row):
                period_start = parse_date(dates_found[0])
                period_end = parse_date(dates_found[1])
        
        # 3. Detect "Ledger: <Name>" or similar Start of Ledger Block
        is_ledger_header = False
        extracted_ledger_name = None
        
        # Check standard Tally/Report formats
        if 'Ledger:' in first_cell or first_cell.startswith("Account Name"):
            if ':' in first_cell:
                parts = first_cell.split(':', 1)
                if len(parts) > 1:
                    extracted_ledger_name = parts[1].strip()
            else:
                # Might be in next column
                extracted_ledger_name = row_values[1] if len(row_values) > 1 else ''
            is_ledger_header = True
        elif 'Ledger Account :' in combined_row: 
             # Fallback for looser match
             match = re.search(r'Ledger Account\s*:\s*(.*)', combined_row, re.IGNORECASE)
             if match:
                 extracted_ledger_name = match.group(1).strip()
                 is_ledger_header = True

        if is_ledger_header and extracted_ledger_name:
            current_ledger_name = extracted_ledger_name
            
            # --- Extract Ledger Master Details ---
            # Try to capture Address, GST, etc. from immediate following rows
            
            address_lines = []
            gst_no = None
            
            # Scan a few rows down for address/GST until we hit a table header
            j = i + 1
            has_table_header = False
            while j < min(i + 12, max_rows):
                r_vals = [str(v).strip() if pd.notna(v) and str(v).lower() != 'nan' else '' for v in df_raw.iloc[j]]
                r_comb = ' '.join(r_vals).lower()
                
                # Stop if we hit table header or date
                if ('date' in r_comb and 'particulars' in r_comb) or ('vch' in r_comb and 'type' in r_comb):
                    has_table_header = True
                    break
                
                if date_pattern.match(r_vals[0] if r_vals else ''):
                    # Start of transactions
                    break

                # Check for GST
                gst_match = gst_pattern.search(' '.join(r_vals)) # Search in original case (using r_vals from df which we rebuilt? no, r_comb is lower)
                # Re-get original string for regex
                orig_row_str = ' '.join([str(v) for v in df_raw.iloc[j] if pd.notna(v)])
                gst_match_orig = gst_pattern.search(orig_row_str)
                if gst_match_orig:
                    gst_no = gst_match_orig.group(0)
                
                # Collect Address (ignore empty, ignore GST line if it's ONLY GST)
                clean_parts = []
                for v in r_vals:
                    if v and 'gst' not in v.lower() and 'ledger' not in v.lower() and v != ':' and v != extracted_ledger_name:
                        # Check if it's not just the ledger name repeated
                        clean_parts.append(v)
                
                if clean_parts:
                     # Heuristic: address lines are usually not key-value pairs like "Email: ..." (ignore for now or include?)
                     # Let's include everything as address for now, user can clean.
                     address_lines.append(', '.join(clean_parts))
                
                j += 1
            
            full_address = ', '.join(address_lines)
            
            # Extract City/State if possible
            city = None
            state = None
            if full_address:
                addr_parts = [p.strip() for p in full_address.split(',')]
                if len(addr_parts) >= 2:
                    # Very rough heuristic
                    pass

            # Determine Ledger Type
            ledger_type = 'Party'
            if 'bank' in current_ledger_name.lower() or 'hdfc' in current_ledger_name.lower() or 'icici' in current_ledger_name.lower() or 'sbi' in current_ledger_name.lower():
                ledger_type = 'Bank'
            
            # Bank specific fields
            bank_name = current_ledger_name if ledger_type == 'Bank' else None
            account_no = None 
            ifsc_code = None

            # Uniqueness check
            if current_ledger_name not in ledger_name_to_id_map:
                ledger_id = current_ledger_id_counter
                ledger_name_to_id_map[current_ledger_name] = ledger_id
                
                ledger_master_data.append({
                    'ledger_id': ledger_id,
                    'ledger_name': current_ledger_name,
                    'ledger_type': ledger_type,
                    'address': full_address,
                    'city': city,
                    'state': state,
                    'bank_name': bank_name,
                    'account_no': account_no,
                    'ifsc_code': ifsc_code,
                    'gst_no': gst_no
                })
                current_ledger_id_counter += 1
            
            # Skip the rows we processed? No, let the main loop continue, it will hit skip logic or headers.
            # But we should ensure we don't re-process headers as transactions.
            # i = j - 1 ? No, safer to just continue.
        
        # 4. Parse Transactions
        # Context: We have a current_ledger_name
        if current_ledger_name and date_pattern.match(first_cell):
            trans_date = parse_date(first_cell)
            
            # Identify columns
            values = [v for v in row_values if v]
            
            # Right-to-Left scan for Numerics
            numerics = []
            non_numerics = []
            
            for v in reversed(values):
                val_num = clean_numeric(v)
                if val_num is not None:
                    numerics.append(val_num)
                else:
                    non_numerics.append(v)
            
            numerics.reverse() 
            non_numerics.reverse() 
            
            debit = None
            credit = None
            balance_val = None
            
            # Logic: valid transaction usually has at least 1 numeric
            if not numerics:
                # Might be a narration-only line? "No merged cells" -> "No title rows inside data".
                # If it's a narration continuation, we should append to previous? 
                # User says "One row = one transaction". 
                # We will skip lines that don't look like full transactions (no amount).
                i += 1
                continue

            if len(numerics) >= 3:
                # Debit, Credit, Balance
                debit = numerics[0]
                credit = numerics[1]
                balance_val = numerics[2]
            elif len(numerics) == 2:
                # Debit, Credit?
                debit = numerics[0]
                credit = numerics[1]
                balance_val = abs(debit - credit) # Calculated
            elif len(numerics) == 1:
                # Single amount (Debit OR Credit)
                amount = numerics[0]
                # Context heuristic
                is_cr = 'cr' in combined_row.lower() or 'receipt' in combined_row.lower() or 'sales' in combined_row.lower()
                if is_cr:
                    credit = amount
                    debit = 0.0
                else:
                    debit = amount
                    credit = 0.0
                balance_val = amount
            
            # Ensure float
            debit = float(debit) if debit else 0.0
            credit = float(credit) if credit else 0.0
            
            # Extract Text Fields
            text_values = []
            for v in non_numerics:
                if parse_date(v) == trans_date:
                    continue 
                text_values.append(v)
            
            voucher_type = None
            voucher_no = None
            
            vch_types = ['payment', 'receipt', 'contra', 'journal', 'sales', 'purchase', 'credit note', 'debit note', 'invoice']
            
            temp_narration = []
            for v in text_values:
                v_lower = v.lower()
                if v_lower in vch_types:
                    voucher_type = v
                elif v.isdigit() and len(v) < 10 and not voucher_no: 
                    voucher_no = v
                else:
                    temp_narration.append(v)
            
            narration = ' '.join(temp_narration)
            
            b_type = 'Dr' if debit >= credit else 'Cr'
            
            ledger_id = ledger_name_to_id_map.get(current_ledger_name)
            
            transaction_data.append({
                'transaction_id': transaction_id_counter,
                'ledger_id': ledger_id,
                'transaction_date': trans_date,
                'voucher_type': voucher_type,
                'voucher_no': voucher_no,
                'narration': narration,
                'debit': debit,
                'credit': credit,
                'balance': balance_val,
                'balance_type': b_type
            })
            
            transaction_id_counter += 1
        
        i += 1
        
    # --- Final Construction ---
    
    for l_name, l_id in ledger_name_to_id_map.items():
        metadata_data.append({
            'report_id': report_id_counter,
            'ledger_id': l_id,
            'period_start': period_start,
            'period_end': period_end,
            'generated_on': datetime.now().strftime('%Y-%m-%d')
        })
        report_id_counter += 1

    # Create DataFrames
    df_ledger_master = pd.DataFrame(ledger_master_data)
    df_transactions = pd.DataFrame(transaction_data)
    df_metadata = pd.DataFrame(metadata_data)
    
    # Enforce Columns (Add missing if empty)
    cols_master = ['ledger_id', 'ledger_name', 'ledger_type', 'address', 'city', 'state', 'bank_name', 'account_no', 'ifsc_code', 'gst_no']
    cols_trans = ['transaction_id', 'ledger_id', 'transaction_date', 'voucher_type', 'voucher_no', 'narration', 'debit', 'credit', 'balance', 'balance_type']
    cols_meta = ['report_id', 'ledger_id', 'period_start', 'period_end', 'generated_on']
    
    # Fill missing columns
    for col in cols_master:
        if col not in df_ledger_master.columns:
            df_ledger_master[col] = None
            
    for col in cols_trans:
        if col not in df_transactions.columns:
            df_transactions[col] = None
            
    for col in cols_meta:
        if col not in df_metadata.columns:
            df_metadata[col] = None

    # Reorder and Select
    if not df_ledger_master.empty:
        df_ledger_master = df_ledger_master[cols_master]
    if not df_transactions.empty:
        df_transactions = df_transactions[cols_trans]
    if not df_metadata.empty:
        df_metadata = df_metadata[cols_meta]
            
    stats = {
        'ledgers': len(df_ledger_master),
        'transactions': len(df_transactions),
        'period_start': period_start,
        'period_end': period_end
    }
    
    return df_ledger_master, df_transactions, df_metadata, stats


def generate_ai_normalization_script(file_path, user_hint=""):
    """Use Claude AI to generate normalization script following the 3-sheet schema"""
    if not st.session_state.ai_client:
        return None
    
    try:
        # Read sample data
        df_sample = pd.read_excel(file_path, header=None, nrows=25)
        sample_data = df_sample.to_string()
        
        # System prompt with strict schema requirements
        system_prompt = """You are a data-engineering assistant.

Your task is to take a ledger-style Excel file (human-readable accounting report)
and convert it into a fully normalized, machine-readable structured format
that can be safely converted into JSON without errors.

Follow these rules strictly:

────────────────────────────────────
1. GENERAL PRINCIPLES
────────────────────────────────────
• Never treat report-style Excel as data.
• One row must represent exactly one entity.
• No merged cells.
• No title rows inside data.
• No blank header columns.
• Column names must be lowercase, snake_case, and JSON-friendly.
• Numeric columns must contain only numbers.
• Leave missing values empty (null in JSON).

────────────────────────────────────
2. SPLIT THE INPUT INTO 3 STRUCTURED SHEETS
────────────────────────────────────

Create exactly three sheets:

SHEET 1: ledger_master (STATIC DATA)
Structure: ledger_id | ledger_name | ledger_type | address | city | state | bank_name | account_no | ifsc_code | gst_no

SHEET 2: ledger_transactions (DYNAMIC DATA)
Structure: transaction_id | ledger_id | transaction_date | voucher_type | voucher_no | narration | debit | credit | balance | balance_type

SHEET 3: report_metadata (REPORT CONTEXT)
Structure: report_id | ledger_id | period_start | period_end | generated_on

────────────────────────────────────
3. DATA EXTRACTION RULES
────────────────────────────────────
• Remove titles such as company name, ledger account, and date ranges from rows.
• Convert all dates to ISO format (YYYY-MM-DD).
• Remove commas, "Dr"/"Cr", and text from numeric fields.
• Do not infer missing values — leave them empty.
• Repeat values explicitly instead of using visual grouping.

Generate COMPLETE, EXECUTABLE Python code that processes the input file and creates these 3 sheets."""

        # Use absolute path for output to avoid confusion
        output_abs_dir = Path(__file__).parent.absolute() / "output"
        output_abs_dir.mkdir(exist_ok=True)
        timestamp = int(time.time())
        expected_output_filename = f"normalized_3sheets_{timestamp}.xlsx"
        expected_output_path = output_abs_dir / expected_output_filename

        user_prompt = f"""Generate Python code to normalize this ledger data:

INPUT FILE: {file_path}
OUTPUT FILE (SAVE HERE): {str(expected_output_path)}

SAMPLE DATA:
{sample_data}

USER REQUIREMENTS: {user_hint if user_hint else "Standard normalization to 3-sheet format"}

The code must:
1. Parse the Excel file
2. Extract ledger master data (ledger_id, ledger_name, ledger_type, address, city, state, bank_name, account_no, ifsc_code, gst_no)
3. Extract all transactions (transaction_id, ledger_id, transaction_date, voucher_type, voucher_no, narration, debit, credit, balance, balance_type)
4. Extract report metadata (report_id, ledger_id, period_start, period_end, generated_on)
5. Save to {str(expected_output_path)} with exactly 3 sheets named 'ledger_master', 'ledger_transactions', 'report_metadata'
6. Ensure JSON-ready format (convert all dates to YYYY-MM-DD strings and numeric fields to float/int)
7. Print 'SUCCESS' at the very end.

Return ONLY executable Python code."""

        # Call AI API
        model_name = st.session_state.deployment_name
        
        message = st.session_state.ai_client.messages.create(
            model=model_name,
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract code
        response_text = message.content[0].text
        
        if "```python" in response_text:
            code = response_text.split("```python")[1].split("```")[0].strip()
        elif "```" in response_text:
            code = response_text.split("```")[1].split("```")[0].strip()
        else:
            code = response_text.strip()
        
        return code
    
    except Exception as e:
        st.error(f"❌ AI Error: {str(e)}")
        return None


def run_ai_normalization(file_path, user_hint):
    """Run AI-powered normalization with 3-sheet schema"""
    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
    st.markdown("### 🤖 AI Agent Processing (3-Sheet Schema)")
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.spinner("⚙️ AI generating normalization script..."):
        script_code = generate_ai_normalization_script(file_path, user_hint)
        
        if not script_code:
            st.error("❌ Failed to generate script")
            return None
        
        with st.expander("📝 AI-Generated Script", expanded=False):
            st.code(script_code, language='python')
    
    with st.spinner("🚀 Executing script..."):
        # Save script
        output_dir = Path(__file__).parent.absolute() / "output"
        output_dir.mkdir(exist_ok=True)
        script_path = output_dir / f"ai_normalize_3sheet_{int(time.time())}.py"
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_code)
        
        # Execute
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.absolute())
        )
        
        # Log regardless of success for debugging
        if result.stdout or result.stderr:
            with st.expander("📋 Execution Log"):
                if result.stdout:
                    st.text("STDOUT:")
                    st.code(result.stdout)
                if result.stderr:
                    st.text("STDERR:")
                    st.code(result.stderr)

        if result.returncode == 0:
            # Look for the absolute path in the script code to find what it saved
            # Or just check the output folder for the newest file
            output_files = list(output_dir.glob("normalized_3sheets_*.xlsx"))
            if output_files:
                latest_file = max(output_files, key=lambda p: p.stat().st_mtime)
                # Check if it was created in the last 2 minutes
                if time.time() - latest_file.stat().st_mtime < 120:
                    st.success("✅ Script executed successfully!")
                    return str(latest_file)
            
            st.warning("⚠️ Script completed but no matching output file was detected in 'output/'")
            return None
        else:
            st.error("❌ Execution failed")
            return None


def show_download_button(file_path, button_text="Download Normalized Data"):
    """Create download button"""
    path = Path(file_path)
    if not path.exists():
        st.error("File not found.")
        return

    with open(path, "rb") as f:
        bytes_data = f.read()
    
    st.download_button(
        label=f"📥 {button_text}",
        data=bytes_data,
        file_name=path.name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 AI Ledger Normalizer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">JSON-Ready | Database-Ready | API-Ready | ML-Ready</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Mode Selection
        mode = st.radio(
            "Processing Mode",
            [
                "🚀 Built-in Normalizer",
                "🤖 AI Agent (Azure/Claude)"
            ]
        )

        st.divider()

        # Azure / Anthropic API Key
        st.subheader("🔑 AI Configuration")
        
        api_key_input = st.text_input(
            "API Key",
            type="password",
            value=st.session_state.api_key if st.session_state.api_key else "",
            help="Enter your Anthropic or Azure API key"
        )
        
        endpoint_input = st.text_input(
            "Endpoint",
            value=st.session_state.endpoint if st.session_state.endpoint else "",
            help="Azure endpoint (ends with /anthropic/)"
        )
        
        deployment_input = st.text_input(
            "Model / Deployment Name",
            value=st.session_state.deployment_name if st.session_state.deployment_name else "",
            help="Deployment name for Azure or model name for Anthropic"
        )
        
        if st.button("Update AI Config"):
            st.session_state.api_key = api_key_input
            st.session_state.endpoint = endpoint_input
            st.session_state.deployment_name = deployment_input
            
            try:
                # Initialize client with optional base_url
                client_kwargs = {"api_key": api_key_input}
                if endpoint_input and "api.anthropic.com" not in endpoint_input:
                    client_kwargs["base_url"] = endpoint_input
                
                st.session_state.ai_client = anthropic.Anthropic(**client_kwargs)
                st.success("✅ AI configured!")
                
                # Update environment for sub-scripts if needed
                os.environ["API_KEY"] = api_key_input
                os.environ["ENDPOINT"] = endpoint_input
                os.environ["DEPLOYMENT_NAME"] = deployment_input
            except Exception as e:
                st.error(f"❌ Configuration error: {str(e)}")
        
        st.divider()
        
        st.header("📋 Output Schema")
        st.markdown("""
        **3 Structured Sheets:**
        
        **1️⃣ ledger_master**
        - ledger_id, ledger_name
        - ledger_type, address
        - city, state, gst_no
        
        **2️⃣ ledger_transactions**
        - transaction_id, ledger_id
        - transaction_date, voucher_type
        - debit, credit, balance
        
        **3️⃣ report_metadata**
        - report_id, period_start
        - period_end, generated_on
        """)
        
        st.divider()
        
        st.header("✨ Features")
        st.markdown("""
        ✅ JSON-ready format
        ✅ Database-normalized
        ✅ No merged cells
        ✅ ISO date formats
        ✅ Clean numeric fields
        ✅ Lowercase snake_case
        """)
    
    # Main content
    uploaded_file = st.file_uploader(
        "📤 Upload Ledger Excel File",
        type=['xlsx', 'xls'],
        help="Upload human-readable ledger report"
    )
    
    if uploaded_file:
        # Save file
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        file_path = temp_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # File info
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**📄 File:** {uploaded_file.name}")
        with col2:
            st.write(f"**📊 Size:** {uploaded_file.size / 1024:.2f} KB")
        with col3:
            api_status = "🟢 AI Ready" if st.session_state.ai_client else "⚪ Built-in Only"
            st.write(f"**Status:** {api_status}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Preview
        with st.expander("📄 Raw Data Preview"):
            try:
                df_preview = pd.read_excel(file_path, header=None, nrows=15)
                st.dataframe(df_preview, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")
        
        # Process based on mode
        if "Built-in" in mode:
            if st.button("🚀 Normalize to 3-Sheet Format", type="primary", use_container_width=True):
                with st.spinner("🔄 Normalizing data..."):
                    df_master, df_trans, df_meta, stats = normalize_ledger_to_3sheets(file_path)
                    
                    if df_master is not None and not df_master.empty:
                        st.markdown('<div class="success-box">', unsafe_allow_html=True)
                        st.markdown("### ✅ Normalization Complete!")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Stats
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Ledgers", stats['ledgers'])
                        with col2:
                            st.metric("Transactions", stats['transactions'])
                        with col3:
                            st.metric("Period Start", stats['period_start'] or 'N/A')
                        with col4:
                            st.metric("Period End", stats['period_end'] or 'N/A')
                        
                        # Tabs for each sheet
                        tab1, tab2, tab3, tab4 = st.tabs([
                            "📊 Ledger Master",
                            "💰 Transactions",
                            "📋 Metadata",
                            "🔍 JSON Preview"
                        ])
                        
                        with tab1:
                            st.subheader("Sheet 1: ledger_master")
                            st.dataframe(df_master, use_container_width=True, height=400)
                            st.caption(f"Total Ledgers: {len(df_master)}")
                        
                        with tab2:
                            st.subheader("Sheet 2: ledger_transactions")
                            st.dataframe(df_trans, use_container_width=True, height=400)
                            st.caption(f"Total Transactions: {len(df_trans)}")
                            
                            if not df_trans.empty:
                                col1, col2 = st.columns(2)
                                with col1:
                                    total_debit = df_trans['debit'].sum()
                                    st.metric("Total Debit", f"₹{total_debit:,.2f}")
                                with col2:
                                    total_credit = df_trans['credit'].sum()
                                    st.metric("Total Credit", f"₹{total_credit:,.2f}")
                        
                        with tab3:
                            st.subheader("Sheet 3: report_metadata")
                            st.dataframe(df_meta, use_container_width=True, height=200)
                        
                        with tab4:
                            st.subheader("JSON Conversion Test")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Ledger Master JSON:**")
                                try:
                                    json_master = df_master.to_json(orient='records', indent=2)
                                    st.code(json_master[:500] + "..." if len(json_master) > 500 else json_master, language='json')
                                    st.success("✅ JSON conversion successful")
                                except Exception as e:
                                    st.error(f"❌ JSON error: {e}")
                            
                            with col2:
                                st.write("**Transactions JSON:**")
                                try:
                                    json_trans = df_trans.to_json(orient='records', indent=2)
                                    st.code(json_trans[:500] + "..." if len(json_trans) > 500 else json_trans, language='json')
                                    st.success("✅ JSON conversion successful")
                                except Exception as e:
                                    st.error(f"❌ JSON error: {e}")
                        
                        # Download
                        st.divider()
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_master.to_excel(writer, sheet_name='ledger_master', index=False)
                            df_trans.to_excel(writer, sheet_name='ledger_transactions', index=False)
                            df_meta.to_excel(writer, sheet_name='report_metadata', index=False)
                        output.seek(0)
                        
                        st.download_button(
                            label="📥 Download 3-Sheet Normalized Excel",
                            data=output,
                            file_name=f"normalized_3sheets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ No data extracted")
        
        else:  # AI Agent Mode
            if not st.session_state.ai_client:
                st.warning("⚠️ Please enter API Key in sidebar for AI Agent Mode")
            else:
                user_hint = st.text_area(
                    "💡 Optional Instructions for AI",
                    placeholder="Example: Extract GST numbers from addresses, classify ledgers as Bank/Party/Expense...",
                    height=100
                )
                
                if st.button("🤖 Run AI Normalization", type="primary", use_container_width=True):
                    output_file = run_ai_normalization(str(file_path), user_hint)
                    
                    if output_file:
                        st.markdown('<div class="success-box">', unsafe_allow_html=True)
                        st.markdown("### ✅ AI Normalization Complete!")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        show_download_button(output_file, "Download AI-Normalized 3-Sheet Excel")
                        
                        # Preview results
                        try:
                            xl_file = pd.ExcelFile(output_file)
                            
                            tab1, tab2, tab3 = st.tabs(["Ledger Master", "Transactions", "Metadata"])
                            
                            def safe_df(df):
                                # Convert all objects (like datetimes) to string for Arrow compatibility
                                for col in df.columns:
                                    if df[col].dtype == 'object' or 'date' in col.lower():
                                        df[col] = df[col].astype(str)
                                return df

                            with tab1:
                                df_m = pd.read_excel(output_file, sheet_name='ledger_master')
                                st.dataframe(safe_df(df_m), use_container_width=True)
                            
                            with tab2:
                                df_t = pd.read_excel(output_file, sheet_name='ledger_transactions')
                                st.dataframe(safe_df(df_t.head(50)), use_container_width=True)
                            
                            with tab3:
                                df_md = pd.read_excel(output_file, sheet_name='report_metadata')
                                st.dataframe(safe_df(df_md), use_container_width=True)
                        
                        except Exception as e:
                            st.warning(f"Preview error: {e}")
    
    else:
        # Landing page
        st.info("👆 Upload a ledger Excel file to begin normalization")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🚀 Built-in Normalizer")
            st.markdown("""
            **Fast & Reliable**
            - No API key needed
            - Instant processing
            - 3-sheet structured output
            - JSON-ready format
            
            **Perfect for:**
            - Standard ledger formats
            - Quick conversions
            - Batch processing
            """)
        
        with col2:
            st.markdown("### 🤖 AI Agent")
            st.markdown("""
            **Intelligent & Adaptive**
            - Claude AI-powered
            - Handles complex formats
            - Custom script generation
            - Advanced extraction
            
            **Perfect for:**
            - Unusual formats
            - Custom requirements
            - Complex hierarchies
            """)
        
        st.divider()
        
        st.subheader("📊 Output Schema (3 Sheets)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Sheet 1: ledger_master**
            ```
            ledger_id
            ledger_name
            ledger_type
            address
            city
            state
            bank_name
            account_no
            ifsc_code
            gst_no
            ```
            """)
        
        with col2:
            st.markdown("""
            **Sheet 2: ledger_transactions**
            ```
            transaction_id
            ledger_id
            transaction_date
            voucher_type
            voucher_no
            narration
            debit
            credit
            balance
            balance_type
            ```
            """)
        
        with col3:
            st.markdown("""
            **Sheet 3: report_metadata**
            ```
            report_id
            ledger_id
            period_start
            period_end
            generated_on
            ```
            """)
        
        st.divider()
        
        with st.expander("📖 Input Format Example"):
            st.code("""
FDS

Ledger Account

1-Apr-25 to 28-Aug-25

Ledger: ABC COMPANY LTD    1-Apr-25 to 28-Aug-25
        123 Main St, Mumbai, Maharashtra - 400001

Date        Particulars              Vch Type  Vch No.  Debit     Credit
01-Apr-25   By  Opening Balance                          1000.00
15-Apr-25   To  Bank Payment         Payment   101      500.00
20-Apr-25   By  Sales Invoice        Sales     202                2000.00
            """, language="text")
        
        with st.expander("✅ Data Quality Guarantees"):
            st.markdown("""
            - ✅ **JSON-ready**: `df.to_json(orient="records")` works perfectly
            - ✅ **Database-ready**: Normalized schema with foreign keys
            - ✅ **API-ready**: Clean column names, proper data types
            - ✅ **ML-ready**: Structured format for analytics pipelines
            - ✅ **No merged cells**: Each row is one complete record
            - ✅ **ISO dates**: All dates in YYYY-MM-DD format
            - ✅ **Clean numbers**: No commas, Dr/Cr text removed
            - ✅ **snake_case**: All column names lowercase with underscores
            """)


if __name__ == "__main__":
    main()