"""
Base integration plugin interface.
All integrations must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IntegrationPlugin(ABC):
    """Base class for integration plugins."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.
        
        Args:
            config: Configuration dictionary
        """
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the integration (async for event loops)."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the integration gracefully."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Return plugin name.
        
        Returns:
            Plugin name
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Return plugin status information.
        
        Returns:
            Status dictionary
        """
        pass


class IntegrationError(Exception):
    """Base exception for integration errors."""
    pass
