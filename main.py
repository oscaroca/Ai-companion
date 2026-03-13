#!/usr/bin/env python3
"""
AI Companion - Unified Entry Point
Main application entry point supporting multiple execution modes.
"""

import sys
import argparse
import signal
from pathlib import Path
from typing import List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config_manager import ConfigurationManager, ConfigurationError
from utils.logging_config import setup_logging, get_logger
from core.conversation_manager import ConversationManager
from core.memory_system import MemorySystem
from services.llm.kobold_backend import KoboldBackend
from services.llm.openai_backend import OpenAIBackend
from services.tts.piper_engine import PiperEngine
from services.tts.pyttsx3_engine import Pyttsx3Engine
from services.tts.gpt_sovits_engine import GPTSoVITSEngine
from services.audio.audio_processor import AudioProcessor
from services.stt.speech_recognizer import SpeechRecognizer
from services.animation.animation_controller import AnimationController
from integrations.wanikani.wanikani_client import WaniKaniClient
from integrations.discord.discord_bot import DiscordIntegration
from integrations.telegram.telegram_bot import TelegramIntegration


logger = None  # Will be initialized after config loading


class CompanionApp:
    """Main application class."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize application.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        try:
            self.config_manager = ConfigurationManager(config_path)
            errors = self.config_manager.validate()
            if errors:
                print("Configuration errors:")
                for error in errors:
                    print(f"  - {error}")
                sys.exit(1)
        except ConfigurationError as e:
            print(f"Configuration error: {e}")
            sys.exit(1)
        
        # Setup logging
        app_config = self.config_manager.get_app_config()
        global logger
        logger = setup_logging(
            log_level=app_config.log_level,
            log_file=app_config.log_file
        )
        
        logger.info("=" * 60)
        logger.info("AI Companion Starting")
        logger.info("=" * 60)
        
        # Initialize components
        self.conversation_manager = None
        self.speech_recognizer = None
        self.running = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def initialize(self):
        """Initialize all components."""
        logger.info("Initializing components...")
        
        # Initialize LLM backend
        llm_config = self.config_manager.get_llm_config()
        logger.info(f"Initializing LLM backend: {llm_config.backend}")
        
        # Load system prompt if specified
        system_prompt = ""
        if llm_config.system_prompt_file:
            prompt_path = Path(llm_config.system_prompt_file)
            if prompt_path.exists():
                system_prompt = prompt_path.read_text(encoding='utf-8')
                logger.info(f"Loaded system prompt from {llm_config.system_prompt_file}")
            
            # Add WaniKani context if enabled
            integrations_config = self.config_manager.get_integrations_config()
            if integrations_config.wanikani.enabled and integrations_config.wanikani.api_key:
                try:
                    wanikani_client = WaniKaniClient(integrations_config.wanikani)
                    learned_items = wanikani_client.fetch_learned_items()
                    wanikani_context = wanikani_client.format_for_context(learned_items)
                    system_prompt = f"{system_prompt}\n\n{wanikani_context}"
                    logger.info(f"Added WaniKani context ({len(learned_items)} items)")
                except Exception as e:
                    logger.warning(f"Failed to load WaniKani context: {e}")
        
        if llm_config.backend == "kobold":
            llm_backend = KoboldBackend(llm_config, system_prompt)
        elif llm_config.backend == "openai":
            llm_backend = OpenAIBackend(llm_config, system_prompt)
        else:
            raise ValueError(f"Unknown LLM backend: {llm_config.backend}")
        
        # Initialize memory system
        memory_config = self.config_manager.get_memory_config()
        logger.info("Initializing memory system...")
        memory_system = MemorySystem(memory_config)
        
        # Initialize TTS engine
        tts_config = self.config_manager.get_tts_config()
        logger.info(f"Initializing TTS engine: {tts_config.engine}")
        
        audio_processor = AudioProcessor()
        
        if tts_config.engine == "piper":
            tts_engine = PiperEngine(tts_config, audio_processor)
        elif tts_config.engine == "pyttsx3":
            tts_engine = Pyttsx3Engine(tts_config, audio_processor)
        elif tts_config.engine == "gpt_sovits":
            tts_engine = GPTSoVITSEngine(tts_config, audio_processor)
        else:
            logger.warning(f"Unknown TTS engine: {tts_config.engine}, TTS disabled")
            tts_engine = None
        
        # Initialize animation controller if Unity enabled
        animation_controller = None
        integrations_config = self.config_manager.get_integrations_config()
        if integrations_config.unity.enabled:
            try:
                animation_controller = AnimationController(integrations_config.unity)
                logger.info("Animation controller initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize animation controller: {e}")
        
        # Initialize conversation manager
        self.conversation_manager = ConversationManager(
            llm_backend=llm_backend,
            memory_system=memory_system,
            tts_engine=tts_engine,
            animation_controller=animation_controller
        )
        
        # Initialize speech recognizer for voice mode
        stt_config = self.config_manager.get_stt_config()
        self.speech_recognizer = SpeechRecognizer(stt_config)
        
        logger.info("All components initialized successfully")
    
    def run_voice_mode(self):
        """Run in voice interaction mode."""
        logger.info("Starting voice mode...")
        print("\n" + "=" * 60)
        print("AI Companion - Voice Mode")
        print("=" * 60)
        print("Speak to interact with the AI companion.")
        print("Press Ctrl+C to exit.")
        print("=" * 60 + "\n")
        
        self.running = True
        user_id = "voice_user"
        
        while self.running:
            try:
                # Listen for speech
                user_input = self.speech_recognizer.recognize_from_microphone(timeout=10)
                
                if user_input:
                    print(f"\nYou: {user_input}")
                    
                    # Get response
                    response = self.conversation_manager.send_message(
                        user_id=user_id,
                        message=user_input,
                        generate_audio=True
                    )
                    
                    print(f"AI: {response.text}\n")
                    
                    # Play audio if available
                    if response.audio_path:
                        logger.info(f"Audio saved to: {response.audio_path}")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in voice mode: {e}")
                print(f"Error: {e}\n")
        
        logger.info("Voice mode stopped")
    
    def run_text_mode(self):
        """Run in text interaction mode (for testing)."""
        logger.info("Starting text mode...")
        print("\n" + "=" * 60)
        print("AI Companion - Text Mode")
        print("=" * 60)
        print("Type your messages to interact with the AI companion.")
        print("Type 'exit' or 'quit' to exit.")
        print("=" * 60 + "\n")
        
        self.running = True
        user_id = "text_user"
        
        while self.running:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                if not user_input:
                    continue
                
                # Get response
                response = self.conversation_manager.send_message(
                    user_id=user_id,
                    message=user_input,
                    generate_audio=False
                )
                
                print(f"AI: {response.text}\n")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in text mode: {e}")
                print(f"Error: {e}\n")
        
        logger.info("Text mode stopped")
    
    def run_discord_mode(self):
        """Run Discord bot mode."""
        logger.info("Starting Discord mode...")
        
        integrations_config = self.config_manager.get_integrations_config()
        
        if not integrations_config.discord.enabled:
            print("Discord integration is not enabled in configuration")
            print("Enable it in config/default_config.yaml or set DISCORD_TOKEN in .env")
            return
        
        try:
            # Create Discord integration
            discord_bot = DiscordIntegration(self.conversation_manager)
            discord_bot.initialize(integrations_config.discord.__dict__)
            
            print("\n" + "=" * 60)
            print("AI Companion - Discord Bot Mode")
            print("=" * 60)
            print("Discord bot is starting...")
            print("Press Ctrl+C to stop.")
            print("=" * 60 + "\n")
            
            # Run Discord bot (blocking)
            import asyncio
            asyncio.run(discord_bot.start())
        
        except KeyboardInterrupt:
            logger.info("Discord bot interrupted by user")
        except Exception as e:
            logger.error(f"Discord bot error: {e}")
            print(f"Error: {e}")
    
    def run_telegram_mode(self):
        """Run Telegram bot mode."""
        logger.info("Starting Telegram mode...")
        
        integrations_config = self.config_manager.get_integrations_config()
        
        if not integrations_config.telegram.enabled:
            print("Telegram integration is not enabled in configuration")
            print("Enable it in config/default_config.yaml or set TELEGRAM_TOKEN in .env")
            return
        
        try:
            # Create Telegram integration
            telegram_bot = TelegramIntegration(self.conversation_manager)
            telegram_bot.initialize(integrations_config.telegram.__dict__)
            
            print("\n" + "=" * 60)
            print("AI Companion - Telegram Bot Mode")
            print("=" * 60)
            print("Telegram bot is starting...")
            print("Press Ctrl+C to stop.")
            print("=" * 60 + "\n")
            
            # Run Telegram bot (blocking)
            import asyncio
            asyncio.run(telegram_bot.start())
        
        except KeyboardInterrupt:
            logger.info("Telegram bot interrupted by user")
        except Exception as e:
            logger.error(f"Telegram bot error: {e}")
            print(f"Error: {e}")
    
    def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down...")
        self.running = False
        
        # Close memory system
        if self.conversation_manager and self.conversation_manager.memory:
            self.conversation_manager.memory.close()
        
        logger.info("Shutdown complete")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="AI Companion - Multi-modal AI assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run in default mode (from config)
  python main.py --mode voice       # Run in voice mode
  python main.py --mode text        # Run in text mode
  python main.py --config custom.yaml  # Use custom config file
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["voice", "text", "discord", "telegram", "unity"],
        help="Execution mode (overrides config default)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: config/default_config.yaml)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="AI Companion v1.0.0"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Determine config path
    config_path = args.config or "config/default_config.yaml"
    
    # Initialize application
    try:
        app = CompanionApp(config_path)
        app.initialize()
    except Exception as e:
        print(f"Failed to initialize application: {e}")
        sys.exit(1)
    
    # Determine execution mode
    mode = args.mode or app.config_manager.get_app_config().mode
    
    # Run in specified mode
    try:
        if mode == "voice":
            app.run_voice_mode()
        elif mode == "text":
            app.run_text_mode()
        elif mode == "discord":
            app.run_discord_mode()
        elif mode == "telegram":
            app.run_telegram_mode()
        elif mode == "unity":
            print("Unity mode runs alongside other modes via animation controller")
            print("Start with --mode voice or --mode text to use Unity integration")
        else:
            print(f"Unknown mode: {mode}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
