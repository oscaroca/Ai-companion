# Configuration Guide

This guide explains all configuration options for the AI Companion system.

## Configuration Files

The system uses two configuration files:

1. **`.env`** - Environment variables and secrets (API keys, tokens)
2. **`config/default_config.yaml`** - Application settings and parameters

## Environment Variables (.env)

Copy `.env.example` to `.env` and configure:

### LLM Backend

```env
# OpenAI API Key (if using OpenAI backend)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Kobold API URL (if using Kobold backend)
KOBOLD_URL=http://localhost:5001/api/v1/generate
```

**How to get:**
- OpenAI: https://platform.openai.com/api-keys
- Kobold: Run KoboldCpp locally (see Setup Guide)

### Bot Integration Tokens

```env
# Discord Bot Token
DISCORD_TOKEN=your-discord-bot-token-here

# Telegram Bot Token
TELEGRAM_TOKEN=your-telegram-bot-token-here
```

**How to get:**
- Discord: https://discord.com/developers/applications
- Telegram: Message @BotFather on Telegram

### External Service API Keys

```env
# WaniKani API Key
WANIKANI_API_KEY=your-wanikani-api-key-here
```

**How to get:**
- WaniKani: https://www.wanikani.com/settings/personal_access_tokens

### Application Settings

```env
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log file path
LOG_FILE=logs/companion.log

# Default execution mode (voice, text, discord, telegram, unity)
DEFAULT_MODE=voice
```

## YAML Configuration (config/default_config.yaml)

### App Configuration

```yaml
app:
  mode: voice  # voice, text, discord, telegram, unity
  log_level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_file: logs/companion.log
  environment: development  # development, production
```

**Options:**
- `mode`: Default execution mode (can be overridden with `--mode` flag)
- `log_level`: Logging verbosity
- `log_file`: Path to log file
- `environment`: Environment name (affects logging format)

### LLM Backend Configuration

```yaml
llm:
  backend: kobold  # kobold or openai
  kobold_url: http://localhost:5001/api/v1/generate
  temperature: 0.7  # 0.0 to 1.0 (higher = more creative)
  top_p: 0.9  # 0.0 to 1.0 (nucleus sampling)
  max_tokens: 300  # Maximum response length
  system_prompt_file: prompts/default.txt
```

**Backend Options:**
- `kobold`: Local GGUF models via KoboldCpp
- `openai`: OpenAI API (GPT-3.5, GPT-4)

**Generation Parameters:**
- `temperature`: Controls randomness (0.0 = deterministic, 1.0 = very random)
- `top_p`: Nucleus sampling threshold
- `max_tokens`: Maximum tokens in response
- `system_prompt_file`: Path to system prompt text file

### TTS Engine Configuration

```yaml
tts:
  engine: piper  # piper, pyttsx3, or gpt_sovits
  piper_model_path: en_US-hfc_female-medium.onnx
  voice_index: 1  # For pyttsx3: 0=male, 1=female
  rate: 180  # Speech rate (words per minute)
  volume: 1.0  # Volume (0.0 to 1.0)
  output_dir: Audio/
```

**Engine Options:**
- `piper`: High-quality neural TTS (requires ONNX model)
- `pyttsx3`: System TTS (no additional setup)
- `gpt_sovits`: Advanced TTS (requires GPT-SoVITS installation)

**Piper Configuration:**
- `piper_model_path`: Path to `.onnx` model file
- Download models from: https://github.com/rhasspy/piper/releases

**pyttsx3 Configuration:**
- `voice_index`: Voice selection (0 for male, 1 for female)
- `rate`: Speech speed (default 180 wpm)
- `volume`: Audio volume (0.0 to 1.0)

### Speech Recognition Configuration

```yaml
stt:
  language: es-ES  # Language code (en-US, es-ES, ja-JP, etc.)
  energy_threshold: 4000  # Microphone sensitivity
  pause_threshold: 0.8  # Silence duration to end speech (seconds)
```

**Language Codes:**
- `en-US`: English (United States)
- `es-ES`: Spanish (Spain)
- `ja-JP`: Japanese
- `fr-FR`: French
- `de-DE`: German

**Sensitivity:**
- `energy_threshold`: Higher = less sensitive (adjust for noisy environments)
- `pause_threshold`: How long to wait for silence before processing

### Memory System Configuration

```yaml
memory:
  storage_path: data/memory.db
  max_history: 20
  embedding_model: sentence-transformers/all-MiniLM-L6-v2
  similarity_threshold: 0.7
  enable_summarization: true
  summary_threshold: 100
```

**Options:**
- `storage_path`: SQLite database file path
- `max_history`: Number of recent messages to include in context
- `embedding_model`: Sentence transformer model for semantic search
- `similarity_threshold`: Minimum similarity for memory retrieval (0.0 to 1.0)
- `enable_summarization`: Auto-summarize old conversations
- `summary_threshold`: Summarize after this many messages

