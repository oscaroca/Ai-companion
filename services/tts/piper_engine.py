"""
Piper TTS engine implementation.
Uses ONNX models for high-quality speech synthesis.
"""

from pathlib import Path
from typing import List
import tempfile

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

from services.tts.base import TTSEngine, TTSError, TTSInitializationError, TTSSynthesisError
from services.audio.audio_processor import AudioProcessor
from config.settings import TTSConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class PiperEngine(TTSEngine):
    """Piper TTS with ONNX models."""
    
    def __init__(self, config: TTSConfig, audio_processor: AudioProcessor):
        """
        Initialize Piper TTS engine.
        
        Args:
            config: TTS configuration
            audio_processor: Audio processor for normalization
        """
        self.config = config
        self.audio_processor = audio_processor
        self.model_path = config.piper_model_path
        self.voice_model = None
        self.current_voice = None
        
        if not self.model_path:
            raise TTSInitializationError("Piper model path not configured")
        
        # Try to load Piper
        try:
            from piper.voice import PiperVoice
            self.PiperVoice = PiperVoice
            self._load_model()
            logger.info(f"Piper TTS engine initialized with model: {self.model_path}")
        except ImportError:
            raise TTSInitializationError(
                "Piper TTS not installed. Install with: pip install piper-tts"
            )
        except Exception as e:
            raise TTSInitializationError(f"Failed to initialize Piper: {e}")
    
    def _load_model(self) -> None:
        """Load Piper voice model."""
        model_path = Path(self.model_path)
        
        if not model_path.exists():
            raise TTSInitializationError(f"Piper model not found: {self.model_path}")
        
        try:
            self.voice_model = self.PiperVoice.load(str(model_path), use_cuda=False)
            self.current_voice = model_path.stem
            logger.info(f"Loaded Piper model: {self.current_voice}")
        except Exception as e:
            raise TTSInitializationError(f"Failed to load Piper model: {e}")
    
    def synthesize(self, text: str, output_path: Path) -> Path:
        """
        Synthesize speech and save to file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            
        Returns:
            Path to normalized audio file
        """
        if not self.voice_model:
            raise TTSSynthesisError("Piper model not loaded")
        
        if not text or not text.strip():
            raise TTSSynthesisError("Text cannot be empty")
        
        try:
            logger.debug(f"Synthesizing speech with Piper: {len(text)} characters")
            
            # Create temporary file for raw output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = Path(tmp.name)
            
            # Synthesize audio
            audio_data = self.voice_model.synthesize(text)
            
            # Write raw audio
            if not SOUNDFILE_AVAILABLE:
                raise TTSSynthesisError("soundfile library required for Piper TTS")
            
            sf.write(str(temp_path), audio_data, samplerate=22050)  # Piper default
            
            # Normalize to Unity format
            output_path = Path(output_path)
            normalized_path = self.audio_processor.normalize_audio(temp_path, output_path)
            
            # Clean up temp file
            temp_path.unlink()
            
            logger.debug(f"Speech synthesized: {normalized_path}")
            return normalized_path
        
        except Exception as e:
            logger.error(f"Piper synthesis failed: {e}")
            raise TTSSynthesisError(f"Failed to synthesize speech: {e}")
    
    def get_voices(self) -> List[str]:
        """
        Return list of available voices.
        
        Returns:
            List with current voice
        """
        if self.current_voice:
            return [self.current_voice]
        return []
    
    def set_voice(self, voice_id: str) -> None:
        """
        Set active voice (load different model).
        
        Args:
            voice_id: Path to voice model file
        """
        self.model_path = voice_id
        self._load_model()
    
    def is_available(self) -> bool:
        """
        Check if Piper engine is available.
        
        Returns:
            True if model is loaded, False otherwise
        """
        return self.voice_model is not None
