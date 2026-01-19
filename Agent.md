# AGENT.md — AI Excel Transformation System Architecture

## 1. System Overview

**Mission:** Build an autonomous, resilience-first SaaS that transforms arbitrary, messy customer Excel files into strict, standardized enterprise formats (ERP/CRM schemas) with minimal human intervention.

**Core Philosophy:**

* **Declarative over Imperative:** Agents generate **JSON Plans**, not Python code.
* **Prebuilt over Generated:** Use a library of tested, deterministic functions (95% of cases) instead of writing new code on the fly.
* **Accuracy over Speed:** Multi-step validation and "Ask Human" protocols for critical ambiguities.
* **Learning System:** Anonymized successful transformations are stored in a Global Library to speed up future onboardings.

---

## 2. Tech Stack & Configuration

### Azure AI Foundry Setup

**Language:** Python  
**SDK:** Anthropic SDK  
**Authentication:** Key Authentication

```python
from anthropic import AnthropicFoundry

client = AnthropicFoundry(
    api_key=api_key,
    base_url=endpoint
)
```

### Environment Variables

```env
ENDPOINT = "https://anydoctransform-resource.services.ai.azure.com/anthropic/"
DEPLOYMENT_NAME = "claude-opus-4-5"
API_KEY = "YOUR_API_KEY"
```

### Installation

```bash
pip install anthropic
```

### Basic API Call Example

```python
from anthropic import AnthropicFoundry

endpoint = "https://anydoctransform-resource.services.ai.azure.com/anthropic/"
deployment_name = "claude-opus-4-5"
api_key = "YOUR_API_KEY"

client = AnthropicFoundry(
    api_key=api_key,
    base_url=endpoint
)

message = client.messages.create(
    model=deployment_name,
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ],
    max_tokens=1024,
)

print(message.content)
```

---

## 3. Architecture & Agents

The system uses a **Hub-and-Spoke Multi-Agent Architecture** orchestrated by a Central Controller.

### 🤖 1. Central Orchestrator (The Boss)

* **Role:** Workflow Manager & State Machine.
* **Responsibility:**
  * Receives the source file and target schema.
  * Routes data between Schema, Planner, and Execution agents.
  * Manages the "Retry Budget" (max 3 retries per error).
  * Decides when to halt and ask the user a question (e.g., "Is 'Nm' First Name or Full Name?").
* **Tools:** State Management (Redis/DB), User Notification System.

### 🧠 2. Schema Analyst Agent

* **Role:** Data Detective.
* **Responsibility:**
  * Reads a **sample** (first 50 rows) of the source file.
  * Infers data types, semantic meanings (e.g., "This looks like an Indian Phone Number").
  * Identifies structural issues (merged cells, multi-row headers).
* **Output:** `Source_Schema_Analysis.json`

### 🏗️ 3. Transformation Planner Agent

* **Role:** The Architect.
* **Responsibility:**
  * Maps Source Columns → Target Columns.
  * Selects **Prebuilt Functions** to bridge gaps (e.g., `SPLIT_FULL_NAME`, `NORMALIZE_PHONE`).
  * Configures **Enrichment** (e.g., "Use Pincode API to fill City").
* **Output:** `Transformation_Plan.json`

### ⚙️ 4. Execution Engine (Deterministic)

* **Role:** The Worker (Not an LLM).
* **Responsibility:**
  * Reads the JSON Plan.
  * Executes high-performance Pandas/Polars operations.
  * Calls external APIs (Enrichment).
  * **No Code Generation:** Runs strictly defined functions from the Registry.

### 🛡️ 5. Validation Agent

* **Role:** QA Tester.
* **Responsibility:**
  * Checks the final output against the strict Target Schema.
  * Flags "Soft Errors" (warnings) vs "Hard Errors" (blockers).
  * Generates the Quality Report.

---

## 4. Data Flow Pipeline

1. **Ingestion:** Excel → CSV (Fast Load) or Excel MCP (if formatting needed).
2. **Sampling:** Extract first 50 rows + Metadata → Send to **Schema Agent**.
3. **Planning:** Schema Agent Output + Target Schema → **Planner Agent** → JSON Plan.
4. **Execution:** JSON Plan + Full Source CSV → **Execution Engine** → Result DataFrame.
5. **Validation:** Result DataFrame → **Validation Agent** → Success/Failure Report.
6. **Output:** Convert Result DataFrame → Final Excel File (Main Sheet + Error Sheet).

---

## 5. JSON Protocols (The "Language" of the Agents)

### A. Transformation Plan Schema

The Planner Agent must output this exact structure.

```json
{
  "transformation_id": "uuid-v4",
  "confidence_score": 0.95,
  "column_mappings": [
    {
      "source_col": "Cust_Name",
      "target_col": "first_name",
      "action": "transform",
      "transform_id": "tf_01"
    }
  ],
  "transformations": [
    {
      "id": "tf_01",
      "function": "SPLIT_FULL_NAME",
      "input_col": "Cust_Name",
      "output_cols": ["first_name", "last_name"],
      "params": {
        "delimiter": "auto",
        "handle_single_name": "first_name_only"
      }
    },
    {
      "id": "tf_02",
      "function": "NORMALIZE_PHONE",
      "input_col": "Mobile_No",
      "output_col": "phone",
      "params": {
        "region": "IN",
        "format": "E.164"
      }
    }
  ],
  "enrichments": [
    {
      "id": "en_01",
      "trigger_col": "Pincode",
      "target_cols": ["City", "State"],
      "api_service": "postal_code_lookup",
      "strategy": "cache_first_then_api"
    }
  ]
}
```

