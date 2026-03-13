"""
Conversation manager orchestrating LLM, memory, TTS, and animations.
Coordinates the complete conversation flow.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Protocol
from datetime import datetime

from services.llm.base import LLMBackend, LLMResponse
from core.memory_system import MemorySystem, Message
from services.tts.base import TTSEngine
from utils.validators import InputValidator, ValidationError
from utils.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class ConversationResponse:
    """Response from conversation manager."""
    text: str
    audio_path: Optional[Path] = None
    animation_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationObserver(Protocol):
    """Protocol for conversation event observers."""
    
    def on_message_sent(self, user_id: str, message: str) -> None:
        """Called when user sends a message."""
        ...
    
    def on_response_generated(self, user_id: str, response: ConversationResponse) -> None:
        """Called when response is generated."""
        ...


class ConversationManager:
    """Manages conversation flow and coordinates components."""
    
    def __init__(
        self,
        llm_backend: LLMBackend,
        memory_system: MemorySystem,
        tts_engine: Optional[TTSEngine] = None,
        animation_controller: Optional[Any] = None  # AnimationController
    ):
        """
        Initialize conversation manager.
        
        Args:
            llm_backend: LLM backend for generating responses
            memory_system: Memory system for storing/retrieving history
            tts_engine: Optional TTS engine for audio generation
            animation_controller: Optional animation controller for Unity
        """
        self.llm = llm_backend
        self.memory = memory_system
        self.tts = tts_engine
        self.animation = animation_controller
        self.observers: List[ConversationObserver] = []
        
        # Performance tracking
        self.metrics = {
            "llm_response_times": [],
            "tts_generation_times": [],
            "total_messages": 0,
            "total_errors": 0
        }
        
        logger.info("Conversation manager initialized")
    
    def send_message(
        self,
        user_id: str,
        message: str,
        generate_audio: bool = False,
        trigger_animation: bool = False
    ) -> ConversationResponse:
        """
        Process user message and generate response.
        
        Flow:
        1. Validate and sanitize input
        2. Retrieve relevant memories
        3. Build context with history and memories
        4. Get LLM response
        5. Store conversation in memory
        6. Generate TTS audio if requested
        7. Trigger animation if available
        8. Notify observers
        
        Args:
            user_id: User identifier
            message: User message
            generate_audio: Whether to generate TTS audio
            trigger_animation: Whether to trigger Unity animation
            
        Returns:
            ConversationResponse with text and optional audio/animation
        """
        start_time = time.time()
        
        try:
            # 1. Validate and sanitize input
            logger.debug(f"Processing message from user {user_id}")
            try:
                sanitized_message = InputValidator.validate_text(message)
            except ValidationError as e:
                logger.warning(f"Input validation failed: {e}")
                return ConversationResponse(
                    text="Sorry, your message contains invalid content.",
                    metadata={"error": str(e)}
                )
            
            # Notify observers
            for observer in self.observers:
                try:
                    observer.on_message_sent(user_id, sanitized_message)
                except Exception as e:
                    logger.error(f"Observer error: {e}")
            
            # 2. Retrieve relevant memories
            recent_history = self.memory.get_recent_history(user_id, limit=10)
            relevant_memories = self.memory.search_memories(user_id, sanitized_message, limit=3)
            user_context = self.memory.get_context(user_id)
            
            # 3. Build context
            history_tuples = [(msg.role, msg.content) for msg in recent_history]
            
            # 4. Get LLM response
            llm_start = time.time()
            try:
                llm_response = self.llm.send(sanitized_message, history_tuples)
                response_text = llm_response.text
            except Exception as e:
                logger.error(f"LLM error: {e}")
                self.metrics["total_errors"] += 1
                return ConversationResponse(
                    text="Sorry, I'm having trouble generating a response right now.",
                    metadata={"error": str(e)}
                )
            
            llm_time = time.time() - llm_start
            self.metrics["llm_response_times"].append(llm_time)
            logger.debug(f"LLM response time: {llm_time:.2f}s")
            
            # 5. Store conversation in memory
            self.memory.store_message(user_id, "user", sanitized_message)
            self.memory.store_message(user_id, "assistant", response_text)
            
            # 6. Generate TTS audio if requested
            audio_path = None
            if generate_audio and self.tts:
                tts_start = time.time()
                try:
                    # Generate unique filename
                    timestamp = int(time.time() * 1000)
                    audio_filename = f"response_{user_id}_{timestamp}.wav"
                    audio_path = Path("Audio") / audio_filename
                    
                    self.tts.synthesize(response_text, audio_path)
                    
                    tts_time = time.time() - tts_start
                    self.metrics["tts_generation_times"].append(tts_time)
                    logger.debug(f"TTS generation time: {tts_time:.2f}s")
                
                except Exception as e:
                    logger.error(f"TTS error: {e}")
                    # Continue without audio
            
            # 7. Trigger animation if available
            animation_id = None
            if trigger_animation and self.animation:
                try:
                    # Simple sentiment-based animation selection
                    animation_id = self._select_animation(response_text)
                    self.animation.trigger_animation(
                        animation_id,
                        audio_filename if audio_path else None
                    )
                except Exception as e:
                    logger.error(f"Animation error: {e}")
            
            # Build response
            response = ConversationResponse(
                text=response_text,
                audio_path=audio_path,
                animation_id=animation_id,
                metadata={
                    "llm_time": llm_time,
                    "total_time": time.time() - start_time,
                    "tokens_used": llm_response.tokens_used
                }
            )
            
            # 8. Notify observers
            for observer in self.observers:
                try:
                    observer.on_response_generated(user_id, response)
                except Exception as e:
                    logger.error(f"Observer error: {e}")
            
            self.metrics["total_messages"] += 1
            logger.info(f"Conversation completed in {time.time() - start_time:.2f}s")
            
            return response
        
        except Exception as e:
            logger.error(f"Unexpected error in conversation manager: {e}")
            self.metrics["total_errors"] += 1
            return ConversationResponse(
                text="Sorry, an unexpected error occurred.",
                metadata={"error": str(e)}
            )
    
    def _select_animation(self, text: str) -> int:
        """
        Select animation based on text sentiment.
        
        Args:
            text: Response text
            
        Returns:
            Animation ID
        """
        # Simple keyword-based animation selection
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["happy", "great", "wonderful", "excellent"]):
            return 22  # Happy
        elif any(word in text_lower for word in ["sad", "sorry", "unfortunately"]):
            return 1  # Sad
        elif any(word in text_lower for word in ["think", "consider", "maybe"]):
            return 27  # Thinking
        elif any(word in text_lower for word in ["excited", "amazing", "awesome"]):
            return 16  # Excited
        else:
            return 0  # Idle
    
    def reset_conversation(self, user_id: str) -> None:
        """
        Reset conversation state for user.
        
        Args:
            user_id: User identifier
        """
        # Note: We don't delete memory, just clear LLM state
        self.llm.reset()
        logger.info(f"Conversation reset for user {user_id}")
    
    def add_observer(self, observer: ConversationObserver) -> None:
        """
        Add conversation event observer.
        
        Args:
            observer: Observer to add
        """
        self.observers.append(observer)
        logger.debug(f"Added observer: {type(observer).__name__}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dictionary with metrics
        """
        avg_llm_time = (
            sum(self.metrics["llm_response_times"]) / len(self.metrics["llm_response_times"])
            if self.metrics["llm_response_times"] else 0
        )
        
        avg_tts_time = (
            sum(self.metrics["tts_generation_times"]) / len(self.metrics["tts_generation_times"])
            if self.metrics["tts_generation_times"] else 0
        )
        
        return {
            "total_messages": self.metrics["total_messages"],
            "total_errors": self.metrics["total_errors"],
            "avg_llm_response_time": avg_llm_time,
            "avg_tts_generation_time": avg_tts_time,
            "error_rate": (
                self.metrics["total_errors"] / self.metrics["total_messages"]
                if self.metrics["total_messages"] > 0 else 0
            )
        }
