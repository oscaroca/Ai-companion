"""
Logging configuration with rotation and structured logging.
Supports secret redaction to prevent sensitive information leakage.
"""

import logging
import logging.handlers
import re
from pathlib import Path
from typing import Optional, Set


# Patterns for detecting secrets in log messages
SECRET_PATTERNS = [
    (re.compile(r'(api[_-]?key|token|password|secret)["\s:=]+([^\s"\']+)', re.IGNORECASE), r'\1=***REDACTED***'),
    (re.compile(r'Bearer\s+([^\s]+)', re.IGNORECASE), r'Bearer ***REDACTED***'),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), r'sk-***REDACTED***'),  # OpenAI keys
]


class SecretRedactingFormatter(logging.Formatter):
    """Formatter that redacts sensitive information from log messages."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record and redact secrets."""
        # Format the message first
        message = super().format(record)
        
        # Apply all secret patterns
        for pattern, replacement in SECRET_PATTERNS:
            message = pattern.sub(replacement, message)
        
        return message


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up logging with rotation and secret redaction.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, logs to console only)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("companion")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatter with secret redaction
    formatter = SecretRedactingFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"companion.{name}")
