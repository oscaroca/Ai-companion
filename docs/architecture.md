# Architecture Documentation

This document describes the architecture and design of the AI Companion system.

## System Overview

The AI Companion is a modular, production-ready conversational AI system with multiple interaction modes and extensible integrations.

```
┌─────────────────────────────────────────────────────────────┐
│                      Entry Point (main.py)                   │
│                  Command-line Interface & Modes              │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │  Voice  │    │ Discord │    │Telegram │
    │  Mode   │    │   Bot   │    │   Bot   │
    └────┬────┘    └────┬────┘    └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
         ┌───────────────▼───────────────┐
         │   Conversation Manager         │
         │   (Orchestration Layer)        │
         └───────────────┬───────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │   LLM   │    │ Memory  │    │   TTS   │
    │ Backend │    │ System  │    │ Engine  │
    └─────────┘    └─────────┘    └─────────┘
```

## Architecture Principles

### 1. Modularity
- Each component has a single responsibility
- Components communicate through well-defined interfaces
- Easy to swap implementations (e.g., different TTS engines)

### 2. Extensibility
- Plugin system for integrations
- Abstract base classes for services
- Observer pattern for event handling

### 3. Security
- Input validation at entry points
- Rate limiting for API calls
- Secret management via environment variables
- Sanitization of user inputs

### 4. Performance
- Caching for external API calls
- Asynchronous operations where possible
- Connection pooling and retry logic
- Performance metrics tracking

## Directory Structure

```
ai-companion/
├── main.py                     # Entry point and mode orchestration
├── config/                     # Configuration management
│   ├── config_manager.py       # Configuration loader and validator
│   ├── settings.py             # Configuration dataclasses
│   └── default_config.yaml     # Default configuration
├── core/                       # Core business logic
│   ├── conversation_manager.py # Conversation orchestration
│   └── memory_system.py        # Persistent memory with semantic search
├── services/                   # Service layer (external integrations)
│   ├── llm/                    # LLM backends
│   │   ├── base.py             # Abstract LLM interface
│   │   ├── kobold_backend.py   # Local GGUF models
│   │   └── openai_backend.py   # OpenAI API
│   ├── tts/                    # Text-to-speech engines
│   │   ├── base.py             # Abstract TTS interface
│   │   ├── piper_engine.py     # Piper neural TTS
│   │   └── pyttsx3_engine.py   # System TTS
│   ├── stt/                    # Speech-to-text
│   │   └── speech_recognizer.py
│   ├── audio/                  # Audio processing
│   │   └── audio_processor.py  # Normalization and validation
│   └── animation/              # Unity integration
│       └── animation_controller.py
├── integrations/               # Bot and service integrations
│   ├── discord/
│   │   └── discord_bot.py
│   ├── telegram/
│   │   └── telegram_bot.py
│   ├── wanikani/
│   │   └── wanikani_client.py
│   └── unity/                  # (Future: Unity plugin)
├── utils/                      # Utility modules
│   ├── validators.py           # Input validation and sanitization
│   ├── rate_limiter.py         # Rate limiting
│   └── logging_config.py       # Logging setup
├── tests/                      # Test suite
├── docs/                       # Documentation
├── data/                       # Runtime data (databases, caches)
├── Audio/                      # Generated audio files
└── prompts/                    # System prompts
```

## Core Components

### 1. Entry Point (main.py)

**Responsibilities:**
- Parse command-line arguments
- Load configuration
- Initialize components
- Route to appropriate execution mode
- Handle graceful shutdown

**Key Classes:**
- `CompanionApp`: Main application class
- `parse_arguments()`: CLI argument parser

**Flow:**
```python
1. Parse CLI arguments
2. Load configuration from YAML and .env
3. Setup logging
4. Initialize core components
5. Run selected mode (voice, discord, telegram, etc.)
6. Handle shutdown signals
```

### 2. Configuration Management (config/)

**Responsibilities:**
- Load configuration from YAML files
- Load secrets from environment variables
- Validate configuration
- Provide type-safe configuration access

**Key Classes:**
- `ConfigurationManager`: Configuration loader and validator
- `AppConfig`, `LLMConfig`, `TTSConfig`, etc.: Type-safe configuration dataclasses

**Features:**
- Environment variable override
- Validation with descriptive errors
- Default values
- Environment-specific configuration

### 3. Conversation Manager (core/conversation_manager.py)

**Responsibilities:**
- Orchestrate conversation flow
- Coordinate LLM, memory, TTS, and animation
- Handle errors gracefully
- Track performance metrics
- Notify observers of events

**Key Classes:**
- `ConversationManager`: Main orchestrator
- `ConversationResponse`: Response dataclass
- `ConversationObserver`: Observer protocol

**Flow:**
```python
1. Validate and sanitize user input
2. Retrieve relevant memories from database
3. Build context with history and memories
4. Get LLM response
5. Store conversation in memory
6. Generate TTS audio (if requested)
7. Trigger Unity animation (if enabled)
8. Notify observers
9. Return response
```