**Embedding Models:**
- `all-MiniLM-L6-v2`: Fast, good quality (default)
- `all-mpnet-base-v2`: Slower, better quality
- `paraphrase-multilingual-MiniLM-L12-v2`: Multilingual support

### Discord Integration

```yaml
integrations:
  discord:
    enabled: false  # Set to true to enable
    command_prefix: "!"
    ffmpeg_path: ffmpeg  # Or full path: C:\ffmpeg\bin\ffmpeg.exe
```

**Setup:**
1. Set `enabled: true`
2. Add `DISCORD_TOKEN` to `.env`
3. Install ffmpeg for voice support
4. Run with `python main.py --mode discord`

**Commands:**
- Prefix: `!` (configurable)
- `!join`, `!leave`, `!talk`, `!reset`

### Telegram Integration

```yaml
integrations:
  telegram:
    enabled: false  # Set to true to enable
```

**Setup:**
1. Set `enabled: true`
2. Add `TELEGRAM_TOKEN` to `.env`
3. Run with `python main.py --mode telegram`

**Commands:**
- `/start`, `/help`, `/reset`, `/status`

### WaniKani Integration

```yaml
integrations:
  wanikani:
    enabled: false  # Set to true to enable
    cache_ttl: 3600  # Cache duration (seconds)
    cache_path: data/wanikani_cache.json
```

**Setup:**
1. Set `enabled: true`
2. Add `WANIKANI_API_KEY` to `.env`
3. Works with all modes automatically

**Caching:**
- `cache_ttl`: How long to cache learned items (default 1 hour)
- `cache_path`: Where to store cached data

### Unity Avatar Integration

```yaml
integrations:
  unity:
    enabled: false  # Set to true to enable
    address: 127.0.0.1
    port: 5005
    audio_dir: Audio/
```

**Setup:**
1. Set `enabled: true`
2. Configure Unity client to listen on UDP port 5005
3. Run with any mode (voice, text, etc.)

**UDP Protocol:**
- Format: `{animation_id}|{audio_filename}`
- Example: `22|response_voice_user_1234567890.wav`

### Rate Limiting

```yaml
rate_limits:
  openai_requests_per_minute: 20
  wanikani_requests_per_minute: 60
  user_messages_per_minute: 10
```

**Options:**
- `openai_requests_per_minute`: OpenAI API rate limit
- `wanikani_requests_per_minute`: WaniKani API rate limit
- `user_messages_per_minute`: Per-user message rate limit

## Environment-Specific Configuration

### Development

```yaml
app:
  environment: development
  log_level: DEBUG
```

- Verbose logging
- Detailed error messages
- No rate limiting

### Production

```yaml
app:
  environment: production
  log_level: INFO
```

- Concise logging
- User-friendly error messages
- Rate limiting enabled

## Configuration Validation

The system validates configuration on startup:

```bash
python main.py
```

If configuration is invalid, you'll see:
```
Configuration errors:
  - Missing required field: llm.backend
  - Invalid value for tts.engine: must be one of [piper, pyttsx3, gpt_sovits]
```

## Configuration Precedence

Configuration is loaded in this order (later overrides earlier):

1. Default values in code
2. `config/default_config.yaml`
3. Environment variables from `.env`
4. Command-line arguments

Example:
```bash
# Config says mode=voice, but command-line overrides it
python main.py --mode text
```

## Security Best Practices

### Secrets Management

- Never commit `.env` to version control
- Use different tokens for dev/prod
- Rotate tokens periodically
- Use environment variables in production

### File Permissions

```bash
# Linux/Mac
chmod 600 .env
chmod 600 config/default_config.yaml
```

### API Key Restrictions

- OpenAI: Set usage limits and alerts
- Discord: Restrict bot permissions to minimum required
- Telegram: Use bot privacy mode
- WaniKani: Read-only token

## Troubleshooting

### "Configuration error: Missing required field"

Check that all required fields are set in config or `.env`.

### "Invalid value for field"

Check that values match expected types and ranges.

### "Failed to load configuration file"

Ensure `config/default_config.yaml` exists and is valid YAML.

### Environment variables not loading

- Check `.env` file exists in project root
- Ensure no spaces around `=` in `.env`
- Restart application after changing `.env`

## Advanced Configuration

### Custom System Prompts

Create `prompts/custom.txt`:
```
You are a helpful AI assistant specialized in [your domain].
```

Then configure:
```yaml
llm:
  system_prompt_file: prompts/custom.txt
```

### Multiple Configurations

Create environment-specific configs:
```bash
config/
  default_config.yaml
  development.yaml
  production.yaml
```

Load with:
```bash
python main.py --config config/production.yaml
```

### Configuration Templates

For teams, create a template:
```yaml
# config/template.yaml
app:
  mode: ${MODE}
llm:
  backend: ${LLM_BACKEND}
```

Then set environment variables:
```bash
export MODE=voice
export LLM_BACKEND=openai
python main.py --config config/template.yaml
```

## See Also

- [Setup Guide](setup.md) - Installation and first-time setup
- [Integration Guide](integrations.md) - Bot and service integrations
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
