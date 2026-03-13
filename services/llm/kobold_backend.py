"""
Kobold backend for local GGUF models.
Connects to KoboldCpp API for text generation.
"""

import requests
import time
from typing import List, Tuple, Dict, Any, Optional

from services.llm.base import (
    LLMBackend,
    LLMResponse,
    LLMError,
    LLMConnectionError,
    LLMInvalidRequestError
)
from config.settings import LLMConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class KoboldBackend(LLMBackend):
    """Kobold local GGUF model backend."""
    
    def __init__(self, config: LLMConfig, system_prompt: str = ""):
        """
        Initialize Kobold backend.
        
        Args:
            config: LLM configuration
            system_prompt: System prompt to prepend to all requests
        """
        self.url = config.kobold_url
        self.temperature = config.temperature
        self.top_p = config.top_p
        self.max_tokens = config.max_tokens
        self.system_prompt = system_prompt
        
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.timeout = 30  # seconds
        
        logger.info(f"Initialized Kobold backend: {self.url}")
    
    def send(self, prompt: str, history: Optional[List[Tuple[str, str]]] = None) -> LLMResponse:
        """
        Send prompt with conversation history and get response.
        
        Args:
            prompt: User prompt/message
            history: Conversation history as list of (role, content) tuples
            
        Returns:
            LLMResponse with generated text
        """
        # Build full prompt with system prompt and history
        full_prompt = self._build_prompt(prompt, history or [])
        
        payload = {
            "prompt": full_prompt,
            "max_length": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stop_sequence": ["User:", "\n\n", "</s>", "Human:", "Assistant:"]
        }
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Sending request to Kobold (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    self.url,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                if "results" not in data or not data["results"]:
                    raise LLMInvalidRequestError("Invalid response from Kobold API")
                
                text = data["results"][0]["text"].strip()
                
                logger.debug(f"Received response from Kobold: {len(text)} characters")
                
                return LLMResponse(
                    text=text,
                    tokens_used=data["results"][0].get("tokens", None),
                    metadata={"backend": "kobold", "attempt": attempt + 1}
                )
            
            except requests.exceptions.Timeout:
                logger.warning(f"Kobold request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise LLMConnectionError("Kobold API timeout after retries")
            
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Kobold connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise LLMConnectionError(f"Cannot connect to Kobold API at {self.url}")
            
            except requests.exceptions.HTTPError as e:
                logger.error(f"Kobold HTTP error: {e}")
                raise LLMError(f"Kobold API error: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error in Kobold backend: {e}")
                raise LLMError(f"Kobold backend error: {e}")
        
        raise LLMConnectionError("Failed to get response from Kobold after retries")
    
    def _build_prompt(self, user_input: str, history: List[Tuple[str, str]]) -> str:
        """
        Build full prompt with system prompt and history.
        
        Args:
            user_input: Current user input
            history: Conversation history
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        # Add system prompt
        if self.system_prompt:
            prompt_parts.append(self.system_prompt)
            prompt_parts.append("\n\n")
        
        # Add conversation history
        for role, content in history:
            prompt_parts.append(f"{role}: {content}\n")
        
        # Add current user input
        prompt_parts.append(f"User: {user_input}\nAssistant:")
        
        return "".join(prompt_parts)
    
    def reset(self) -> None:
        """Reset conversation state (no-op for stateless Kobold)."""
        logger.debug("Kobold backend reset (no-op)")
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Return backend capabilities.
        
        Returns:
            Dictionary with capability flags
        """
        return {
            "streaming": False,
            "function_calling": False,
            "vision": False,
            "embeddings": False
        }
    
    def is_available(self) -> bool:
        """
        Check if Kobold backend is available.
        
        Returns:
            True if backend is reachable, False otherwise
        """
        try:
            # Try a simple health check
            response = requests.get(
                self.url.replace("/api/v1/generate", "/api/v1/model"),
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Kobold backend not available: {e}")
            return False
