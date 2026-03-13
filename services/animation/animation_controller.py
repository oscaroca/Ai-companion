"""
Animation controller for Unity 3D avatar.
Sends animation triggers and audio paths via UDP.
"""

import socket
from pathlib import Path
from typing import Optional, Dict

from config.settings import UnityConfig
from utils.logging_config import get_logger


logger = get_logger(__name__)


class AnimationController:
    """Controls Unity avatar animations via UDP."""
    
    # Animation mapping
    ANIMATIONS = {
        0: "idle",
        1: "idle_sad",
        4: "acknowledging",
        5: "angry_gesture",
        6: "annoyed_head_shake",
        10: "angry",
        12: "bashful",
        13: "blow_a_kiss",
        14: "bored",
        16: "excited",
        22: "happy",
        24: "rejected",
        27: "thinking",
        29: "threatening",
        31: "yawn",
        34: "head_nod_yes",
        40: "relieved_sigh",
    }
    
    def __init__(self, config: UnityConfig):
        """
        Initialize animation controller.
        
        Args:
            config: Unity configuration
        """
        self.config = config
        self.address = (config.address, config.port)
        self.audio_dir = Path(config.audio_dir)
        
        # Create UDP socket
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            logger.info(f"Animation controller initialized (Unity: {self.address})")
        except Exception as e:
            logger.error(f"Failed to create UDP socket: {e}")
            self.sock = None
    
    def trigger_animation(
        self,
        animation_id: int,
        audio_filename: Optional[str] = None
    ) -> bool:
        """
        Send animation trigger to Unity via UDP.
        
        Args:
            animation_id: Animation ID to trigger
            audio_filename: Optional audio filename to play
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.sock:
            logger.warning("UDP socket not available, cannot send animation")
            return False
        
        try:
            # Build message: "animation_id|audio_filename"
            if audio_filename:
                message = f"{animation_id}|{audio_filename}"
            else:
                message = f"{animation_id}|"
            
            # Send UDP message
            self.sock.sendto(message.encode('utf-8'), self.address)
            
            animation_name = self.ANIMATIONS.get(animation_id, f"unknown_{animation_id}")
            logger.debug(f"Sent animation trigger: {animation_name} (ID: {animation_id})")
            
            if audio_filename:
                logger.debug(f"Audio file: {audio_filename}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send animation trigger: {e}")
            return False
    
    def get_animation_for_sentiment(self, text: str) -> int:
        """
        Map text sentiment to animation ID.
        
        Args:
            text: Text to analyze
            
        Returns:
            Animation ID
        """
        text_lower = text.lower()
        
        # Positive emotions
        if any(word in text_lower for word in ["happy", "great", "wonderful", "excellent", "amazing"]):
            return 22  # Happy
        
        # Excitement
        if any(word in text_lower for word in ["excited", "awesome", "fantastic"]):
            return 16  # Excited
        
        # Sadness
        if any(word in text_lower for word in ["sad", "sorry", "unfortunately", "disappointed"]):
            return 1  # Sad
        
        # Thinking
        if any(word in text_lower for word in ["think", "consider", "maybe", "perhaps", "hmm"]):
            return 27  # Thinking
        
        # Agreement
        if any(word in text_lower for word in ["yes", "agree", "correct", "exactly", "right"]):
            return 34  # Head nod yes
        
        # Anger/frustration
        if any(word in text_lower for word in ["angry", "frustrated", "annoyed"]):
            return 10  # Angry
        
        # Boredom
        if any(word in text_lower for word in ["bored", "boring", "tired"]):
            return 14  # Bored
        
        # Default to idle
        return 0  # Idle
    
    def get_available_animations(self) -> Dict[int, str]:
        """
        Get dictionary of available animations.
        
        Returns:
            Dictionary mapping animation IDs to names
        """
        return self.ANIMATIONS.copy()
    
    def close(self) -> None:
        """Close UDP socket."""
        if self.sock:
            self.sock.close()
            logger.info("Animation controller closed")
