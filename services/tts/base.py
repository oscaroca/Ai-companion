"""
Abstract base class for TTS engines.
Provides a unified interface for different text-to-speech providers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""
    
    @abstractmethod
    def synthesize(self, text: str, output_path: Path) -> Path:
        """
        Synthesize speech and save to file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            
        Returns:
            Path to normalized audio file (Unity-compatible format)
        """
        pass
    
    @abstractmethod
    def get_voices(self) -> List[str]:
        """
        Return list of available voices.
        
        Returns:
            List of voice identifiers
        """
        pass
    
    @abstractmethod
    def set_voice(self, voice_id: str) -> None:
        """
        Set active voice.
        
        Args:
            voice_id: Voice identifier
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if TTS engine is available and ready.
        
        Returns:
            True if engine can be used, False otherwise
        """
        pass


class TTSError(Exception):
    """Base exception for TTS engine errors."""
    pass


class TTSInitializationError(TTSError):
    """Raised when TTS engine initialization fails."""
    pass


class TTSSynthesisError(TTSError):
    """Raised when speech synthesis fails."""
    pass