### 4. Memory System (core/memory_system.py)

**Responsibilities:**
- Store conversation history in SQLite
- Generate embeddings for semantic search
- Retrieve relevant memories by similarity
- Store user context and preferences
- Summarize old conversations
- Support data deletion (privacy compliance)

**Key Classes:**
- `MemorySystem`: Memory manager
- `Message`: Message dataclass

**Database Schema:**
```sql
users (
  user_id TEXT PRIMARY KEY,
  created_at TIMESTAMP
)

messages (
  id INTEGER PRIMARY KEY,
  user_id TEXT,
  role TEXT,  -- 'user' or 'assistant'
  content TEXT,
  embedding BLOB,  -- Serialized numpy array
  timestamp TIMESTAMP
)

user_context (
  user_id TEXT PRIMARY KEY,
  context_data TEXT  -- JSON
)

conversation_summaries (
  id INTEGER PRIMARY KEY,
  user_id TEXT,
  summary TEXT,
  message_count INTEGER,
  created_at TIMESTAMP
)
```

**Semantic Search:**
1. Generate embedding for query using sentence-transformers
2. Compute cosine similarity with stored embeddings
3. Return top-k most similar messages above threshold

### 5. LLM Backend (services/llm/)

**Responsibilities:**
- Abstract LLM interface
- Handle API calls with retry logic
- Manage conversation context
- Track token usage

**Key Classes:**
- `LLMBackend`: Abstract base class
- `KoboldBackend`: Local GGUF models via KoboldCpp
- `OpenAIBackend`: OpenAI API (GPT-3.5, GPT-4)

**Interface:**
```python
class LLMBackend(ABC):
    @abstractmethod
    def send(self, message: str, history: List[Tuple[str, str]]) -> LLMResponse:
        """Send message and get response."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset conversation state."""
        pass
```

**Features:**
- Exponential backoff retry
- Connection pooling
- Error handling
- System prompt support

### 6. TTS Engine (services/tts/)

**Responsibilities:**
- Abstract TTS interface
- Synthesize speech from text
- Normalize audio for Unity/Discord
- Handle voice selection

**Key Classes:**
- `TTSEngine`: Abstract base class
- `PiperEngine`: Neural TTS with ONNX models
- `Pyttsx3Engine`: System TTS

**Interface:**
```python
class TTSEngine(ABC):
    @abstractmethod
    def synthesize(self, text: str, output_path: Path) -> None:
        """Synthesize speech and save to file."""
        pass
    
    @abstractmethod
    def get_voices(self) -> List[str]:
        """Get available voices."""
        pass
```

**Audio Processing:**
- Normalize to 44.1kHz, mono, 16-bit PCM WAV
- Validate audio format
- Handle encoding errors

### 7. Speech Recognition (services/stt/)

**Responsibilities:**
- Capture audio from microphone
- Convert speech to text
- Adjust for ambient noise
- Support multiple languages

**Key Classes:**
- `SpeechRecognizer`: Speech-to-text manager

**Features:**
- Google Speech Recognition API
- Ambient noise adjustment
- Configurable language
- Timeout handling

### 8. Animation Controller (services/animation/)

**Responsibilities:**
- Send animation triggers to Unity via UDP
- Map sentiment to animations
- Send audio file paths
- Handle network errors

**Key Classes:**
- `AnimationController`: UDP client for Unity

**Protocol:**
```
UDP Message Format: {animation_id}|{audio_filename}
Example: 22|response_voice_user_1234567890.wav
```

**Animation Mapping:**
- Happy: 22
- Sad: 1
- Thinking: 27
- Excited: 16
- Idle: 0

### 9. Integrations (integrations/)

**Responsibilities:**
- Implement bot interfaces
- Handle platform-specific features
- Manage per-user context
- Integrate with ConversationManager

**Discord Bot:**
- Commands: `!join`, `!leave`, `!talk`, `!reset`
- Voice channel support
- Audio playback with ffmpeg
- Mention detection

**Telegram Bot:**
- Commands: `/start`, `/help`, `/reset`, `/status`
- Per-user conversation context
- Async message handling
- Error recovery

**WaniKani Client:**
- Fetch learned vocabulary and kanji
- Cache with TTL
- Format for LLM context
- Rate limiting

### 10. Utilities (utils/)

**Input Validation:**
- Text sanitization (max length, injection prevention)
- Path validation (prevent traversal attacks)
- URL validation
- Network address validation

**Rate Limiting:**
- Token bucket algorithm
- Per-user rate limits
- Configurable thresholds
- Violation logging

**Logging:**
- Structured logging with rotation
- Secret redaction
- Severity levels
- Performance tracking

## Data Flow

### Voice Mode Flow

```
1. User speaks
   ↓
2. SpeechRecognizer captures audio
   ↓
3. Google Speech API converts to text
   ↓
4. ConversationManager receives message
   ↓
5. InputValidator sanitizes input
   ↓
6. MemorySystem retrieves relevant history
   ↓
7. LLMBackend generates response
   ↓
8. MemorySystem stores conversation
   ↓
9. TTSEngine synthesizes speech
   ↓
10. AudioProcessor normalizes audio
   ↓
11. AnimationController triggers Unity (if enabled)
   ↓
12. Audio plays to user
```

