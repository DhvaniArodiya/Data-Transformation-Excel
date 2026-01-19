"""
Configuration settings for AI Excel Transformation System.
Loads environment variables and provides centralized configuration.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure AI Foundry Configuration
    anthropic_endpoint: str = Field(
        default="https://anydoctransform-resource.services.ai.azure.com/anthropic/",
        alias="ENDPOINT"
    )
    anthropic_api_key: str = Field(
        default="",
        alias="API_KEY"
    )
    deployment_name: str = Field(
        default="claude-opus-4-5",
        alias="DEPLOYMENT_NAME"
    )
    
    # Processing Settings
    sample_rows: int = Field(default=50, description="Number of rows to sample for analysis")
    max_retries: int = Field(default=3, description="Max retries per transformation error")
    
    # File Storage Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    jobs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "jobs")
    output_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "output")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
