"""
Unity integration plugin.
Observes conversation events and triggers Unity animations.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from services.animation.animation_controller import AnimationController
from core.conversation_manager import ConversationObserver, ConversationResponse
from config.settings import UnityConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class UnityIntegration(ConversationObserver):
    """Unity integration plugin that observes conversation events."""
    
    def __init__(self):
        """Initialize Unity integration."""
        self.controller: Optional[AnimationController] = None
        self.config: Optional[UnityConfig] = None
        self._status = "not_initialized"
        logger.info("Unity integration created")
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        try:
            # Convert dict to UnityConfig
            self.config = UnityConfig(
                enabled=config.get('enabled', False),
                address=config.get('address', '127.0.0.1'),
                port=config.get('port', 5005),
                audio_dir=config.get('audio_dir', 'Audio/')
            )
            
            # Initialize animation controller
            self.controller = AnimationController(self.config)
            self._status = "initialized"
            logger.info(f"Unity integration initialized (UDP {self.config.address}:{self.config.port})")
        
        except Exception as e:
            logger.error(f"Failed to initialize Unity integration: {e}")
            self._status = f"error: {e}"
            raise
    
    def start(self) -> None:
        """Start the plugin."""
        if not self.controller:
            raise RuntimeError("Unity integration not initialized")
        
        logger.info("Unity integration started")
        self._status = "running"
    
    def stop(self) -> None:
        """Stop the plugin."""
        logger.info("Unity integration stopped")
        self._status = "stopped"
    
    def get_name(self) -> str:
        """
        Get plugin name.
        
        Returns:
            Plugin name
        """
        return "unity"
    
    def get_status(self) -> str:
        """
        Get plugin status.
        
        Returns:
            Status string
        """
        return self._status
    
    # ConversationObserver methods
    
    def on_message_sent(self, user_id: str, message: str) -> None:
        """
        Called when user sends a message.
        
        Args:
            user_id: User identifier
            message: User message
        """
        # Could trigger "listening" animation here
        pass
    
    def on_response_generated(self, user_id: str, response: ConversationResponse) -> None:
        """
        Called when response is generated.
        
        Args:
            user_id: User identifier
            response: Generated response
        """
        if not self.controller:
            return
        
        try:
            # Get animation ID from response or select based on text
            animation_id = response.animation_id
            if animation_id is None:
                animation_id = self.controller.get_animation_for_sentiment(response.text)
            
            # Get audio filename if available
            audio_filename = None
            if response.audio_path:
                audio_filename = Path(response.audio_path).name
            
            # Trigger animation
            self.controller.trigger_animation(animation_id, audio_filename)
            logger.debug(f"Triggered Unity animation {animation_id} with audio {audio_filename}")
        
        except Exception as e:
            logger.error(f"Failed to trigger Unity animation: {e}")
