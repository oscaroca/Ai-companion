# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the AI Companion system.

## General Issues

### Application Won't Start

**Symptom:** Application crashes immediately or shows configuration errors.

**Solutions:**

1. **Check Python version:**
   ```bash
   python --version  # Should be 3.8 or higher
   ```

2. **Verify virtual environment is activated:**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Reinstall dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Check configuration files exist:**
   ```bash
   # Should exist:
   config/default_config.yaml
   .env
   ```

5. **Validate configuration:**
   ```bash
   python -c "from config.config_manager import ConfigurationManager; cm = ConfigurationManager(); print('Config OK')"
   ```

### "ModuleNotFoundError"

**Symptom:** `ModuleNotFoundError: No module named 'X'`

**Solutions:**

1. **Ensure virtual environment is activated**
2. **Install missing module:**
   ```bash
   pip install <module_name>
   ```
3. **Reinstall all dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### "Configuration error: Missing required field"

**Symptom:** Application shows configuration validation errors.

**Solutions:**

1. **Check .env file exists and has required values:**
   ```bash
   # Copy from example if missing
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   ```

2. **Verify required environment variables:**
   - For OpenAI: `OPENAI_API_KEY`
   - For Discord: `DISCORD_TOKEN`
   - For Telegram: `TELEGRAM_TOKEN`
   - For WaniKani: `WANIKANI_API_KEY`

