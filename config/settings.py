"""
Configuration dataclasses for the AI Companion system.
Defines all configuration structures with type hints and default values.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class AppConfig:
    """Main application configuration."""
    mode: str = "voice"  # voice, discord, telegram, unity
    log_level: str = "INFO"
    log_file: str = "logs/companion.log"
    environment: str = "development"  # development, production


@dataclass
class LLMConfig:
    """LLM backend configuration."""
    backend: str = "kobold"  # kobold, openai
    kobold_url: str = "http://localhost:5001/api/v1/generate"
    openai_api_key: Optional[str] = None
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 300
    system_prompt_file: str = "prompts/default.txt"


@dataclass
class TTSConfig:
    """TTS engine configuration."""
    engine: str = "piper"  # piper, pyttsx3, gpt_sovits
    piper_model_path: Optional[str] = None
    voice_index: int = 1
    rate: int = 180
    volume: float = 1.0
    output_dir: str = "Audio/"


@dataclass
class STTConfig:
    """Speech-to-text configuration."""
    language: str = "es-ES"  # Language code for recognition
    energy_threshold: int = 4000
    pause_threshold: float = 0.8


@dataclass
class MemoryConfig:
    """Memory system configuration."""
    storage_path: str = "data/memory.db"
    max_history: int = 20
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.7
    enable_summarization: bool = True
    summary_threshold: int = 100  # Summarize after this many messages


@dataclass
class DiscordConfig:
    """Discord integration configuration."""
    enabled: bool = False
    token: Optional[str] = None
    voice_channel_id: Optional[int] = None
    command_prefix: str = "!"
    ffmpeg_path: str = "ffmpeg"


@dataclass
class TelegramConfig:
    """Telegram integration configuration."""
    enabled: bool = False
    token: Optional[str] = None


@dataclass
class WaniKaniConfig:
    """WaniKani integration configuration."""
    enabled: bool = False
    api_key: Optional[str] = None
    cache_ttl: int = 3600  # Cache time-to-live in seconds
    cache_path: str = "data/wanikani_cache.json"


@dataclass
class UnityConfig:
    """Unity integration configuration."""
    enabled: bool = False
    address: str = "127.0.0.1"
    port: int = 5005
    audio_dir: str = "Audio/"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    openai_requests_per_minute: int = 20
    wanikani_requests_per_minute: int = 60
    user_messages_per_minute: int = 10


@dataclass
class IntegrationsConfig:
    """All integration configurations."""
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    wanikani: WaniKaniConfig = field(default_factory=WaniKaniConfig)
    unity: UnityConfig = field(default_factory=UnityConfig)


@dataclass
class CompanionConfig:
    """Complete application configuration."""
    app: AppConfig = field(default_factory=AppConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    integrations: IntegrationsConfig = field(default_factory=IntegrationsConfig)
    rate_limits: RateLimitConfig = field(default_factory=RateLimitConfig)
