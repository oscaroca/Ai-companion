# Setup Guide

This guide will help you set up the AI Companion system from scratch.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- Microphone (for voice mode)
- Speakers or headphones (for audio output)

## Step-by-Step Setup

### 1. Python Environment

#### Windows

```powershell
# Check Python version
python --version

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

#### Linux/Mac

```bash
# Check Python version
python3 --version

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 2. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 3. System Dependencies

#### FFmpeg (Required for audio processing)

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH

**Linux:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

#### PyAudio (Required for microphone input)

**Windows:**
```bash
pip install pyaudio
```

**Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**Mac:**
```bash
brew install portaudio
pip install pyaudio
```

### 4. Configuration

#### Create Environment File

```bash
# Copy example file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

#### Edit .env File

Open `.env` in a text editor and configure:

```env
# LLM Backend
OPENAI_API_KEY=sk-your-openai-key-here  # If using OpenAI

# Bot Integrations (optional)
DISCORD_TOKEN=your-discord-token
TELEGRAM_TOKEN=your-telegram-token

# External Services (optional)
WANIKANI_API_KEY=your-wanikani-key

# Application Settings
LOG_LEVEL=INFO
DEFAULT_MODE=voice
```

#### Configure YAML (Optional)

Edit `config/default_config.yaml` to customize:
- LLM backend settings
- TTS engine preferences
- Memory system parameters
- Integration options

### 5. Download Models

#### For Kobold (Local LLM)

1. Download KoboldCpp:
   - https://github.com/LostRuins/koboldcpp/releases
   - Extract to `llm model start/` directory

2. Download a GGUF model:
   - Hugging Face: https://huggingface.co/models?search=gguf
   - Recommended: Mistral-7B or Llama-3.1-8B
   - Place in `llm model start/` directory

3. Start KoboldCpp:
   ```bash
   cd "llm model start"
   koboldcpp.exe --model your-model.gguf --port 5001
   ```

#### For Piper TTS

1. Download a Piper voice model:
   - https://github.com/rhasspy/piper/releases
   - Recommended: `en_US-hfc_female-medium`

2. Place `.onnx` and `.onnx.json` files in project root

3. Update config:
   ```yaml
   tts:
     engine: piper
     piper_model_path: en_US-hfc_female-medium.onnx
   ```

### 6. Test Installation

#### Test Configuration

```bash
python -c "from config.config_manager import ConfigurationManager; cm = ConfigurationManager(); print('Config OK')"
```

#### Test LLM Backend

```bash
# For Kobold (ensure KoboldCpp is running)
python -c "from services.llm.kobold_backend import KoboldBackend; from config.settings import LLMConfig; kb = KoboldBackend(LLMConfig()); print('Kobold OK' if kb.is_available() else 'Kobold not available')"
```

#### Test TTS

```bash
python -c "from services.tts.pyttsx3_engine import Pyttsx3Engine; from services.audio.audio_processor import AudioProcessor; from config.settings import TTSConfig; tts = Pyttsx3Engine(TTSConfig(), AudioProcessor()); print('TTS OK')"
```

### 7. First Run

#### Text Mode (No microphone required)

```bash
python main.py --mode text
```

Type messages to test the AI companion.

#### Voice Mode

```bash
python main.py --mode voice
```

Speak to interact with the AI companion.

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
```bash
# Ensure virtual environment is activated
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Microphone Not Working

1. Check system microphone permissions
2. Test with: `python -m speech_recognition`
3. Adjust `energy_threshold` in config if needed

### Kobold Connection Failed

1. Ensure KoboldCpp is running
2. Check URL in config matches KoboldCpp
3. Try accessing http://localhost:5001 in browser

### Audio Quality Issues

1. Try different TTS engines (piper vs pyttsx3)
2. Adjust `rate` and `volume` in config
3. Check audio output device settings

### Memory/Performance Issues

1. Reduce `max_history` in memory config
2. Use smaller LLM model
3. Disable embeddings if not needed

## Next Steps

- Customize system prompt in `prompts/default.txt`
- Configure integrations (Discord, Telegram)
- Set up Unity avatar (see Unity integration guide)
- Explore advanced configuration options

## Getting Help

- Check README.md for general information
- See docs/troubleshooting.md for common issues
- Open an issue on GitHub for bugs
