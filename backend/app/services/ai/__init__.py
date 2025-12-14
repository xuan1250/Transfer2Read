"""
AI Services Package

This package provides AI integration services for PDF layout analysis.
Supports GPT-4o (primary) and Claude 3.5 Haiku (fallback) via LangChain.
"""

from app.services.ai.base import AIProvider
from app.services.ai.gpt4 import GPT4Provider
from app.services.ai.claude import ClaudeProvider

__all__ = ["AIProvider", "GPT4Provider", "ClaudeProvider"]
