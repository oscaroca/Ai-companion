"""
Audio processing utilities for format conversion and normalization.
Ensures audio compatibility with Unity and other systems.
"""

from pathlib import Path
from typing import Optional

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

from utils.logging_config import get_logger


logger = get_logger(__name__)


class AudioProcessingError(Exception):
    """Raised when audio processing fails."""
    pass


class AudioProcessor:
    """Handles audio format conversion and normalization."""
    
    # Unity-compatible audio format
    TARGET_SAMPLE_RATE = 44100  # Hz
    TARGET_CHANNELS = 1  # Mono
    TARGET_SAMPLE_WIDTH = 2  # 16-bit PCM
    
    def __init__(self):
        """Initialize audio processor."""
        if not PYDUB_AVAILABLE:
            logger.warning("pydub not available, audio processing may be limited")
        
        if not SOUNDFILE_AVAILABLE:
            logger.warning("soundfile not available, some audio formats may not be supported")
        
        logger.info("Audio processor initialized")
    
    def normalize_audio(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Normalize audio to Unity-compatible format.
        
        Converts to:
        - 44.1kHz sample rate
        - Mono channel
        - 16-bit PCM WAV
        
        Args:
            input_path: Path to input audio file
            output_path: Path for output file (uses input_path if None)
            
        Returns:
            Path to normalized audio file
            
        Raises:
            AudioProcessingError: If processing fails
        """
        if not PYDUB_AVAILABLE:
            raise AudioProcessingError(
                "pydub is required for audio normalization. "
                "Install with: pip install pydub"
            )
        
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise AudioProcessingError(f"Input file not found: {input_path}")
        
        # Use input path if output not specified
        if output_path is None:
            output_path = input_path
        else:
            output_path = Path(output_path)
        
        try:
            logger.debug(f"Normalizing audio: {input_path}")
            
            # Load audio file
            audio = AudioSegment.from_file(str(input_path))
            
            # Convert to target format
            audio = audio.set_frame_rate(self.TARGET_SAMPLE_RATE)
            audio = audio.set_channels(self.TARGET_CHANNELS)
            audio = audio.set_sample_width(self.TARGET_SAMPLE_WIDTH)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export as WAV
            audio.export(
                str(output_path),
                format="wav",
                parameters=["-acodec", "pcm_s16le"]  # 16-bit PCM
            )
            
            logger.debug(f"Audio normalized: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to normalize audio: {e}")
            raise AudioProcessingError(f"Audio normalization failed: {e}")
    
    def validate_audio(self, audio_path: Path) -> bool:
        """
        Validate audio file format.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            True if audio meets target format, False otherwise
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            logger.warning(f"Audio file not found: {audio_path}")
            return False
        
        try:
            if SOUNDFILE_AVAILABLE:
                # Use soundfile for validation
                info = sf.info(str(audio_path))
                
                is_valid = (
                    info.samplerate == self.TARGET_SAMPLE_RATE and
                    info.channels == self.TARGET_CHANNELS and
                    info.subtype == 'PCM_16'
                )
                
                if not is_valid:
                    logger.debug(
                        f"Audio format mismatch: "
                        f"rate={info.samplerate} (expected {self.TARGET_SAMPLE_RATE}), "
                        f"channels={info.channels} (expected {self.TARGET_CHANNELS}), "
                        f"subtype={info.subtype} (expected PCM_16)"
                    )
                
                return is_valid
            
            elif PYDUB_AVAILABLE:
                # Use pydub for validation
                audio = AudioSegment.from_file(str(audio_path))
                
                is_valid = (
                    audio.frame_rate == self.TARGET_SAMPLE_RATE and
                    audio.channels == self.TARGET_CHANNELS and
                    audio.sample_width == self.TARGET_SAMPLE_WIDTH
                )
                
                if not is_valid:
                    logger.debug(
                        f"Audio format mismatch: "
                        f"rate={audio.frame_rate} (expected {self.TARGET_SAMPLE_RATE}), "
                        f"channels={audio.channels} (expected {self.TARGET_CHANNELS}), "
                        f"sample_width={audio.sample_width} (expected {self.TARGET_SAMPLE_WIDTH})"
                    )
                
                return is_valid
            
            else:
                logger.warning("No audio library available for validation")
                return False
        
        except Exception as e:
            logger.error(f"Failed to validate audio: {e}")
            return False
    
    def get_audio_info(self, audio_path: Path) -> dict:
        """
        Get audio file information.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio properties
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise AudioProcessingError(f"Audio file not found: {audio_path}")
        
        try:
            if SOUNDFILE_AVAILABLE:
                info = sf.info(str(audio_path))
                return {
                    "sample_rate": info.samplerate,
                    "channels": info.channels,
                    "duration": info.duration,
                    "format": info.format,
                    "subtype": info.subtype
                }
            
            elif PYDUB_AVAILABLE:
                audio = AudioSegment.from_file(str(audio_path))
                return {
                    "sample_rate": audio.frame_rate,
                    "channels": audio.channels,
                    "duration": len(audio) / 1000.0,  # Convert ms to seconds
                    "sample_width": audio.sample_width
                }
            
            else:
                raise AudioProcessingError("No audio library available")
        
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            raise AudioProcessingError(f"Failed to get audio info: {e}")
