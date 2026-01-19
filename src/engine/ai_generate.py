"""
AI Generate Function - LLM fallback for complex transformations.
Uses Claude to generate/transform values when prebuilt functions aren't sufficient.
"""

from typing import Any, Dict, Optional, List
import pandas as pd

from ..client import get_ai_client, AIClient


class AIGenerator:
    """
    AI-powered value generation/transformation.
    Used as a fallback when prebuilt functions can't handle the transformation.
    """
    
    def __init__(self, client: Optional[AIClient] = None):
        """Initialize with optional AI client."""
        self._client = client or get_ai_client()
    
    def generate(
        self,
        value: Any,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Use AI to transform or generate a value.
        
        Args:
            value: Input value to transform
            params: Parameters including prompt_template
            context: Additional context (other columns in the row)
            
        Returns:
            Generated/transformed value
        """
        if pd.isna(value) or value is None:
            return ""
        
        prompt_template = params.get("prompt_template", "Transform this value: {value}")
        max_tokens = params.get("max_tokens", 100)
        
        # Build prompt
        prompt = self._build_prompt(value, prompt_template, context)
        
        # Call AI
        try:
            response = self._client.get_text_response(
                prompt=prompt,
                system=self._get_system_prompt(),
                max_tokens=max_tokens,
            )
            return response.strip()
        except Exception as e:
            return str(value)  # Return original on error
    
    def _build_prompt(
        self,
        value: Any,
        template: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build the prompt from template."""
        prompt = template.replace("{value}", str(value))
        
        # Add context if provided
        if context:
            for key, val in context.items():
                prompt = prompt.replace(f"{{{key}}}", str(val) if not pd.isna(val) else "")
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI generation."""
        return """You are a data transformation assistant. Your task is to transform or generate values based on the user's instructions.

RULES:
1. Return ONLY the transformed value, nothing else.
2. Do not include explanations, quotes, or formatting.
3. If you cannot transform the value, return it unchanged.
4. Be concise and accurate."""
    
    def batch_generate(
        self,
        values: List[Any],
        params: Dict[str, Any],
        contexts: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 10,
    ) -> List[str]:
        """
        Generate values for a batch of inputs.
        
        Args:
            values: List of input values
            params: Parameters including prompt_template
            contexts: Optional list of contexts for each value
            batch_size: Number of values to process in one API call
            
        Returns:
            List of generated values
        """
        results = []
        
        for i in range(0, len(values), batch_size):
            batch_values = values[i:i + batch_size]
            batch_contexts = contexts[i:i + batch_size] if contexts else [None] * len(batch_values)
            
            # For small batches, process individually
            for value, context in zip(batch_values, batch_contexts):
                result = self.generate(value, params, context)
                results.append(result)
        
        return results
    
    def extract_entities(
        self,
        text: str,
        entity_types: List[str],
    ) -> Dict[str, str]:
        """
        Extract specific entities from text using AI.
        
        Args:
            text: Input text
            entity_types: Types of entities to extract (e.g., ["name", "phone", "email"])
            
        Returns:
            Dict mapping entity_type to extracted value
        """
        if pd.isna(text) or not text:
            return {et: "" for et in entity_types}
        
        prompt = f"""Extract the following information from this text:
Text: "{text}"

Extract: {', '.join(entity_types)}

Return as JSON object with keys: {entity_types}
Return empty string for any information not found."""
        
        try:
            response = self._client.get_json_response(
                prompt=prompt,
                system="You are an entity extraction assistant. Return only valid JSON.",
                max_tokens=200,
            )
            
            result = {}
            for et in entity_types:
                result[et] = response.get(et, "")
            return result
            
        except Exception:
            return {et: "" for et in entity_types}
    
    def classify(
        self,
        value: Any,
        categories: List[str],
        default: str = "Other",
    ) -> str:
        """
        Classify a value into one of the given categories.
        
        Args:
            value: Value to classify
            categories: List of possible categories
            default: Default category if classification fails
            
        Returns:
            Selected category
        """
        if pd.isna(value) or not value:
            return default
        
        prompt = f"""Classify this value into one of the categories.

Value: "{value}"
Categories: {categories}

Return ONLY the category name, nothing else."""
        
        try:
            response = self._client.get_text_response(
                prompt=prompt,
                system="You are a classification assistant. Return only the category name.",
                max_tokens=50,
            )
            
            result = response.strip()
            if result in categories:
                return result
            
            # Try case-insensitive match
            for cat in categories:
                if cat.lower() == result.lower():
                    return cat
            
            return default
            
        except Exception:
            return default
    
    def standardize_address(
        self,
        address: str,
    ) -> Dict[str, str]:
        """
        Parse and standardize an address into components.
        
        Args:
            address: Raw address string
            
        Returns:
            Dict with address_line1, address_line2, city, state, pincode, country
        """
        if pd.isna(address) or not address:
            return {
                "address_line1": "",
                "address_line2": "",
                "city": "",
                "state": "",
                "pincode": "",
                "country": "",
            }
        
        prompt = f"""Parse this Indian address into structured components:
Address: "{address}"

Return JSON with these keys:
- address_line1: Street/building info
- address_line2: Area/landmark
- city: City name
- state: State name
- pincode: 6-digit pincode
- country: Country (default India)

Return empty string for any component not found."""
        
        try:
            return self._client.get_json_response(
                prompt=prompt,
                system="You are an address parsing assistant for Indian addresses. Return only valid JSON.",
                max_tokens=200,
            )
        except Exception:
            return {
                "address_line1": str(address),
                "address_line2": "",
                "city": "",
                "state": "",
                "pincode": "",
                "country": "India",
            }


# Global instance
_ai_generator: Optional[AIGenerator] = None


def get_ai_generator() -> AIGenerator:
    """Get or create the global AI generator."""
    global _ai_generator
    if _ai_generator is None:
        _ai_generator = AIGenerator()
    return _ai_generator


def ai_generate(value: Any, params: Dict[str, Any], **kwargs) -> str:
    """
    Function registry compatible wrapper for AI generation.
    """
    generator = get_ai_generator()
    context = kwargs.get("row")
    return generator.generate(value, params, context)