3. **Check YAML syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/default_config.yaml'))"
   ```

## LLM Backend Issues

### Kobold Connection Failed

**Symptom:** `Connection refused` or `Failed to connect to Kobold`

**Solutions:**

1. **Verify KoboldCpp is running:**
   - Open http://localhost:5001 in browser
   - Should see KoboldCpp interface

2. **Check URL in configuration:**
   ```yaml
   llm:
     kobold_url: http://localhost:5001/api/v1/generate
   ```

3. **Verify model is loaded in KoboldCpp:**
   - Check KoboldCpp console for "Model loaded"
   - Try generating text in KoboldCpp UI

4. **Check firewall settings:**
   - Allow connections to localhost:5001
   - Disable antivirus temporarily to test

5. **Try different port:**
   ```bash
   # Start KoboldCpp on different port
   koboldcpp.exe --model your-model.gguf --port 5002
   ```
   
   Then update config:
   ```yaml
   llm:
     kobold_url: http://localhost:5002/api/v1/generate
   ```

### OpenAI API Errors

**Symptom:** `OpenAI API error` or `Rate limit exceeded`

**Solutions:**

1. **Verify API key is correct:**
   ```bash
   # Check .env file
   OPENAI_API_KEY=sk-...
   ```

2. **Check API key is valid:**
   - Go to https://platform.openai.com/api-keys
   - Verify key exists and is active

3. **Check account has credits:**
   - Go to https://platform.openai.com/account/billing
   - Add payment method if needed

4. **Rate limit exceeded:**
   - Wait a few minutes
   - Reduce `openai_requests_per_minute` in config
   - Upgrade OpenAI plan

5. **Model not available:**
   - Check model name in config
   - Verify you have access to the model
   - Try `gpt-3.5-turbo` instead of `gpt-4`

### Slow LLM Responses

**Symptom:** Responses take a long time to generate.

**Solutions:**

1. **For Kobold (local):**
   - Use smaller model (7B instead of 13B)
   - Reduce `max_tokens` in config
   - Enable GPU acceleration in KoboldCpp
   - Close other applications

2. **For OpenAI:**
   - Check internet connection
   - Try different time of day
   - Reduce `max_tokens` in config

3. **Check system resources:**
   ```bash
   # Windows
   taskmgr
   
   # Linux
   htop
   ```

## TTS Issues

### "Could not find Piper model"

**Symptom:** `FileNotFoundError: Piper model not found`

**Solutions:**

1. **Download Piper model:**
   - Go to https://github.com/rhasspy/piper/releases
   - Download `.onnx` and `.onnx.json` files
   - Place in project root

2. **Verify model path in config:**
   ```yaml
   tts:
     piper_model_path: en_US-hfc_female-medium.onnx
   ```

3. **Use absolute path:**
   ```yaml
   tts:
     piper_model_path: C:/path/to/en_US-hfc_female-medium.onnx
   ```

4. **Switch to pyttsx3 temporarily:**
   ```yaml
   tts:
     engine: pyttsx3
   ```

### "pyttsx3 initialization failed"

**Symptom:** `RuntimeError: pyttsx3 initialization failed`

**Solutions:**

1. **Windows:**
   ```bash
   pip install --upgrade pyttsx3
   pip install pywin32
   ```

2. **Linux:**
   ```bash
   sudo apt-get install espeak
   pip install pyttsx3
   ```

3. **Mac:**
   ```bash
   # Should work out of the box
   # If not, try:
   pip install --upgrade pyttsx3
   ```

4. **Try different voice:**
   ```yaml
   tts:
     voice_index: 0  # Try 0, 1, 2, etc.
   ```

### No Audio Output

**Symptom:** TTS generates files but no sound plays.

**Solutions:**

1. **Check audio files are created:**
   ```bash
   ls Audio/  # Should see .wav files
   ```

2. **Test audio file manually:**
   - Open a .wav file in media player
   - If it doesn't play, audio format issue

3. **Check system audio:**
   - Verify speakers/headphones are connected
   - Check volume is not muted
   - Test with other audio

4. **Check audio format:**
   ```bash
   # Should be 44.1kHz, mono, 16-bit PCM
   ffmpeg -i Audio/response_*.wav
   ```

### Poor Audio Quality

**Symptom:** Audio sounds distorted or robotic.

**Solutions:**

1. **For Piper:**
   - Try different model (higher quality)
   - Download from https://github.com/rhasspy/piper/releases

2. **For pyttsx3:**
   - Adjust rate:
     ```yaml
     tts:
       rate: 180  # Try 150-200
     ```
   - Try different voice:
     ```yaml
     tts:
       voice_index: 1  # Try different values
     ```

3. **Check audio normalization:**
   - Verify AudioProcessor is working
   - Check logs for audio processing errors

## Speech Recognition Issues

### Microphone Not Working

**Symptom:** `No microphone detected` or speech not recognized.

**Solutions:**

1. **Check microphone permissions:**
   - Windows: Settings → Privacy → Microphone
   - Mac: System Preferences → Security & Privacy → Microphone
   - Linux: Check PulseAudio settings

2. **Test microphone:**
   ```bash
   python -m speech_recognition
   ```

3. **Install PyAudio:**
   ```bash
   # Windows
   pip install pyaudio
   
   # Linux
   sudo apt-get install portaudio19-dev python3-pyaudio
   pip install pyaudio
   
   # Mac
   brew install portaudio
   pip install pyaudio
   ```

4. **Check microphone is default device:**
   - Windows: Sound settings → Input
   - Mac: System Preferences → Sound → Input
   - Linux: PulseAudio volume control

### Speech Not Recognized

**Symptom:** Microphone works but speech is not recognized.

**Solutions:**

1. **Adjust energy threshold:**
   ```yaml
   stt:
     energy_threshold: 4000  # Try 2000-6000
   ```

2. **Check internet connection:**
   - Google Speech API requires internet
   - Test with: `ping google.com`

3. **Speak clearly and loudly:**
   - Reduce background noise
   - Speak directly into microphone
   - Avoid mumbling

4. **Check language setting:**
   ```yaml
   stt:
     language: en-US  # Match your language
   ```

5. **Adjust pause threshold:**
   ```yaml
   stt:
     pause_threshold: 0.8  # Try 0.5-1.5
   ```

### "Speech recognition timed out"

**Symptom:** Recognition times out before you finish speaking.

**Solutions:**

1. **Increase timeout in code:**
   ```python
   # In main.py, voice mode
   user_input = self.speech_recognizer.recognize_from_microphone(timeout=20)  # Increase from 10
   ```

2. **Speak faster or in shorter sentences**

3. **Adjust pause threshold:**
   ```yaml
   stt:
     pause_threshold: 1.5  # Longer pause before processing
   ```

## Memory System Issues

### "Database is locked"

**Symptom:** `sqlite3.OperationalError: database is locked`

**Solutions:**

1. **Close other instances:**
   - Only run one instance of the application
   - Check Task Manager for multiple processes

2. **Delete lock file:**
   ```bash
   # If database is not in use
   rm data/memory.db-journal  # Linux/Mac
   del data\memory.db-journal  # Windows
   ```

3. **Restart application**

### Memory Not Persisting

**Symptom:** Conversations are not remembered between sessions.

**Solutions:**

1. **Check database file exists:**
   ```bash
   ls data/memory.db  # Should exist after first run
   ```

2. **Verify storage path in config:**
   ```yaml
   memory:
     storage_path: data/memory.db
   ```

3. **Check file permissions:**
   ```bash
   # Linux/Mac
   chmod 644 data/memory.db
   ```

4. **Check logs for errors:**
   ```bash
   tail -f logs/companion.log
   ```

### Slow Memory Retrieval

**Symptom:** Long delays when retrieving memories.

**Solutions:**

1. **Reduce max_history:**
   ```yaml
   memory:
     max_history: 10  # Reduce from 20
   ```

2. **Increase similarity threshold:**
   ```yaml
   memory:
     similarity_threshold: 0.8  # Increase from 0.7
   ```

3. **Use smaller embedding model:**
   ```yaml
   memory:
     embedding_model: sentence-transformers/all-MiniLM-L6-v2
   ```

4. **Clear old data:**
   ```bash
   # Backup first!
   cp data/memory.db data/memory.db.backup
   # Then delete old messages in database
   ```

## Integration Issues

### Discord Bot Not Responding

**Symptom:** Bot is online but doesn't respond to commands.

**Solutions:**

1. **Check Message Content Intent:**
   - Go to https://discord.com/developers/applications
   - Select your bot
   - Go to Bot section
   - Enable "Message Content Intent"
   - Restart bot

2. **Check bot permissions:**
   - Bot needs "Send Messages" permission
   - Check role permissions in server

3. **Verify command prefix:**
   ```yaml
   integrations:
     discord:
       command_prefix: "!"  # Must match what you type
   ```

4. **Check logs:**
   ```bash
   tail -f logs/companion.log
   ```

5. **Try mentioning bot:**
   ```
   @BotName hello
   ```

### Discord Voice Not Working

**Symptom:** Bot joins voice channel but no audio plays.

**Solutions:**

1. **Install ffmpeg:**
   - Windows: Download from https://ffmpeg.org/download.html
   - Linux: `sudo apt-get install ffmpeg`
   - Mac: `brew install ffmpeg`

2. **Verify ffmpeg in PATH:**
   ```bash
   ffmpeg -version
   ```

3. **Set ffmpeg path in config:**
   ```yaml
   integrations:
     discord:
       ffmpeg_path: C:\ffmpeg\bin\ffmpeg.exe  # Windows
       # Or just: ffmpeg  # If in PATH
   ```

4. **Check bot voice permissions:**
   - Bot needs "Connect" and "Speak" permissions
   - Check role permissions in server

5. **Verify audio files are generated:**
   ```bash
   ls Audio/  # Should see .wav files
   ```

### Telegram Bot Not Responding

**Symptom:** Bot doesn't respond to messages.

**Solutions:**

1. **Verify bot token:**
   ```bash
   # Check .env file
   TELEGRAM_TOKEN=your-token-here
   ```

2. **Check token is valid:**
   - Message @BotFather on Telegram
   - Send `/mybots`
   - Verify your bot is listed

3. **Restart bot:**
   ```bash
   # Stop and restart
   python main.py --mode telegram
   ```

4. **Check internet connection:**
   ```bash
   ping api.telegram.org
   ```

5. **Check logs:**
   ```bash
   tail -f logs/companion.log
   ```

### WaniKani Integration Not Working

**Symptom:** WaniKani data not appearing in conversations.

**Solutions:**

1. **Verify API key:**
   ```bash
   # Check .env file
   WANIKANI_API_KEY=your-key-here
   ```

2. **Test API key:**
   ```bash
   curl -H "Authorization: Bearer your-key-here" https://api.wanikani.com/v2/user
   ```

3. **Enable integration:**
   ```yaml
   integrations:
     wanikani:
       enabled: true
   ```

4. **Clear cache:**
   ```bash
   rm data/wanikani_cache.json
   ```

5. **Check you have learned items:**
   - Go to https://www.wanikani.com
   - Verify you have completed lessons

### Unity Avatar Not Animating

**Symptom:** Unity doesn't receive animation triggers.

**Solutions:**

1. **Verify Unity is listening:**
   - Check Unity console for UDP listener
   - Verify port 5005 is open

2. **Check configuration:**
   ```yaml
   integrations:
     unity:
       enabled: true
       address: 127.0.0.1
       port: 5005
   ```

3. **Test UDP connection:**
   ```bash
   # Send test message
   echo "22|test.wav" | nc -u 127.0.0.1 5005
   ```

4. **Check firewall:**
   - Allow UDP port 5005
   - Disable firewall temporarily to test

5. **Verify audio directory:**
   ```yaml
   integrations:
     unity:
       audio_dir: Audio/  # Must be accessible by Unity
   ```

## Performance Issues

### High Memory Usage

**Symptom:** Application uses too much RAM.

**Solutions:**

1. **Reduce max_history:**
   ```yaml
   memory:
     max_history: 10
   ```

2. **Use smaller embedding model:**
   ```yaml
   memory:
     embedding_model: sentence-transformers/all-MiniLM-L6-v2
   ```

3. **Clear old audio files:**
   ```bash
   # Delete old files
   rm Audio/response_*.wav  # Linux/Mac
   del Audio\response_*.wav  # Windows
   ```

4. **Restart application periodically**

### High CPU Usage

**Symptom:** Application uses too much CPU.

**Solutions:**

1. **For Kobold:**
   - Use smaller model
   - Reduce `max_tokens`
   - Enable GPU acceleration

2. **For TTS:**
   - Use pyttsx3 instead of Piper
   - Reduce TTS rate

3. **Disable unused integrations:**
   ```yaml
   integrations:
     discord:
       enabled: false
     telegram:
       enabled: false
   ```

### Slow Responses

**Symptom:** Long delays between user input and response.

**Solutions:**

1. **Check LLM backend performance:**
   - See "Slow LLM Responses" section above

2. **Reduce memory retrieval:**
   ```yaml
   memory:
     max_history: 5
     similarity_threshold: 0.9
   ```

3. **Disable TTS temporarily:**
   ```bash
   python main.py --mode text  # No TTS
   ```

4. **Check system resources:**
   - Close other applications
   - Check disk space
   - Check network latency

## Logging and Debugging

### Enable Debug Logging

```yaml
app:
  log_level: DEBUG