### B. Validation Report Schema

```json
{
  "status": "partial_success",
  "total_rows": 1000,
  "failed_rows": 23,
  "errors": [
    {
      "row_index": 45,
      "column": "Email",
      "issue": "Invalid Format",
      "value": "john.doe@gmail_com"
    }
  ],
  "quality_score": 97.7
}
```

---

## 6. Function Registry (The "Toolbox")

The Execution Engine supports these prebuilt, tested functions. The Agents merely **configure** them.

| Category | Function Name | Description | Parameters |
|----------|---------------|-------------|------------|
| **String** | `SPLIT_FULL_NAME` | Splits name into First/Middle/Last | `delimiter`, `culture` |
| | `REGEX_EXTRACT` | Extracts pattern (AI generates Regex) | `pattern`, `group_index` |
| | `CLEAN_WHITESPACE` | Trims and removes double spaces | `none` |
| **Date** | `SMART_DATE_PARSE` | Handles mixed formats (DD/MM vs MM/DD) | `ambiguity_preference` |
| | `FORMAT_DATE` | Standardizes to ISO8601 or custom | `target_format` |
| **Number** | `NORMALIZE_CURRENCY` | Removes symbols, fixes decimals | `currency_symbol` |
| **Logic** | `MAP_VALUES` | Maps categories (e.g., M->Male) | `mapping_dict`, `default` |
| | `CONDITIONAL_FILL` | If A is Empty, take B | `fallback_col` |
| **Enrich** | `LOOKUP_PINCODE` | Pincode -> City/State/Country | `provider`, `cache_ttl` |
| | `VALIDATE_GSTIN` | Checks checksum & status | `none` |
| | `AI_GENERATE` | **Fallback:** Uses LLM to generate value | `prompt_template` |

---

## 7. Prompt Engineering Strategy

### System Prompt: Transformation Planner

```text
You are an expert Data Engineer Agent. Your goal is to map a "Source Schema" to a "Target Schema" by selecting the best functions from the "Function Registry".

RULES:
1. PREFER PREBUILT: Always use a function from the registry if possible. Only use 'AI_GENERATE' for unstructured text enrichment.
2. BE EXPLICIT: For 'REGEX_EXTRACT', you must write the actual Regex pattern that fits the sample data provided.
3. DATA ENRICHMENT: If the target schema requires 'City'/'State' and the source has 'Pincode', generate an 'enrichment' step using 'LOOKUP_PINCODE'.
4. VALIDATION: If the target field is 'Email', automatically add a 'VALIDATE_EMAIL' step.

OUTPUT: Return ONLY the JSON Transformation Plan. No markdown, no conversational text.
```

### System Prompt: Schema Analyst

```text
You are a Data Inspector. Analyze the provided sample rows.
1. Infer the strict data type (Int, Float, Date, String).
2. Infer the semantic type (Phone, GSTIN, Name, Address).
3. Identify 'dirty' data (e.g., dates mixed with text).

Return a JSON summarizing the columns and their health.
```

---

## 8. Global Function Library (The "Memory")

To improve performance over time, the system maintains a database of successful transformation patterns.

* **Structure:** `source_pattern_signature` -> `transformation_plan_template`
* **Workflow:**
  1. Before calling the AI Planner, check the **Global Library**.
  2. If a user has successfully mapped "Cust Nm" to "Customer Name" using `SPLIT_FULL_NAME` 50 times before, **auto-suggest** that plan.
  3. This reduces LLM costs and increases predictability.

---

## 9. API Contract (Simplified)

### `POST /api/transform`
* **Input:** File (Excel/CSV), Enterprise_ID (config)
* **Output:** `job_id`

### `GET /api/status/{job_id}`
* **Output:** `processing` | `waiting_for_input` | `completed`

### `GET /api/question/{job_id}`
* **Output:** JSON Question (if status is `waiting_for_input`).
* *Example:* `{"question": "Column 'D' has mixed dates. Default to US or UK format?", "options": ["US", "UK"]}`

### `POST /api/answer/{job_id}`
* **Input:** `{"answer": "US"}` (Resumes execution).

---

## 10. Implementation Checklist

- [ ] **Setup Python Engine:** Implement the `FunctionRegistry` and `ExecutionEngine` using Polars/Pandas.
- [ ] **Define JSON Schemas:** Create Pydantic models for all agent Inputs/Outputs.
- [ ] **Build Schema Agent:** Connect to Claude/GPT-4 to analyze CSV samples.
- [ ] **Build Planner Agent:** Feed Schema Agent output to Planner to generate JSON.
- [ ] **Integrate Enrichment:** Connect a simple Pincode API to the engine.
- [ ] **Orchestrator Logic:** Build the `while` loop that manages the flow and handles exceptions.

---

## 11. Related Documentation

| File | Description |
|------|-------------|
| `code.agent.md` | Code execution tool - Bash commands, file operations, sandboxed Python |
| `bash.agent.md` | Bash tool - Persistent shell sessions, system automation |
| `memory.agent.md` | Memory tool - Cross-conversation persistence, file-based storage |
| `excel-mcp-server/` | Go-based MCP server for Excel manipulation |