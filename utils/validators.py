"""
Input validation and sanitization utilities.
Protects against injection attacks and malformed data.
"""

import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class InputValidator:
    """Validates and sanitizes user inputs."""
    
    MAX_INPUT_LENGTH = 2000
    MAX_PATH_LENGTH = 260  # Windows MAX_PATH
    
    # Patterns for detecting injection attacks
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",  # Shell metacharacters
        r"(\.\./|\.\.\\)",  # Path traversal
    ]
    
    SCRIPT_INJECTION_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers like onclick=
    ]
    
    @staticmethod
    def validate_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Validate and sanitize text input.
        
        Args:
            text: Input text to validate
            max_length: Maximum allowed length (uses MAX_INPUT_LENGTH if None)
            
        Returns:
            Sanitized text
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(text, str):
            raise ValidationError(f"Input must be a string, got {type(text).__name__}")
        
        # Check length
        max_len = max_length or InputValidator.MAX_INPUT_LENGTH
        if len(text) > max_len:
            raise ValidationError(
                f"Input exceeds maximum length of {max_len} characters "
                f"(got {len(text)} characters)"
            )
        
        # Check for SQL injection patterns
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValidationError(
                    "Input contains potentially malicious SQL patterns"
                )
        
        # Check for script injection patterns
        for pattern in InputValidator.SCRIPT_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValidationError(
                    "Input contains potentially malicious script patterns"
                )
        
        # Basic sanitization: strip leading/trailing whitespace
        sanitized = text.strip()
        
        return sanitized
    
    @staticmethod
    def validate_path(path_str: str, must_exist: bool = False) -> Path:
        """
        Validate file path and prevent traversal attacks.
        
        Args:
            path_str: Path string to validate
            must_exist: If True, path must exist
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(path_str, str):
            raise ValidationError(f"Path must be a string, got {type(path_str).__name__}")
        
        # Check length
        if len(path_str) > InputValidator.MAX_PATH_LENGTH:
            raise ValidationError(
                f"Path exceeds maximum length of {InputValidator.MAX_PATH_LENGTH} characters"
            )
        
        # Check for path traversal attempts
        if ".." in path_str:
            raise ValidationError("Path contains path traversal sequence (..)")
        
        # Check for command injection in path
        for pattern in InputValidator.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, path_str):
                raise ValidationError(
                    "Path contains potentially malicious characters"
                )
        
        try:
            path = Path(path_str)
            
            # Resolve to absolute path to prevent traversal
            resolved_path = path.resolve()
            
            # Check if path exists (if required)
            if must_exist and not resolved_path.exists():
                raise ValidationError(f"Path does not exist: {path_str}")
            
            return resolved_path
        
        except (ValueError, OSError) as e:
            raise ValidationError(f"Invalid path: {e}")
    
    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate URL format.
        
        Args:
            url: URL string to validate
            
        Returns:
            Validated URL string
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(url, str):
            raise ValidationError(f"URL must be a string, got {type(url).__name__}")
        
        if len(url) > InputValidator.MAX_INPUT_LENGTH:
            raise ValidationError(
                f"URL exceeds maximum length of {InputValidator.MAX_INPUT_LENGTH} characters"
            )
        
        try:
            result = urlparse(url)
            
            # Check for valid scheme
            if result.scheme not in ['http', 'https', 'ws', 'wss']:
                raise ValidationError(
                    f"Invalid URL scheme: {result.scheme}. "
                    "Must be http, https, ws, or wss"
                )
            
            # Check for valid netloc (domain)
            if not result.netloc:
                raise ValidationError("URL must contain a valid domain")
            
            return url
        
        except Exception as e:
            raise ValidationError(f"Invalid URL: {e}")
    
    @staticmethod
    def validate_network_address(address: str) -> str:
        """
        Validate network address (IP or hostname).
        
        Args:
            address: Network address to validate
            
        Returns:
            Validated address
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(address, str):
            raise ValidationError(
                f"Address must be a string, got {type(address).__name__}"
            )
        
        if len(address) > 255:
            raise ValidationError("Address exceeds maximum length of 255 characters")
        
        # Check for IPv4 pattern
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ipv4_pattern, address):
            # Validate IPv4 octets
            octets = address.split('.')
            for octet in octets:
                if int(octet) > 255:
                    raise ValidationError(f"Invalid IPv4 address: {address}")
            return address
        
        # Check for hostname pattern
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if re.match(hostname_pattern, address):
            return address
        
        # Check for localhost
        if address.lower() in ['localhost', '::1']:
            return address
        
        raise ValidationError(f"Invalid network address: {address}")
    
    @staticmethod
    def validate_port(port: int) -> int:
        """
        Validate network port number.
        
        Args:
            port: Port number to validate
            
        Returns:
            Validated port number
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(port, int):
            raise ValidationError(f"Port must be an integer, got {type(port).__name__}")
        
        if port < 1 or port > 65535:
            raise ValidationError(
                f"Port must be between 1 and 65535, got {port}"
            )
        
        return port
    
    @staticmethod
    def sanitize_for_logging(text: str) -> str:
        """
        Sanitize text for safe logging (remove sensitive patterns).
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text safe for logging
        """
        # Redact API keys and tokens
        text = re.sub(
            r'(api[_-]?key|token|password|secret)["\s:=]+([^\s"\']+)',
            r'\1=***REDACTED***',
            text,
            flags=re.IGNORECASE
        )
        
        # Redact Bearer tokens
        text = re.sub(
            r'Bearer\s+([^\s]+)',
            r'Bearer ***REDACTED***',
            text,
            flags=re.IGNORECASE
        )
        
        # Redact OpenAI keys
        text = re.sub(r'sk-[a-zA-Z0-9]{20,}', 'sk-***REDACTED***', text)
        
        return text
