"""
Plugin manager for handling optional integrations.
Manages loading, starting, and stopping integration plugins.
"""

from typing import Dict, List, Optional
from pathlib import Path
import importlib
import sys

from utils.logging_config import get_logger


logger = get_logger(__name__)


class PluginManager:
    """Manages integration plugins."""
    
    def __init__(self):
        """Initialize plugin manager."""
        self.plugins: Dict[str, 'IntegrationPlugin'] = {}
        logger.info("Plugin manager initialized")
    
    def register_plugin(self, name: str, plugin: 'IntegrationPlugin') -> None:
        """
        Register a plugin.
        
        Args:
            name: Plugin name
            plugin: Plugin instance
        """
        self.plugins[name] = plugin
        logger.info(f"Registered plugin: {name}")
    
    def load_plugins(self, plugin_configs: Dict[str, dict]) -> None:
        """
        Load plugins from configuration.
        
        Args:
            plugin_configs: Dictionary of plugin configurations
        """
        for name, config in plugin_configs.items():
            if not config.get('enabled', False):
                logger.debug(f"Plugin {name} is disabled, skipping")
                continue
            
            try:
                # Try to import and initialize plugin
                plugin_instance = self._load_plugin(name, config)
                if plugin_instance:
                    self.register_plugin(name, plugin_instance)
            except ImportError as e:
                logger.warning(f"Plugin {name} dependencies not installed: {e}")
                logger.info(f"To use {name}, install required dependencies")
            except Exception as e:
                logger.error(f"Failed to load plugin {name}: {e}")
    
    def _load_plugin(self, name: str, config: dict) -> Optional['IntegrationPlugin']:
        """
        Load a specific plugin.
        
        Args:
            name: Plugin name
            config: Plugin configuration
            
        Returns:
            Plugin instance or None if failed
        """
        # Map plugin names to module paths
        plugin_map = {
            'discord': 'integrations.discord.discord_bot.DiscordIntegration',
            'telegram': 'integrations.telegram.telegram_bot.TelegramIntegration',
            'wanikani': 'integrations.wanikani.wanikani_integration.WaniKaniIntegration',
            'unity': 'integrations.unity.unity_integration.UnityIntegration',
        }
        
        if name not in plugin_map:
            logger.warning(f"Unknown plugin: {name}")
            return None
        
        module_path, class_name = plugin_map[name].rsplit('.', 1)
        
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            
            # Instantiate plugin
            plugin_instance = plugin_class()
            plugin_instance.initialize(config)
            
            return plugin_instance
        
        except ImportError as e:
            # Missing dependencies
            raise ImportError(f"Missing dependencies for {name}: {e}")
        except Exception as e:
            logger.error(f"Error loading plugin {name}: {e}")
            return None
    
    def start_plugins(self) -> None:
        """Start all registered plugins."""
        for name, plugin in self.plugins.items():
            try:
                logger.info(f"Starting plugin: {name}")
                plugin.start()
            except Exception as e:
                logger.error(f"Failed to start plugin {name}: {e}")
    
    def stop_plugins(self) -> None:
        """Stop all registered plugins."""
        for name, plugin in self.plugins.items():
            try:
                logger.info(f"Stopping plugin: {name}")
                plugin.stop()
            except Exception as e:
                logger.error(f"Error stopping plugin {name}: {e}")
    
    def get_plugin_status(self) -> Dict[str, str]:
        """
        Get status of all plugins.
        
        Returns:
            Dictionary mapping plugin names to status strings
        """
        status = {}
        for name, plugin in self.plugins.items():
            try:
                status[name] = plugin.get_status()
            except Exception as e:
                status[name] = f"error: {e}"
        
        return status
    
    def get_plugin(self, name: str) -> Optional['IntegrationPlugin']:
        """
        Get a specific plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(name)
