"""
Pyttsx3 TTS engine implementation.
Uses system TTS voices for speech synthesis.
"""

from pathlib import Path
from typing import List
import tempfile

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

from services.tts.base import TTSEngine, TTSError, TTSInitializationError, TTSSynthesisError
from services.audio.audio_processor import AudioProcessor
from config.settings import TTSConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class Pyttsx3Engine(TTSEngine):
    """System TTS using pyttsx3."""
    
    def __init__(self, config: TTSConfig, audio_processor: AudioProcessor):
        """
        Initialize pyttsx3 TTS engine.
        
        Args:
            config: TTS configuration
            audio_processor: Audio processor for normalization
        """
        if not PYTTSX3_AVAILABLE:
            raise TTSInitializationError(
                "pyttsx3 not installed. Install with: pip install pyttsx3"
            )
        
        self.config = config
        self.audio_processor = audio_processor
        
        try:
            self.engine = pyttsx3.init()
            
            # Set voice
            voices = self.engine.getProperty('voices')
            if voices and len(voices) > config.voice_index:
                self.engine.setProperty('voice', voices[config.voice_index].id)
            
            # Set rate and volume
            self.engine.setProperty('rate', config.rate)
            self.engine.setProperty('volume', config.volume)
            
            logger.info(f"Pyttsx3 TTS engine initialized (voice index: {config.voice_index})")
        
        except Exception as e:
            raise TTSInitializationError(f"Failed to initialize pyttsx3: {e}")
    
    def synthesize(self, text: str, output_path: Path) -> Path:
        """
        Synthesize speech and save to file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            
        Returns:
            Path to normalized audio file
        """
        if not text or not text.strip():
            raise TTSSynthesisError("Text cannot be empty")
        
        try:
            logger.debug(f"Synthesizing speech with pyttsx3: {len(text)} characters")
            
            # Create temporary file for raw output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = Path(tmp.name)
            
            # Synthesize to temp file
            self.engine.save_to_file(text, str(temp_path))
            self.engine.runAndWait()
            
            # Normalize to Unity format
            output_path = Path(output_path)
            normalized_path = self.audio_processor.normalize_audio(temp_path, output_path)
            
            # Clean up temp file
            temp_path.unlink()
            
            logger.debug(f"Speech synthesized: {normalized_path}")
            return normalized_path
        
        except Exception as e:
            logger.error(f"Pyttsx3 synthesis failed: {e}")
            raise TTSSynthesisError(f"Failed to synthesize speech: {e}")
    
    def get_voices(self) -> List[str]:
        """
        Return list of available voices.
        
        Returns:
            List of voice names
        """
        try:
            voices = self.engine.getProperty('voices')
            return [voice.name for voice in voices]
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []
    
    def set_voice(self, voice_id: str) -> None:
        """
        Set active voice.
        
        Args:
            voice_id: Voice identifier (name or index)
        """
        try:
            voices = self.engine.getProperty('voices')
            
            # Try to find voice by name
            for voice in voices:
                if voice.name == voice_id or voice.id == voice_id:
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"Set voice to: {voice.name}")
                    return
            
            # Try to parse as index
            try:
                index = int(voice_id)
                if 0 <= index < len(voices):
                    self.engine.setProperty('voice', voices[index].id)
                    logger.info(f"Set voice to index {index}: {voices[index].name}")
                    return
            except ValueError:
                pass
            
            logger.warning(f"Voice not found: {voice_id}")
        
        except Exception as e:
            logger.error(f"Failed to set voice: {e}")
    
    def is_available(self) -> bool:
        """
        Check if pyttsx3 engine is available.
        
        Returns:
            True if engine is initialized, False otherwise
        """
        return self.engine is not None
