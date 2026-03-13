"""
Speech recognition service using Google Speech Recognition.
Converts speech to text with multi-language support.
"""

from typing import Optional

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

from config.settings import STTConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class SpeechRecognitionError(Exception):
    """Base exception for speech recognition errors."""
    pass


class SpeechRecognizer:
    """Speech-to-text using Google Speech Recognition."""
    
    def __init__(self, config: STTConfig):
        """
        Initialize speech recognizer.
        
        Args:
            config: STT configuration
        """
        if not SR_AVAILABLE:
            raise ImportError(
                "speech_recognition not installed. "
                "Install with: pip install SpeechRecognition"
            )
        
        self.config = config
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = config.energy_threshold
        self.recognizer.pause_threshold = config.pause_threshold
        
        logger.info(f"Speech recognizer initialized (language: {config.language})")
    
    def recognize_from_microphone(
        self,
        timeout: Optional[float] = None,
        phrase_time_limit: Optional[float] = None
    ) -> Optional[str]:
        """
        Capture audio from microphone and recognize speech.
        
        Args:
            timeout: Maximum time to wait for speech to start (seconds)
            phrase_time_limit: Maximum time for phrase (seconds)
            
        Returns:
            Recognized text or None if recognition failed
        """
        try:
            with sr.Microphone() as source:
                logger.info("Listening for speech...")
                
                # Adjust for ambient noise
                logger.debug("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Listen for audio
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                logger.debug("Audio captured, recognizing...")
                
                # Recognize speech
                text = self.recognizer.recognize_google(
                    audio,
                    language=self.config.language
                )
                
                logger.info(f"Recognized: {text}")
                return text
        
        except sr.WaitTimeoutError:
            logger.warning("Listening timed out, no speech detected")
            return None
        
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error in speech recognition: {e}")
            return None
    
    def recognize_from_file(self, audio_file: str) -> Optional[str]:
        """
        Recognize speech from audio file.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Recognized text or None if recognition failed
        """
        try:
            with sr.AudioFile(audio_file) as source:
                logger.debug(f"Loading audio from file: {audio_file}")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                
                # Load audio
                audio = self.recognizer.record(source)
                
                logger.debug("Recognizing speech from file...")
                
                # Recognize speech
                text = self.recognizer.recognize_google(
                    audio,
                    language=self.config.language
                )
                
                logger.info(f"Recognized from file: {text}")
                return text
        
        except sr.UnknownValueError:
            logger.warning("Could not understand audio from file")
            return None
        
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Error recognizing speech from file: {e}")
            return None
    
    def set_language(self, language: str) -> None:
        """
        Set recognition language.
        
        Args:
            language: Language code (e.g., 'en-US', 'es-ES')
        """
        self.config.language = language
        logger.info(f"Language set to: {language}")
    
    def is_available(self) -> bool:
        """
        Check if speech recognizer is available.
        
        Returns:
            True if recognizer is initialized, False otherwise
        """
        return self.recognizer is not None
