"""
Telegram bot integration for AI Companion.
Supports text conversations with per-user context.
"""

from typing import Optional, Dict, Any

try:
    from telegram import Update
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

from integrations.base_integration import IntegrationPlugin, IntegrationError
from core.conversation_manager import ConversationManager
from config.settings import TelegramConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class TelegramIntegration(IntegrationPlugin):
    """Telegram bot integration."""
    
    def __init__(self, conversation_manager: ConversationManager):
        """
        Initialize Telegram integration.
        
        Args:
            conversation_manager: Conversation manager instance
        """
        if not TELEGRAM_AVAILABLE:
            raise IntegrationError(
                "python-telegram-bot not installed. "
                "Install with: pip install python-telegram-bot"
            )
        
        self.conversation = conversation_manager
        self.config: Optional[TelegramConfig] = None
        self.app = None
        self.running = False
        
        logger.info("Telegram integration created")
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.
        
        Args:
            config: Configuration dictionary
        """
        # Convert dict to TelegramConfig
        self.config = TelegramConfig(**config)
        
        if not self.config.token:
            raise IntegrationError("Telegram token is required")
        
        # Build application
        self.app = ApplicationBuilder().token(self.config.token).build()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Telegram integration initialized")
    
    def _register_handlers(self) -> None:
        """Register Telegram message and command handlers."""
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(CommandHandler("help", self._help_command))
        self.app.add_handler(CommandHandler("reset", self._reset_command))
        self.app.add_handler(CommandHandler("status", self._status_command))
        
        # Message handler (for all text messages)
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )
        
        logger.debug("Telegram handlers registered")
    
    async def _start_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        await update.message.reply_text(
            "👋 Hello! I'm your AI Companion.\n\n"
            "Send me a message to start chatting!\n\n"
            "Commands:\n"
            "/help - Show help\n"
            "/reset - Reset conversation\n"
            "/status - Show status"
        )
        logger.info(f"User {update.effective_user.id} started bot")
    
    async def _help_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /help command."""
        await update.message.reply_text(
            "🤖 AI Companion Help\n\n"
            "Just send me any message and I'll respond!\n\n"
            "Available commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/reset - Reset our conversation\n"
            "/status - Show bot status"
        )
    
    async def _reset_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /reset command."""
        user_id = f"telegram_{update.effective_user.id}"
        self.conversation.reset_conversation(user_id)
        
        await update.message.reply_text(
            "✅ Conversation reset! Let's start fresh."
        )
        logger.info(f"Reset conversation for user {update.effective_user.id}")
    
    async def _status_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /status command."""
        metrics = self.conversation.get_metrics()
        
        status_text = (
            "📊 Bot Status\n\n"
            f"Total messages: {metrics['total_messages']}\n"
            f"Errors: {metrics['total_errors']}\n"
            f"Avg response time: {metrics['avg_llm_response_time']:.2f}s\n"
            f"Error rate: {metrics['error_rate']:.1%}"
        )
        
        await update.message.reply_text(status_text)
    
    async def _handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle incoming text message.
        
        Args:
            update: Telegram update object
            context: Telegram context
        """
        try:
            user_text = update.message.text
            user_id = f"telegram_{update.effective_user.id}"
            
            logger.debug(f"Message from {update.effective_user.username}: {user_text}")
            
            # Show typing indicator
            await update.message.chat.send_action("typing")
            
            # Generate response
            response = self.conversation.send_message(
                user_id=user_id,
                message=user_text,
                generate_audio=False  # Telegram doesn't need audio
            )
            
            # Send response
            await update.message.reply_text(response.text)
            
            logger.debug(f"Sent response to {update.effective_user.username}")
        
        except Exception as e:
            logger.error(f"Error handling Telegram message: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an error processing your message. Please try again."
            )
    
    async def start(self) -> None:
        """Start the Telegram bot."""
        if not self.app or not self.config:
            raise IntegrationError("Telegram integration not initialized")
        
        logger.info("Starting Telegram bot...")
        self.running = True
        
        try:
            # Start polling
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            logger.info("Telegram bot started successfully")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Telegram bot error: {e}")
            raise IntegrationError(f"Failed to start Telegram bot: {e}")
    
    async def stop(self) -> None:
        """Stop the Telegram bot."""
        logger.info("Stopping Telegram bot...")
        self.running = False
        
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        
        logger.info("Telegram bot stopped")
    
    def get_name(self) -> str:
        """Return plugin name."""
        return "telegram"
    
    def get_status(self) -> Dict[str, Any]:
        """Return plugin status."""
        return {
            "name": "telegram",
            "running": self.running,
            "connected": self.app is not None
        }


# Need to import asyncio for the sleep in start()
import asyncio
