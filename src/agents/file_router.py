from typing import List
from pathlib import Path
import json
from .base_agent import BaseAgent

class FileRouterAgent(BaseAgent):
    """
    Agent responsible for selecting which files are relevant to a user's prompt.
    """
    
    @property
    def name(self) -> str:
        return "File Router"
        
    @property
    def system_prompt(self) -> str:
        return """You are a File Selection Agent.
Your goal is to identify which files from a list are relevant to the user's request.

INPUT:
1. A user prompt describing a transformation or data analysis task.
2. A list of available filenames.

OUTPUT:
Return a JSON object with a single key "selected_files" containing a list of the filenames that are relevant.
If the prompt applies to ALL files (e.g., "convert all to CSV"), return all filenames.
If no files match, return an empty list.

Example Input:
Prompt: "Calculate total salary for employees"
Files: ["inventory.xlsx", "employees_2024.csv", "sales_data.xml"]

Example Output:
{
  "selected_files": ["employees_2024.csv"]
}
"""

    def run(self, *args, **kwargs):
        """
        Alias for select_files to satisfy BaseAgent interface.
        Expects arguments: file_paths: List[Path], user_prompt: str
        """
        return self.select_files(*args, **kwargs)

    def select_files(self, file_paths: List[Path], user_prompt: str, schemas: dict = None) -> List[Path]:
        """
        Select relevant files based on the prompt.
        
        Args:
            file_paths: List of paths to available files
            user_prompt: The user's instruction
            schemas: Optional dictionary mapping filenames to their structure (sheets/columns)
            
        Returns:
            List of Path objects for the selected files
        """
        if not file_paths:
            return []
            
        # Prepare the input for the LLM
        files_context = []
        for p in file_paths:
            file_info = {"filename": p.name}
            if schemas and p.name in schemas:
                file_info["structure"] = schemas[p.name]
            files_context.append(file_info)
        
        prompt = f"""
USER PROMPT: "{user_prompt}"

AVAILABLE FILES:
{json.dumps(files_context, indent=2)}

Which of these files are relevant to the prompt? 
Evaluate based on filenames AND their internal structure (sheet names, column names) if provided.
Return JSON with a "selected_files" key containing a list of the *exact* filenames.
"""
        
        try:
            # Call LLM
            response = self._call_api_json(prompt)
            selected_names = response.get("selected_files", [])
            
            # Map back to Path objects
            selected_paths = []
            for name in selected_names:
                # Find the matching path
                for path in file_paths:
                    if path.name == name:
                        selected_paths.append(path)
                        break
            
            return selected_paths
            
        except Exception as e:
            print(f"File selection failed: {e}")
            # Fallback: If routing fails, return empty list rather than spamming all files
            return []
