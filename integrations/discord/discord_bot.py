"""
Discord bot integration for AI Companion.
Supports text commands and voice channel audio playback.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

from integrations.base_integration import IntegrationPlugin, IntegrationError
from core.conversation_manager import ConversationManager
from config.settings import DiscordConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class DiscordIntegration(IntegrationPlugin):
    """Discord bot integration."""
    
    def __init__(self, conversation_manager: ConversationManager):
        """
        Initialize Discord integration.
        
        Args:
            conversation_manager: Conversation manager instance
        """
        if not DISCORD_AVAILABLE:
            raise IntegrationError(
                "discord.py not installed. Install with: pip install discord.py"
            )
        
        self.conversation = conversation_manager
        self.config: Optional[DiscordConfig] = None
        self.bot: Optional[commands.Bot] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.running = False
        
        logger.info("Discord integration created")
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.
        
        Args:
            config: Configuration dictionary
        """
        # Convert dict to DiscordConfig
        self.config = DiscordConfig(**config)
        
        if not self.config.token:
            raise IntegrationError("Discord token is required")
        
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        # Create bot
        self.bot = commands.Bot(
            command_prefix=self.config.command_prefix,
            intents=intents
        )
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("Discord integration initialized")
    
    def _register_handlers(self) -> None:
        """Register Discord event handlers and commands."""
        
        @self.bot.event
        async def on_ready():
            logger.info(f"Discord bot ready: {self.bot.user}")
            
            # Auto-join voice channel if configured
            if self.config.voice_channel_id:
                await self._auto_join_voice()
        
        @self.bot.event
        async def on_message(message: discord.Message):
            # Ignore bot's own messages
            if message.author == self.bot.user:
                return
            
            # Process commands first
            await self.bot.process_commands(message)
            
            # If not a command and bot is mentioned, respond
            if self.bot.user in message.mentions:
                await self._handle_message(message)
        
        @self.bot.command(name="join")
        async def join_voice(ctx: commands.Context):
            """Join the voice channel of the user."""
            if ctx.author.voice:
                channel = ctx.author.voice.channel
                self.voice_client = await channel.connect()
                await ctx.send(f"Joined {channel.name}!")
                logger.info(f"Joined voice channel: {channel.name}")
            else:
                await ctx.send("You are not in a voice channel!")
        
        @self.bot.command(name="leave")
        async def leave_voice(ctx: commands.Context):
            """Leave the voice channel."""
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.disconnect()
                self.voice_client = None
                await ctx.send("Disconnected from voice channel!")
                logger.info("Left voice channel")
            else:
                await ctx.send("I'm not in a voice channel!")
        
        @self.bot.command(name="talk")
        async def talk(ctx: commands.Context, *, message: str):
            """Talk to the AI companion."""
            await self._handle_message(ctx.message, message)
        
        @self.bot.command(name="reset")
        async def reset(ctx: commands.Context):
            """Reset conversation history."""
            user_id = f"discord_{ctx.author.id}"
            self.conversation.reset_conversation(user_id)
            await ctx.send("Conversation reset!")
    
    async def _auto_join_voice(self) -> None:
        """Auto-join configured voice channel."""
        try:
            if not self.bot.guilds:
                logger.warning("No guilds available for auto-join")
                return
            
            guild = self.bot.guilds[0]
            channel = guild.get_channel(self.config.voice_channel_id)
            
            if channel and isinstance(channel, discord.VoiceChannel):
                self.voice_client = await channel.connect()
                logger.info(f"Auto-joined voice channel: {channel.name}")
            else:
                logger.warning(f"Voice channel not found: {self.config.voice_channel_id}")
        
        except Exception as e:
            logger.error(f"Failed to auto-join voice channel: {e}")
    
    async def _handle_message(
        self,
        message: discord.Message,
        text: Optional[str] = None
    ) -> None:
        """
        Handle incoming message.
        
        Args:
            message: Discord message object
            text: Optional text override
        """
        try:
            # Get message text
            user_text = text or message.content
            
            # Remove bot mention
            user_text = user_text.replace(f"<@{self.bot.user.id}>", "").strip()
            
            if not user_text:
                return
            
            # Show typing indicator
            async with message.channel.typing():
                # Get user ID
                user_id = f"discord_{message.author.id}"
                
                # Generate response
                response = self.conversation.send_message(
                    user_id=user_id,
                    message=user_text,
                    generate_audio=self.voice_client is not None
                )
                
                # Send text response
                await message.channel.send(response.text)
                
                # Play audio in voice channel if available
                if response.audio_path and self.voice_client:
                    await self._play_audio(response.audio_path)
        
        except Exception as e:
            logger.error(f"Error handling Discord message: {e}")
            await message.channel.send("Sorry, I encountered an error processing your message.")
    
    async def _play_audio(self, audio_path: Path) -> None:
        """
        Play audio in voice channel.
        
        Args:
            audio_path: Path to audio file
        """
        if not self.voice_client or not self.voice_client.is_connected():
            logger.warning("Not connected to voice channel")
            return
        
        try:
            # Stop current audio if playing
            if self.voice_client.is_playing():
                self.voice_client.stop()
            
            # Play audio
            audio_source = discord.FFmpegPCMAudio(
                str(audio_path),
                executable=self.config.ffmpeg_path
            )
            
            self.voice_client.play(audio_source)
            
            logger.debug(f"Playing audio in Discord: {audio_path}")
        
        except Exception as e:
            logger.error(f"Failed to play audio in Discord: {e}")
    
    async def start(self) -> None:
        """Start the Discord bot."""
        if not self.bot or not self.config:
            raise IntegrationError("Discord integration not initialized")
        
        logger.info("Starting Discord bot...")
        self.running = True
        
        try:
            await self.bot.start(self.config.token)
        except Exception as e:
            logger.error(f"Discord bot error: {e}")
            raise IntegrationError(f"Failed to start Discord bot: {e}")
    
    async def stop(self) -> None:
        """Stop the Discord bot."""
        logger.info("Stopping Discord bot...")
        self.running = False
        
        if self.voice_client:
            await self.voice_client.disconnect()
        
        if self.bot:
            await self.bot.close()
        
        logger.info("Discord bot stopped")
    
    def get_name(self) -> str:
        """Return plugin name."""
        return "discord"
    
    def get_status(self) -> Dict[str, Any]:
        """Return plugin status."""
        return {
            "name": "discord",
            "running": self.running,
            "connected": self.bot is not None and not self.bot.is_closed() if self.bot else False,
            "in_voice": self.voice_client is not None and self.voice_client.is_connected() if self.voice_client else False
        }
