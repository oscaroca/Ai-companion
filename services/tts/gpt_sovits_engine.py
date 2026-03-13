"""
GPT-SoVITS TTS Engine
High-quality neural TTS using GPT-SoVITS API.
"""

import requests
from pathlib import Path
from typing import List, Optional
import time

from services.tts.base import TTSEngine
from services.audio.audio_processor import AudioProcessor
from config.settings import TTSConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class GPTSoVITSEngine(TTSEngine):
    """GPT-SoVITS TTS engine using API server."""
    
    def __init__(self, config: TTSConfig, audio_processor: AudioProcessor):
        """
        Initialize GPT-SoVITS engine.
        
        Args:
            config: TTS configuration
            audio_processor: Audio processor for normalization
        """
        self.config = config
        self.audio_processor = audio_processor
        
        # GPT-SoVITS API configuration
        self.api_url = getattr(config, 'gpt_sovits_api_url', 'http://127.0.0.1:9880')
        self.ref_audio_path = getattr(config, 'gpt_sovits_ref_audio', 'reference.wav')
        self.prompt_text = getattr(config, 'gpt_sovits_prompt_text', '')
        self.prompt_lang = getattr(config, 'gpt_sovits_prompt_lang', 'en')
        self.text_lang = getattr(config, 'gpt_sovits_text_lang', 'en')
        
        # Generation parameters
        self.top_k = getattr(config, 'gpt_sovits_top_k', 5)
        self.top_p = getattr(config, 'gpt_sovits_top_p', 1.0)
        self.temperature = getattr(config, 'gpt_sovits_temperature', 1.0)
        self.speed_factor = getattr(config, 'gpt_sovits_speed_factor', 1.0)
        
        # Output directory
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if API server is running
        self._check_api_server()
        
        logger.info(f"GPT-SoVITS engine initialized (API: {self.api_url})")
    
    def _check_api_server(self) -> bool:
        """
        Check if GPT-SoVITS API server is running.
        
        Returns:
            True if server is accessible, False otherwise
        """
        try:
            response = requests.get(f"{self.api_url}/", timeout=2)
            logger.info("GPT-SoVITS API server is running")
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"GPT-SoVITS API server not accessible: {e}")
            logger.warning("Start the server with: python GPT-SoVITS-v3lora-20250228/api_v2.py")
            return False
    
    def synthesize(self, text: str, output_path: Path) -> None:
        """
        Synthesize speech from text using GPT-SoVITS API.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            
        Raises:
            RuntimeError: If synthesis fails
        """
        try:
            logger.debug(f"Synthesizing with GPT-SoVITS: {text[:50]}...")
            
            # Prepare API request
            payload = {
                "text": text,
                "text_lang": self.text_lang,
                "ref_audio_path": self.ref_audio_path,
                "prompt_text": self.prompt_text,
                "prompt_lang": self.prompt_lang,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "temperature": self.temperature,
                "text_split_method": "cut5",
                "batch_size": 1,
                "speed_factor": self.speed_factor,
                "streaming_mode": False,
                "media_type": "wav"
            }
            
            # Call GPT-SoVITS API
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/tts",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"GPT-SoVITS API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data}"
                except:
                    error_msg += f" - {response.text}"
                raise RuntimeError(error_msg)
            
            # Save raw audio
            temp_path = output_path.with_suffix('.temp.wav')
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Normalize audio for Unity/Discord compatibility
            self.audio_processor.normalize_audio(temp_path, output_path)
            
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            
            elapsed = time.time() - start_time
            logger.info(f"GPT-SoVITS synthesis completed in {elapsed:.2f}s")
        
        except requests.exceptions.Timeout:
            raise RuntimeError("GPT-SoVITS API timeout - synthesis took too long")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Cannot connect to GPT-SoVITS API server. "
                "Start it with: python GPT-SoVITS-v3lora-20250228/api_v2.py"
            )
        except Exception as e:
            logger.error(f"GPT-SoVITS synthesis error: {e}")
            raise RuntimeError(f"GPT-SoVITS synthesis failed: {e}")
    
    def get_voices(self) -> List[str]:
        """
        Get available voices (reference audios).
        
        Returns:
            List of available voice names
        """
        # GPT-SoVITS uses reference audio files
        # Return the configured reference audio
        return [self.ref_audio_path]
    
    def set_voice(self, voice_name: str) -> None:
        """
        Set the voice (reference audio) to use.
        
        Args:
            voice_name: Path to reference audio file
        """
        self.ref_audio_path = voice_name
        logger.info(f"GPT-SoVITS reference audio set to: {voice_name}")
    
    def set_prompt(self, prompt_text: str, prompt_lang: str = "en") -> None:
        """
        Set the prompt text for the reference audio.
        
        Args:
            prompt_text: Text that matches the reference audio
            prompt_lang: Language of the prompt text
        """
        self.prompt_text = prompt_text
        self.prompt_lang = prompt_lang
        logger.info(f"GPT-SoVITS prompt set: {prompt_text[:50]}...")
