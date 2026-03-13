"""
Configuration Manager for loading and validating application configuration.
Supports loading from YAML/JSON files and environment variables.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import asdict

from config.settings import (
    CompanionConfig,
    AppConfig,
    LLMConfig,
    TTSConfig,
    STTConfig,
    MemoryConfig,
    IntegrationsConfig,
    DiscordConfig,
    TelegramConfig,
    WaniKaniConfig,
    UnityConfig,
    RateLimitConfig
)


class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""
    pass


class ConfigurationManager:
    """Manages application configuration from multiple sources."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Load configuration from file and environment variables.
        
        Args:
            config_path: Path to YAML or JSON configuration file
        """
        self.config_path = config_path
        self.config = CompanionConfig()
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration from file and environment variables."""
        # Load from file if provided
        if self.config_path:
            self._load_from_file(self.config_path)
        
        # Override with environment variables
        self._load_from_env()
    
    def _load_from_file(self, config_path: str) -> None:
        """
        Load configuration from YAML or JSON file.
        
        Args:
            config_path: Path to configuration file
        """
        path = Path(config_path)
        
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif path.suffix == '.json':
                    data = json.load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported configuration file format: {path.suffix}. "
                        "Use .yaml, .yml, or .json"
                    )
            
            if data:
                self._apply_config_dict(data)
        
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"Failed to parse configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")
    
    def _apply_config_dict(self, data: Dict[str, Any]) -> None:
        """Apply configuration dictionary to config object."""
        # App config
        if 'app' in data:
            for key, value in data['app'].items():
                if hasattr(self.config.app, key):
                    setattr(self.config.app, key, value)
        
        # LLM config
        if 'llm' in data:
            for key, value in data['llm'].items():
                if hasattr(self.config.llm, key):
                    setattr(self.config.llm, key, value)
        
        # TTS config
        if 'tts' in data:
            for key, value in data['tts'].items():
                if hasattr(self.config.tts, key):
                    setattr(self.config.tts, key, value)
        
        # STT config
        if 'stt' in data:
            for key, value in data['stt'].items():
                if hasattr(self.config.stt, key):
                    setattr(self.config.stt, key, value)
        
        # Memory config
        if 'memory' in data:
            for key, value in data['memory'].items():
                if hasattr(self.config.memory, key):
                    setattr(self.config.memory, key, value)
        
        # Integrations config
        if 'integrations' in data:
            integrations = data['integrations']
            
            if 'discord' in integrations:
                for key, value in integrations['discord'].items():
                    if hasattr(self.config.integrations.discord, key):
                        setattr(self.config.integrations.discord, key, value)
            
            if 'telegram' in integrations:
                for key, value in integrations['telegram'].items():
                    if hasattr(self.config.integrations.telegram, key):
                        setattr(self.config.integrations.telegram, key, value)
            
            if 'wanikani' in integrations:
                for key, value in integrations['wanikani'].items():
                    if hasattr(self.config.integrations.wanikani, key):
                        setattr(self.config.integrations.wanikani, key, value)
            
            if 'unity' in integrations:
                for key, value in integrations['unity'].items():
                    if hasattr(self.config.integrations.unity, key):
                        setattr(self.config.integrations.unity, key, value)
        
        # Rate limits config
        if 'rate_limits' in data:
            for key, value in data['rate_limits'].items():
                if hasattr(self.config.rate_limits, key):
                    setattr(self.config.rate_limits, key, value)
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables (overrides file config)."""
        # App config
        if os.getenv('LOG_LEVEL'):
            self.config.app.log_level = os.getenv('LOG_LEVEL')
        if os.getenv('LOG_FILE'):
            self.config.app.log_file = os.getenv('LOG_FILE')
        if os.getenv('DEFAULT_MODE'):
            self.config.app.mode = os.getenv('DEFAULT_MODE')
        if os.getenv('ENVIRONMENT'):
            self.config.app.environment = os.getenv('ENVIRONMENT')
        
        # LLM config
        if os.getenv('LLM_BACKEND'):
            self.config.llm.backend = os.getenv('LLM_BACKEND')
        if os.getenv('KOBOLD_URL'):
            self.config.llm.kobold_url = os.getenv('KOBOLD_URL')
        if os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY'):
            self.config.llm.openai_api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
        
        # TTS config
        if os.getenv('TTS_ENGINE'):
            self.config.tts.engine = os.getenv('TTS_ENGINE')
        if os.getenv('PIPER_MODEL_PATH'):
            self.config.tts.piper_model_path = os.getenv('PIPER_MODEL_PATH')
        
        # STT config
        if os.getenv('STT_LANGUAGE'):
            self.config.stt.language = os.getenv('STT_LANGUAGE')
        
        # Integration tokens
        if os.getenv('DISCORD_TOKEN'):
            self.config.integrations.discord.token = os.getenv('DISCORD_TOKEN')
        if os.getenv('TELEGRAM_TOKEN') or os.getenv('TELEGRAM_KEY'):
            self.config.integrations.telegram.token = os.getenv('TELEGRAM_TOKEN') or os.getenv('TELEGRAM_KEY')
        if os.getenv('WANIKANI_API_KEY'):
            self.config.integrations.wanikani.api_key = os.getenv('WANIKANI_API_KEY')
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.app.log_level.upper() not in valid_log_levels:
            errors.append(
                f"Invalid log level: {self.config.app.log_level}. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )
        
        # Validate LLM backend
        valid_backends = ['kobold', 'openai']
        if self.config.llm.backend not in valid_backends:
            errors.append(
                f"Invalid LLM backend: {self.config.llm.backend}. "
                f"Must be one of: {', '.join(valid_backends)}"
            )
        
        # Validate OpenAI API key if using OpenAI backend
        if self.config.llm.backend == 'openai' and not self.config.llm.openai_api_key:
            errors.append("OpenAI API key is required when using OpenAI backend")
        
        # Validate OpenAI API key format
        if self.config.llm.openai_api_key:
            if not self.config.llm.openai_api_key.startswith('sk-'):
                errors.append("OpenAI API key must start with 'sk-'")
        
        # Validate TTS engine
        valid_tts_engines = ['piper', 'pyttsx3', 'gpt_sovits']
        if self.config.tts.engine not in valid_tts_engines:
            errors.append(
                f"Invalid TTS engine: {self.config.tts.engine}. "
                f"Must be one of: {', '.join(valid_tts_engines)}"
            )
        
        # Validate Piper model path if using Piper
        if self.config.tts.engine == 'piper' and not self.config.tts.piper_model_path:
            errors.append("Piper model path is required when using Piper TTS engine")
        
        # Validate Discord configuration if enabled
        if self.config.integrations.discord.enabled:
            if not self.config.integrations.discord.token:
                errors.append("Discord token is required when Discord integration is enabled")
        
        # Validate Telegram configuration if enabled
        if self.config.integrations.telegram.enabled:
            if not self.config.integrations.telegram.token:
                errors.append("Telegram token is required when Telegram integration is enabled")
        
        # Validate WaniKani configuration if enabled
        if self.config.integrations.wanikani.enabled:
            if not self.config.integrations.wanikani.api_key:
                errors.append("WaniKani API key is required when WaniKani integration is enabled")
        
        # Validate numeric ranges
        if not 0.0 <= self.config.llm.temperature <= 2.0:
            errors.append("LLM temperature must be between 0.0 and 2.0")
        
        if not 0.0 <= self.config.llm.top_p <= 1.0:
            errors.append("LLM top_p must be between 0.0 and 1.0")
        
        if self.config.llm.max_tokens <= 0:
            errors.append("LLM max_tokens must be positive")
        
        if not 0.0 <= self.config.tts.volume <= 1.0:
            errors.append("TTS volume must be between 0.0 and 1.0")
        
        if self.config.memory.similarity_threshold < 0.0 or self.config.memory.similarity_threshold > 1.0:
            errors.append("Memory similarity threshold must be between 0.0 and 1.0")
        
        return errors
    
    def get_app_config(self) -> AppConfig:
        """Get application configuration."""
        return self.config.app
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM backend configuration."""
        return self.config.llm
    
    def get_tts_config(self) -> TTSConfig:
        """Get TTS engine configuration."""
        return self.config.tts
    
    def get_stt_config(self) -> STTConfig:
        """Get STT configuration."""
        return self.config.stt
    
    def get_memory_config(self) -> MemoryConfig:
        """Get memory system configuration."""
        return self.config.memory
    
    def get_integrations_config(self) -> IntegrationsConfig:
        """Get integrations configuration."""
        return self.config.integrations
    
    def get_rate_limit_config(self) -> RateLimitConfig:
        """Get rate limit configuration."""
        return self.config.rate_limits
    
    def get_full_config(self) -> CompanionConfig:
        """Get complete configuration."""
        return self.config
