"""
Base Agent - Abstract base class for all AI agents.
Provides common functionality for Claude API interactions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json

from ..client import get_ai_client, AIClient


class BaseAgent(ABC):
    """
    Abstract base class for AI agents.
    Provides common functionality for interacting with Claude.
    """
    
    def __init__(self, client: Optional[AIClient] = None):
        """
        Initialize the agent.
        
        Args:
            client: Optional AIClient instance. If None, uses global client.
        """
        self._client = client or get_ai_client()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the agent's name."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Execute the agent's main task."""
        pass
    
    def _call_api(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        """
        Make a simple text API call.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum response tokens
            temperature: Sampling temperature
            
        Returns:
            Text response from Claude
        """
        return self._client.get_text_response(
            prompt=prompt,
            system=self.system_prompt,
            max_tokens=max_tokens,
        )
    
    def _call_api_json(
        self,
        prompt: str,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Make an API call expecting JSON response.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum response tokens
            
        Returns:
            Parsed JSON response
        """
        return self._client.get_json_response(
            prompt=prompt,
            system=self.system_prompt,
            max_tokens=max_tokens,
        )
    
    def _format_data_for_prompt(
        self,
        data: Any,
        format_type: str = "json"
    ) -> str:
        """
        Format data for inclusion in a prompt.
        
        Args:
            data: Data to format (dict, list, DataFrame, etc.)
            format_type: 'json' or 'csv'
            
        Returns:
            Formatted string
        """
        if format_type == "json":
            if hasattr(data, 'model_dump'):
                return json.dumps(data.model_dump(), indent=2)
            return json.dumps(data, indent=2, default=str)
        elif format_type == "csv":
            if hasattr(data, 'to_csv'):
                return data.to_csv(index=False)
            return str(data)
        return str(data)
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        Parse JSON from response text, handling markdown code blocks.
        
        Args:
            text: Response text that may contain JSON
            
        Returns:
            Parsed JSON dictionary
        """
        text = text.strip()
        
        # Handle markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        return json.loads(text)