### Discord Bot Flow

```
1. User sends Discord message
   ↓
2. DiscordIntegration receives event
   ↓
3. ConversationManager processes message
   ↓
4. (Same as Voice Mode steps 5-10)
   ↓
11. DiscordIntegration sends text response
   ↓
12. If in voice channel, plays audio
```

### Telegram Bot Flow

```
1. User sends Telegram message
   ↓
2. TelegramIntegration receives update
   ↓
3. ConversationManager processes message
   ↓
4. (Same as Voice Mode steps 5-9)
   ↓
10. TelegramIntegration sends text response
```

## Design Patterns

### 1. Abstract Factory Pattern
- `LLMBackend`, `TTSEngine` abstract base classes
- Factory methods create concrete implementations
- Easy to add new backends/engines

### 2. Observer Pattern
- `ConversationObserver` protocol
- Integrations observe conversation events
- Decouples conversation logic from integrations

### 3. Strategy Pattern
- Different execution modes (voice, discord, telegram)
- Swappable at runtime via configuration
- Same core logic, different interfaces

### 4. Singleton Pattern
- `ConfigurationManager` (single instance)
- `MemorySystem` (single database connection)
- Ensures consistency

### 5. Repository Pattern
- `MemorySystem` abstracts database access
- Clean separation of data and business logic
- Easy to swap storage backends

## Security Architecture

### Input Validation Layer

```
User Input
   ↓
InputValidator.validate_text()
   ↓
- Max length check
- Injection prevention
- Sanitization
   ↓
Validated Input → ConversationManager
```

### Secret Management

```
.env file (not in git)
   ↓
Environment Variables
   ↓
ConfigurationManager
   ↓
- Validation
- Redaction in logs
   ↓
Services (LLM, Bots, etc.)
```

### Rate Limiting

```
User Request
   ↓
RateLimiter.check_rate_limit(user_id)
   ↓
- Token bucket algorithm
- Per-user tracking
- Configurable limits
   ↓
Allow/Deny → Service
```

## Performance Considerations

### Caching Strategy

**WaniKani Cache:**
- TTL: 1 hour (configurable)
- Storage: JSON file
- Reduces API calls

**Memory Embeddings:**
- Pre-computed and stored in database
- Avoids re-computation on every query
- Fast cosine similarity search

### Async Operations

**Discord/Telegram Bots:**
- Async message handling
- Non-blocking I/O
- Concurrent user support

**LLM Calls:**
- Retry with exponential backoff
- Timeout handling
- Connection pooling

### Resource Management

**Database Connections:**
- Single connection per MemorySystem instance
- Proper cleanup on shutdown
- Transaction management

**Audio Files:**
- Unique filenames prevent conflicts
- Cleanup old files (manual or scheduled)
- Normalized format reduces processing

## Error Handling

### Graceful Degradation

```
LLM Error → Return fallback message
TTS Error → Continue without audio
Animation Error → Continue without animation
Memory Error → Use empty context
```

### Retry Logic

```
API Call
   ↓
Failure?
   ↓
Retry with exponential backoff
   ↓
Max retries reached?
   ↓
Log error and return fallback
```

### Logging Strategy

```
DEBUG: Detailed flow information
INFO: Important events (startup, shutdown, user actions)
WARNING: Recoverable errors (API failures, retries)
ERROR: Unrecoverable errors (configuration issues, crashes)
CRITICAL: System-level failures
```

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Fast execution

### Property-Based Tests
- Test universal properties (e.g., round-trip serialization)
- Generate random inputs
- Catch edge cases

### Integration Tests
- Test component interactions
- Use test databases and mock APIs
- Verify end-to-end flows

## Deployment Considerations

### Development Environment
- Local LLM (Kobold)
- Debug logging
- No rate limiting
- Test tokens

### Production Environment
- Cloud LLM (OpenAI) or optimized local
- Info logging
- Rate limiting enabled
- Production tokens
- Monitoring and alerts

### Scaling
- Multiple bot instances (separate processes)
- Shared database (SQLite → PostgreSQL)
- Load balancing for API calls
- Caching layer (Redis)

## Future Enhancements

### Planned Features
1. Plugin system for integrations
2. Web UI for configuration
3. Multi-language support
4. Voice cloning with GPT-SoVITS
5. Advanced memory summarization
6. Metrics dashboard
7. A/B testing framework

### Architecture Evolution
- Microservices architecture for scaling
- Message queue for async processing
- Distributed caching
- API gateway for integrations

## See Also

- [Configuration Guide](configuration.md) - Configuration options
- [Setup Guide](setup.md) - Installation and setup
- [Integration Guide](integrations.md) - Bot integrations
- [Troubleshooting](troubleshooting.md) - Common issues