```

Or in .env:
```env
LOG_LEVEL=DEBUG
```

### View Logs

```bash
# Real-time logs
tail -f logs/companion.log  # Linux/Mac
Get-Content logs\companion.log -Wait  # Windows PowerShell

# Search logs
grep ERROR logs/companion.log  # Linux/Mac
Select-String -Path logs\companion.log -Pattern "ERROR"  # Windows PowerShell
```

### Common Log Messages

**"Configuration loaded successfully"**
- Good: Configuration is valid

**"LLM backend initialized"**
- Good: LLM connection established

**"Memory system initialized"**
- Good: Database connection established

**"Failed to connect to LLM backend"**
- Bad: Check LLM backend is running

**"Input validation failed"**
- Warning: User input was rejected (security)

**"Rate limit exceeded"**
- Warning: Too many requests, user is rate limited

## Getting Help

### Before Asking for Help

1. **Check logs:**
   ```bash
   tail -100 logs/companion.log
   ```

2. **Verify configuration:**
   ```bash
   cat config/default_config.yaml
   cat .env  # Redact secrets!
   ```

3. **Test components individually:**
   ```bash
   # Test LLM
   python -c "from services.llm.kobold_backend import KoboldBackend; ..."
   
   # Test TTS
   python -c "from services.tts.pyttsx3_engine import Pyttsx3Engine; ..."
   ```

4. **Try minimal configuration:**
   - Disable all integrations
   - Use text mode
   - Use pyttsx3 TTS

### Reporting Issues

When reporting issues, include:

1. **Error message** (full traceback)
2. **Configuration** (redact secrets!)
3. **Logs** (last 50-100 lines)
4. **System information:**
   - OS and version
   - Python version
   - Installed packages: `pip list`
5. **Steps to reproduce**

### Community Support

- GitHub Issues: [Your GitHub URL]
- Discord Server: [Your Discord URL]
- Documentation: [Your Docs URL]

## FAQ

**Q: Can I use multiple LLM backends simultaneously?**
A: No, only one backend at a time. You can switch by changing config.

**Q: Can I run multiple bots (Discord + Telegram) at once?**
A: Yes, run separate processes for each mode.

**Q: How do I backup my conversation history?**
A: Copy `data/memory.db` to a safe location.

**Q: Can I use a different database (PostgreSQL, MySQL)?**
A: Currently only SQLite is supported. PostgreSQL support is planned.

**Q: How do I reset all conversations?**
A: Delete `data/memory.db` (backup first!).

**Q: Can I use custom TTS voices?**
A: Yes, download different Piper models or use system voices with pyttsx3.

**Q: How do I reduce API costs?**
A: Use local Kobold backend, reduce `max_tokens`, enable caching.

**Q: Can I run this on a server without a microphone?**
A: Yes, use text mode or bot modes (Discord, Telegram).

**Q: How do I update to the latest version?**
A: `git pull` and `pip install -r requirements.txt`.

## See Also

- [Setup Guide](setup.md) - Installation instructions
- [Configuration Guide](configuration.md) - Configuration options
- [Integration Guide](integrations.md) - Bot integrations
- [Architecture](architecture.md) - System architecture
