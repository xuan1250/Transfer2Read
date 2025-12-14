"""
AI Cost Tracker

LangChain callback for tracking token usage and calculating AI costs.
Implements Story 5.1 requirements for real-time AI cost estimation.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult

logger = logging.getLogger(__name__)


class CostTrackerCallback(BaseCallbackHandler):
    """
    LangChain callback handler for tracking AI token usage and calculating costs.

    Tracks prompt tokens, completion tokens, and calculates estimated cost
    based on model pricing.

    Pricing (as of 2025-12-14):
    - GPT-4o: $2.50/1M input tokens, $10.00/1M output tokens
    - Claude 3.5 Haiku: $0.25/1M input tokens, $1.25/1M output tokens

    Attributes:
        model_name: AI model name (e.g., "gpt-4o", "claude-3-5-haiku")
        prompt_tokens: Total input tokens used
        completion_tokens: Total output tokens generated
        total_tokens: Sum of prompt + completion tokens
        estimated_cost: Calculated cost in USD
        calls: Number of LLM calls made
        timestamps: List of call timestamps for debugging
    """

    # Model pricing per 1M tokens (USD)
    MODEL_PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25},
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        # Fallback default (use GPT-4o pricing as conservative estimate)
        "default": {"input": 2.50, "output": 10.00}
    }

    def __init__(self, model_name: str = "gpt-4o", job_id: Optional[str] = None):
        """
        Initialize cost tracker callback.

        Args:
            model_name: AI model name for pricing lookup
            job_id: Optional job ID for logging context
        """
        super().__init__()
        self.model_name = model_name
        self.job_id = job_id
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.estimated_cost = 0.0
        self.calls = 0
        self.timestamps: List[str] = []

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """
        Called when LLM finishes generating response.

        Extracts token usage from response metadata and updates cost calculation.

        Args:
            response: LLM result containing token usage metadata
            **kwargs: Additional callback arguments
        """
        try:
            # Extract token usage from response metadata
            if response.llm_output and "token_usage" in response.llm_output:
                usage = response.llm_output["token_usage"]
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)

                # Update totals
                self.prompt_tokens += prompt_tokens
                self.completion_tokens += completion_tokens
                self.total_tokens += (prompt_tokens + completion_tokens)
                self.calls += 1
                self.timestamps.append(datetime.utcnow().isoformat())

                # Recalculate cost
                self.estimated_cost = self._calculate_cost()

                logger.debug(
                    f"AI call completed - Model: {self.model_name}, "
                    f"Tokens: {prompt_tokens}+{completion_tokens}={prompt_tokens+completion_tokens}, "
                    f"Cost: ${self._calculate_call_cost(prompt_tokens, completion_tokens):.4f}, "
                    f"Total cost: ${self.estimated_cost:.4f}"
                )

        except Exception as e:
            logger.warning(f"Failed to track AI cost: {str(e)}")

    def _calculate_cost(self) -> float:
        """
        Calculate total estimated cost based on accumulated tokens.

        Returns:
            float: Estimated cost in USD (rounded to 4 decimal places)
        """
        return self._calculate_call_cost(self.prompt_tokens, self.completion_tokens)

    def _calculate_call_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost for a single call or total tokens.

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            float: Estimated cost in USD (rounded to 4 decimal places)
        """
        # Get pricing for model (fall back to default if model not found)
        pricing = self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING["default"])

        # Calculate cost per token tier
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        # Return total cost rounded to 4 decimals (e.g., $0.1523)
        return round(input_cost + output_cost, 4)

    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get summary of token usage and cost.

        Returns:
            dict: Summary containing:
                - prompt_tokens: Total input tokens
                - completion_tokens: Total output tokens
                - total_tokens: Sum of input + output
                - estimated_cost: Calculated cost in USD
                - model_name: AI model used
                - calls: Number of LLM calls made
                - avg_tokens_per_call: Average tokens per call
        """
        avg_tokens = self.total_tokens / self.calls if self.calls > 0 else 0

        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
            "model_name": self.model_name,
            "calls": self.calls,
            "avg_tokens_per_call": round(avg_tokens, 2)
        }

    def reset(self) -> None:
        """Reset all counters to zero."""
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.estimated_cost = 0.0
        self.calls = 0
        self.timestamps = []

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"CostTrackerCallback(model={self.model_name}, "
            f"tokens={self.total_tokens}, cost=${self.estimated_cost:.4f}, "
            f"calls={self.calls})"
        )
