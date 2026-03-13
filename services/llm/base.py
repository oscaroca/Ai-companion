"""
Abstract base class for LLM backends.
Provides a unified interface for different language model providers.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from LLM backend."""
    text: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMBackend(ABC):
    """Abstract base class for LLM backends."""
    
    @abstractmethod
    def send(self, prompt: str, history: Optional[List[Tuple[str, str]]] = None) -> LLMResponse:
        """
        Send prompt with conversation history and get response.
        
        Args:
            prompt: User prompt/message
            history: Conversation history as list of (role, content) tuples
            
        Returns:
            LLMResponse with generated text and metadata
        """
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset conversation state."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Return backend capabilities.
        
        Returns:
            Dictionary with capability flags:
            - streaming: Supports streaming responses
            - function_calling: Supports function/tool calling
            - vision: Supports image inputs
            - embeddings: Supports text embeddings
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if backend is available and ready.
        
        Returns:
            True if backend can be used, False otherwise
        """
        pass


class LLMError(Exception):
    """Base exception for LLM backend errors."""
    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM backend fails."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""
    pass


class LLMInvalidRequestError(LLMError):
    """Raised when request is invalid."""
    pass
