"""
OpenAI backend for cloud-based language models.
Connects to OpenAI API for text generation.
"""

import time
from typing import List, Tuple, Dict, Any, Optional

try:
    from openai import OpenAI, OpenAIError, RateLimitError, APIConnectionError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from services.llm.base import (
    LLMBackend,
    LLMResponse,
    LLMError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMInvalidRequestError
)
from config.settings import LLMConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class OpenAIBackend(LLMBackend):
    """OpenAI API backend."""
    
    def __init__(self, config: LLMConfig, system_prompt: str = ""):
        """
        Initialize OpenAI backend.
        
        Args:
            config: LLM configuration
            system_prompt: System prompt for the assistant
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI library not installed. Install with: pip install openai"
            )
        
        if not config.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=config.openai_api_key)
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.system_prompt = system_prompt
        self.model = "gpt-3.5-turbo"  # Default model
        
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        logger.info("Initialized OpenAI backend")
    
    def send(self, prompt: str, history: Optional[List[Tuple[str, str]]] = None) -> LLMResponse:
        """
        Send prompt with conversation history and get response.
        
        Args:
            prompt: User prompt/message
            history: Conversation history as list of (role, content) tuples
            
        Returns:
            LLMResponse with generated text
        """
        # Build messages array
        messages = self._build_messages(prompt, history or [])
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Sending request to OpenAI (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                text = response.choices[0].message.content.strip()
                tokens_used = response.usage.total_tokens if response.usage else None
                finish_reason = response.choices[0].finish_reason
                
                logger.debug(f"Received response from OpenAI: {len(text)} characters, {tokens_used} tokens")
                
                return LLMResponse(
                    text=text,
                    tokens_used=tokens_used,
                    finish_reason=finish_reason,
                    metadata={"backend": "openai", "model": self.model, "attempt": attempt + 1}
                )
            
            except RateLimitError as e:
                logger.warning(f"OpenAI rate limit exceeded (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise LLMRateLimitError("OpenAI rate limit exceeded after retries")
            
            except APIConnectionError as e:
                logger.warning(f"OpenAI connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise LLMConnectionError(f"Cannot connect to OpenAI API: {e}")
            
            except OpenAIError as e:
                logger.error(f"OpenAI API error: {e}")
                raise LLMError(f"OpenAI API error: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error in OpenAI backend: {e}")
                raise LLMError(f"OpenAI backend error: {e}")
        
        raise LLMConnectionError("Failed to get response from OpenAI after retries")
    
    def _build_messages(self, user_input: str, history: List[Tuple[str, str]]) -> List[Dict[str, str]]:
        """
        Build messages array for OpenAI API.
        
        Args:
            user_input: Current user input
            history: Conversation history
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Add system prompt
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        # Add conversation history
        for role, content in history:
            # Map role names to OpenAI format
            openai_role = "assistant" if role.lower() in ["assistant", "ai", "bot"] else "user"
            messages.append({"role": openai_role, "content": content})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def reset(self) -> None:
        """Reset conversation state (no-op for stateless OpenAI)."""
        logger.debug("OpenAI backend reset (no-op)")
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Return backend capabilities.
        
        Returns:
            Dictionary with capability flags
        """
        return {
            "streaming": True,
            "function_calling": True,
            "vision": False,  # Depends on model
            "embeddings": True
        }
    
    def is_available(self) -> bool:
        """
        Check if OpenAI backend is available.
        
        Returns:
            True if backend is configured and reachable, False otherwise
        """
        try:
            # Try a simple API call to check availability
            self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI backend not available: {e}")
            return False
