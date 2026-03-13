# AI Companion

A production-ready, modular AI companion system with multiple interaction modes, persistent memory, and extensible integrations.

## Features

- 🎤 **Voice Interaction**: Speech-to-text and text-to-speech for natural conversations
- 🧠 **Persistent Memory**: Semantic search with conversation history and context
- 🔌 **Multiple LLM Backends**: Support for local (Kobold) and cloud (OpenAI) models
- 🎭 **Unity 3D Avatar**: Visual representation with synchronized animations
- 🤖 **Bot Integrations**: Discord and Telegram support
- 📚 **WaniKani Integration**: Japanese learning context awareness
- 🔒 **Security**: Input validation, rate limiting, and secret management
- 📊 **Performance Monitoring**: Track response times and metrics

## Quick Start

### 1. Installation

```bash
# Clone the repository
cd ai-companion

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure your API keys:

```bash
copy .env.example .env
```

Edit `.env` and add your API keys:
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI backend)
- `DISCORD_TOKEN`: Your Discord bot token (if using Discord)
- `TELEGRAM_TOKEN`: Your Telegram bot token (if using Telegram)
- `WANIKANI_API_KEY`: Your WaniKani API key (if using WaniKani)

### 3. Run the Application

```bash
# Run in voice mode (default)
python main.py

# Run in text mode (for testing without microphone)
python main.py --mode text

# Use custom configuration
python main.py --config my_config.yaml
```

## Usage

### Voice Mode

```bash
python main.py --mode voice
```

Speak naturally to interact with the AI companion. The system will:
1. Listen for your speech
2. Convert speech to text
3. Generate an AI response
4. Convert response to speech
5. Play the audio

### Text Mode

```bash
python main.py --mode text
```

Type messages to interact with the AI companion. Useful for testing without a microphone.

### Discord Bot Mode

```bash
python main.py --mode discord
```

Runs the AI companion as a Discord bot. Configure in `.env`:
```env
DISCORD_TOKEN=your-discord-bot-token
```

Then enable in `config/default_config.yaml`:
```yaml
integrations:
  discord:
    enabled: true
```

**Discord Commands:**
- `!join` - Join your voice channel
- `!leave` - Leave voice channel
- `!talk <message>` - Talk to the AI
- `!reset` - Reset conversation
- Mention the bot (@BotName) to chat

### Telegram Bot Mode

```bash
python main.py --mode telegram
```

Runs the AI companion as a Telegram bot. Configure in `.env`:
```env
TELEGRAM_TOKEN=your-telegram-bot-token
```

Then enable in `config/default_config.yaml`:
```yaml
integrations:
  telegram:
    enabled: true
```

**Telegram Commands:**
- `/start` - Start the bot
- `/help` - Show help
- `/reset` - Reset conversation
- `/status` - Show bot status
- Just send any message to chat!

### Unity Avatar Mode

Unity mode runs alongside other modes. Enable in `config/default_config.yaml`:
```yaml
integrations:
  unity:
    enabled: true
    address: 127.0.0.1
    port: 5005
    audio_dir: Audio/
```

Then run with voice or text mode:
```bash
python main.py --mode voice  # With Unity avatar
```

The Unity client should listen on UDP port 5005 for animation triggers.

### WaniKani Integration

For Japanese learning context, enable WaniKani:

1. Get API key from https://www.wanikani.com/settings/personal_access_tokens
2. Add to `.env`:
   ```env
   WANIKANI_API_KEY=your-api-key
   ```
3. Enable in config:
   ```yaml
   integrations:
     wanikani:
       enabled: true
   ```

The AI will know your learned vocabulary and kanji!

## Configuration

The application uses a YAML configuration file (`config/default_config.yaml`) with the following sections:

### App Configuration

```yaml
app:
  mode: voice  # voice, text, discord, telegram, unity
  log_level: INFO
  log_file: logs/companion.log
  environment: development
```

### LLM Backend

```yaml
llm:
  backend: kobold  # kobold or openai
  kobold_url: http://localhost:5001/api/v1/generate
  temperature: 0.7
  max_tokens: 300
```

### TTS Engine

```yaml
tts:
  engine: piper  # piper, pyttsx3, or gpt_sovits
  piper_model_path: en_US-hfc_female-medium.onnx
  output_dir: Audio/
```

### Memory System

```yaml
memory:
  storage_path: data/memory.db
  max_history: 20
  embedding_model: sentence-transformers/all-MiniLM-L6-v2
  similarity_threshold: 0.7
```

See `config/default_config.yaml` for all available options.

## Architecture

```
ai-companion/
├── main.py                 # Unified entry point
├── config/                 # Configuration management
│   ├── config_manager.py
│   ├── settings.py
│   └── default_config.yaml
├── core/                   # Core components
│   ├── conversation_manager.py
│   └── memory_system.py
├── services/               # Service layer
│   ├── llm/               # LLM backends
│   ├── tts/               # TTS engines
│   ├── stt/               # Speech recognition
│   ├── audio/             # Audio processing
│   └── animation/         # Animation control
├── integrations/          # Bot integrations
│   ├── discord/
│   ├── telegram/
│   ├── wanikani/
│   └── unity/
└── utils/                 # Utilities
    ├── validators.py
    ├── rate_limiter.py
    └── logging_config.py
```

## LLM Backends

### Kobold (Local)

1. Download KoboldCpp from [releases](https://github.com/LostRuins/koboldcpp/releases)
2. Download a GGUF model (e.g., from Hugging Face)
3. Start KoboldCpp:
   ```bash
   koboldcpp.exe --model your-model.gguf --port 5001
   ```
4. Configure in `config/default_config.yaml`:
   ```yaml
   llm:
     backend: kobold
     kobold_url: http://localhost:5001/api/v1/generate
   ```

### OpenAI (Cloud)

1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add to `.env`:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```
3. Configure in `config/default_config.yaml`:
   ```yaml
   llm:
     backend: openai
   ```

## TTS Engines

### Piper (Recommended)

1. Download a Piper ONNX model from [Piper releases](https://github.com/rhasspy/piper/releases)
2. Place the `.onnx` file in your project directory
3. Configure in `config/default_config.yaml`:
   ```yaml
   tts:
     engine: piper
     piper_model_path: en_US-hfc_female-medium.onnx
   ```

### pyttsx3 (System TTS)

Uses your system's built-in TTS voices. No additional setup required.

```yaml
tts:
  engine: pyttsx3
  voice_index: 1  # 0 for male, 1 for female
  rate: 180
```

## Memory System

The AI companion uses a semantic memory system that:
- Stores all conversations in a SQLite database
- Generates embeddings for semantic search
- Retrieves relevant context based on similarity
- Supports user-specific preferences and facts

Memory is stored in `data/memory.db` by default.

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint code
pylint **/*.py

# Type checking
mypy .
```

## Troubleshooting

### "No module named 'piper'"

Install Piper TTS:
```bash
pip install piper-tts
```

### "Could not find ffmpeg"

Install ffmpeg:
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Linux: `sudo apt-get install ffmpeg`
- Mac: `brew install ffmpeg`

### "Speech recognition not working"

1. Check microphone permissions
2. Ensure PyAudio is installed: `pip install pyaudio`
3. Test microphone with: `python -m speech_recognition`

### "Kobold connection error"

1. Ensure KoboldCpp is running
2. Check the URL in configuration matches KoboldCpp's address
3. Verify the model is loaded in KoboldCpp

## License

[Your License Here]

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## Support

For issues and questions, please open an issue on GitHub.
