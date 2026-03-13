# Integration Guide

This guide explains how to set up and use each integration with the AI Companion.

## Discord Bot Integration

### Setup

1. **Create Discord Bot:**
   - Go to https://discord.com/developers/applications
   - Click "New Application"
   - Go to "Bot" section and click "Add Bot"
   - Enable "Message Content Intent" and "Server Members Intent"
   - Copy the bot token

2. **Configure Bot:**
   - Add token to `.env`:
     ```env
     DISCORD_TOKEN=your-bot-token-here
     ```
   
   - Enable in `config/default_config.yaml`:
     ```yaml
     integrations:
       discord:
         enabled: true
         command_prefix: "!"
         ffmpeg_path: ffmpeg  # Or full path on Windows
     ```

3. **Invite Bot to Server:**
   - Go to OAuth2 → URL Generator
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Connect`, `Speak`
   - Copy and open the generated URL
   - Select your server and authorize

4. **Run Bot:**
   ```bash
   python main.py --mode discord
   ```

### Usage

**Text Commands:**
- `!join` - Bot joins your voice channel
- `!leave` - Bot leaves voice channel
- `!talk <message>` - Send a message to the AI
- `!reset` - Reset conversation history

**Mention Bot:**
- `@BotName hello` - Chat by mentioning the bot

**Voice Features:**
- Bot will play TTS responses in voice channel
- Audio is automatically normalized for Discord

### Troubleshooting

**Bot doesn't respond:**
- Check "Message Content Intent" is enabled
- Verify bot has "Send Messages" permission
- Check logs for errors

**Voice doesn't work:**
- Ensure ffmpeg is installed and in PATH
- Check bot has "Connect" and "Speak" permissions
- Verify you're in a voice channel when using `!join`

## Telegram Bot Integration

### Setup

1. **Create Telegram Bot:**
   - Open Telegram and search for @BotFather
   - Send `/newbot` command
   - Follow prompts to create bot
   - Copy the bot token

2. **Configure Bot:**
   - Add token to `.env`:
     ```env
     TELEGRAM_TOKEN=your-bot-token-here
     ```
   
   - Enable in `config/default_config.yaml`:
     ```yaml
     integrations:
       telegram:
         enabled: true
     ```

3. **Run Bot:**
   ```bash
   python main.py --mode telegram
   ```

4. **Start Chatting:**
   - Find your bot on Telegram
   - Send `/start` to begin

### Usage

**Commands:**
- `/start` - Initialize the bot
- `/help` - Show help message
- `/reset` - Reset your conversation
- `/status` - Show bot statistics

**Chatting:**
- Just send any message to chat with the AI
- Each user has separate conversation context
- Conversations are persistent across sessions

### Features

- **Per-user Context:** Each user has their own conversation history
- **Persistent Memory:** Conversations are saved to database
- **Fast Responses:** Optimized for text-only interaction
- **Status Tracking:** View response times and error rates

## WaniKani Integration

### Setup

1. **Get API Key:**
   - Go to https://www.wanikani.com/settings/personal_access_tokens
   - Click "Generate a new token"
   - Give it a description (e.g., "AI Companion")
   - Copy the token

2. **Configure:**
   - Add to `.env`:
     ```env
     WANIKANI_API_KEY=your-api-key-here
     ```
   
   - Enable in `config/default_config.yaml`:
     ```yaml
     integrations:
       wanikani:
         enabled: true
         cache_ttl: 3600  # Cache for 1 hour
     ```

3. **Use with Any Mode:**
   ```bash
   python main.py --mode voice  # Or text, discord, telegram
   ```

### Features

- **Learned Items:** AI knows your learned vocabulary and kanji
- **Context-Aware:** Responses use appropriate Japanese level
- **Caching:** Minimizes API calls (refreshes hourly)
- **Automatic Integration:** Works with all conversation modes

### How It Works

1. On startup, fetches your learned items from WaniKani
2. Formats them into the system prompt
3. AI uses this context in all responses
4. Cache is refreshed after TTL expires

## Unity Avatar Integration

### Setup

1. **Unity Project Setup:**
   - Create or open Unity project with VRM avatar
   - Add UDP listener script (see Unity integration guide)
   - Configure to listen on port 5005

2. **Configure AI Companion:**
   - Enable in `config/default_config.yaml`:
     ```yaml
     integrations:
       unity:
         enabled: true
         address: 127.0.0.1
         port: 5005
         audio_dir: Audio/  # Must be accessible by Unity
     ```

3. **Run with Unity:**
   ```bash
   # Start Unity project first
   # Then start AI Companion
   python main.py --mode voice
   ```

### UDP Message Format

Messages sent to Unity:
```
{animation_id}|{audio_filename}
```

Example:
```
22|response_voice_user_1234567890.wav
```

### Animation IDs

Common animations:
- `0` - Idle
- `1` - Sad
- `10` - Angry
- `16` - Excited
- `22` - Happy
- `27` - Thinking
- `34` - Head nod yes

See `services/animation/animation_controller.py` for full list.

### Audio Synchronization

1. AI generates response
2. TTS creates audio file in `Audio/` directory
3. Audio is normalized to Unity format (44.1kHz, mono, 16-bit PCM)
4. UDP message sent with animation ID and filename
5. Unity plays audio and triggers animation

## Running Multiple Integrations

Currently, integrations run in separate modes. To run multiple:

**Option 1: Multiple Processes**
```bash
# Terminal 1
python main.py --mode discord

