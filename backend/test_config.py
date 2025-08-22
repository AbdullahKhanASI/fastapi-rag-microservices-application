#!/usr/bin/env python3
"""Test configuration loading"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.config import settings

print(f"Current working directory: {os.getcwd()}")
print(f"Project root: {Path(__file__).parent}")
print(f"OpenAI API Key: {settings.openai_api_key}")
print(f"Anthropic API Key: {settings.anthropic_api_key}")
print(f"LLM Model: {settings.llm_model}")

# Check if .env file exists
env_file = Path(".env")
print(f".env file exists: {env_file.exists()}")
if env_file.exists():
    print(f".env file path: {env_file.absolute()}")
    with open(env_file) as f:
        lines = f.readlines()[:3]  # Show first 3 lines
        print("First few lines of .env:")
        for line in lines:
            if "OPENAI_API_KEY" in line:
                print(f"  {line.strip()[:30]}...")