"""
WaniKani integration plugin.
Provides learned vocabulary and kanji to conversation context.
"""

from typing import Dict, Any, Optional
from integrations.wanikani.wanikani_client import WaniKaniClient
from config.settings import WaniKaniConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class WaniKaniIntegration:
    """WaniKani integration plugin."""
    
    def __init__(self):
        """Initialize WaniKani integration."""
        self.client: Optional[WaniKaniClient] = None
        self.config: Optional[WaniKaniConfig] = None
        self._status = "not_initialized"
        logger.info("WaniKani integration created")
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        try:
            # Convert dict to WaniKaniConfig
            self.config = WaniKaniConfig(
                enabled=config.get('enabled', False),
                api_key=config.get('api_key', ''),
                cache_ttl=config.get('cache_ttl', 3600),
                cache_path=config.get('cache_path', 'data/wanikani_cache.json')
            )
            
            # Initialize client
            self.client = WaniKaniClient(self.config)
            self._status = "initialized"
            logger.info("WaniKani integration initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize WaniKani integration: {e}")
            self._status = f"error: {e}"
            raise
    
    def start(self) -> None:
        """Start the plugin."""
        if not self.client:
            raise RuntimeError("WaniKani integration not initialized")
        
        try:
            # Fetch learned items to verify connection
            items = self.client.fetch_learned_items()
            logger.info(f"WaniKani integration started ({len(items)} learned items)")
            self._status = "running"
        
        except Exception as e:
            logger.error(f"Failed to start WaniKani integration: {e}")
            self._status = f"error: {e}"
            raise
    
    def stop(self) -> None:
        """Stop the plugin."""
        logger.info("WaniKani integration stopped")
        self._status = "stopped"
    
    def get_name(self) -> str:
        """
        Get plugin name.
        
        Returns:
            Plugin name
        """
        return "wanikani"
    
    def get_status(self) -> str:
        """
        Get plugin status.
        
        Returns:
            Status string
        """
        return self._status
    
    def get_learned_items(self) -> list:
        """
        Get learned vocabulary and kanji.
        
        Returns:
            List of learned items
        """
        if not self.client:
            return []
        
        try:
            return self.client.fetch_learned_items()
        except Exception as e:
            logger.error(f"Failed to fetch learned items: {e}")
            return []
    
    def get_context_string(self) -> str:
        """
        Get formatted context string for LLM.
        
        Returns:
            Formatted context string
        """
        if not self.client:
            return ""
        
        try:
            items = self.client.fetch_learned_items()
            return self.client.format_for_context(items)
        except Exception as e:
            logger.error(f"Failed to get context string: {e}")
            return ""