# Terminal 2
python main.py --mode telegram
```

**Option 2: Custom Script**
Create a script to run multiple modes with asyncio (advanced).

## Integration Best Practices

### Security

- Never commit `.env` file
- Rotate tokens periodically
- Use separate tokens for dev/prod
- Monitor bot usage for abuse

### Performance

- Enable caching for WaniKani
- Use appropriate rate limits
- Monitor memory usage with multiple bots
- Consider using separate databases per bot

### Monitoring

- Check logs regularly: `logs/companion.log`
- Use `/status` command in Telegram
- Monitor Discord bot status
- Track API usage for rate limits

## Troubleshooting

### General Issues

**"Integration not enabled":**
- Check `enabled: true` in config
- Verify token in `.env`
- Restart application

**Import errors:**
```bash
# Discord
pip install discord.py

# Telegram
pip install python-telegram-bot

# WaniKani (uses requests, should be installed)
pip install requests
```

### Discord-Specific

**Bot offline:**
- Check token is correct
- Verify bot is invited to server
- Check internet connection

**No voice:**
- Install ffmpeg
- Check voice permissions
- Verify audio files are generated

### Telegram-Specific

**Bot not responding:**
- Check token is correct
- Verify bot is not blocked
- Check logs for errors

**Slow responses:**
- Check LLM backend performance
- Monitor network latency
- Consider using faster model

### WaniKani-Specific

**No learned items:**
- Verify API key is correct
- Check you have learned items on WaniKani
- Try force refresh (delete cache file)

**Cache not updating:**
- Check `cache_ttl` setting
- Delete cache file to force refresh
- Verify API key permissions

## Advanced Configuration

### Custom System Prompts with WaniKani

Edit `prompts/default.txt` to customize how the AI uses WaniKani data:

```
You are a Japanese tutor. Use the learned vocabulary below to provide appropriate practice.

{WaniKani context will be appended here automatically}
```

### Discord Voice Quality

Adjust TTS settings for better Discord voice:

```yaml
tts:
  engine: piper  # Better quality than pyttsx3
  piper_model_path: en_US-hfc_female-medium.onnx
  rate: 180
  volume: 1.0
```

### Telegram Response Speed

For faster Telegram responses:

```yaml
llm:
  backend: openai  # Faster than local Kobold
  max_tokens: 150  # Shorter responses
```

### Unity Animation Mapping

Customize animation selection in `services/animation/animation_controller.py`:

```python
def get_animation_for_sentiment(self, text: str) -> int:
    # Add your custom mappings
    if "custom_keyword" in text.lower():
        return 42  # Your custom animation
    # ...
```

## Getting Help

- Check logs: `logs/companion.log`
- Review configuration: `config/default_config.yaml`
- Test components individually
- Open GitHub issue with logs and config (redact tokens!)
