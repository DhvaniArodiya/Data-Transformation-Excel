"""
Azure AI Foundry Client Wrapper.
Provides a configured Anthropic client for Claude API calls.
"""

from typing import Optional, List, Dict, Any
from anthropic import Anthropic
from .config import get_settings


class AIClient:
    """
    Wrapper for Azure AI Foundry (Anthropic) client.
    Handles authentication and provides convenience methods for agent interactions.
    """
    
    def __init__(self):
        """Initialize the AI client with Azure AI Foundry configuration."""
        self._settings = get_settings()
        self._client = Anthropic(
            api_key=self._settings.anthropic_api_key,
            base_url=self._settings.anthropic_endpoint,
        )
        self._model = self._settings.deployment_name
    
    @property
    def client(self) -> Anthropic:
        """Get the underlying Anthropic client."""
        return self._client
    
    @property
    def model(self) -> str:
        """Get the configured model name."""
        return self._model
    
    def create_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """
        Create a message using the Claude API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 for deterministic)
            tools: Optional list of tools for agent mode
            
        Returns:
            The API response object
        """
        kwargs = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }
        
        if system:
            kwargs["system"] = system
        
        if tools:
            kwargs["tools"] = tools
        
        return self._client.messages.create(**kwargs)
    
    def get_text_response(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> str:
        """
        Simple text-in, text-out API call.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt
            max_tokens: Maximum tokens in response
            
        Returns:
            The text content of the response
        """
        response = self.create_message(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=max_tokens,
        )
        
        # Extract text from response
        if response.content and len(response.content) > 0:
            return response.content[0].text
        return ""
    
    def get_json_response(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Get a JSON response from the API.
        Automatically parses the response as JSON.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt (should instruct JSON output)
            max_tokens: Maximum tokens in response
            
        Returns:
            Parsed JSON as a dictionary
        """
        import json
        
        text = self.get_text_response(prompt, system, max_tokens)
        
        # Try to extract JSON from the response
        # Handle cases where response might have markdown code blocks
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse was: {text[:500]}")


# Global client instance
_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Get or create the global AI client instance."""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
