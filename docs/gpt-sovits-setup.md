# GPT-SoVITS TTS Setup Guide

GPT-SoVITS provides high-quality voice cloning and text-to-speech synthesis.

## Prerequisites

- GPT-SoVITS installed in `GPT-SoVITS-v3lora-20250228/` directory
- Python 3.9+ (GPT-SoVITS requirement)
- Reference audio file (3-10 seconds of clean speech)

## Setup Steps

### 1. Prepare Reference Audio

Create a reference audio file that represents the voice you want to clone:

1. Record or find a clean audio sample (3-10 seconds)
2. Save it as `SOVITS/reference.wav`
3. The audio should be:
   - Clear speech without background noise
   - Single speaker
   - Natural speaking pace
   - WAV format (preferred)

### 2. Start GPT-SoVITS API Server

Open a separate terminal and run:

```bash
# Windows
python GPT-SoVITS-v3lora-20250228\api_v2.py -a 127.0.0.1 -p 9880

# Linux/Mac
python GPT-SoVITS-v3lora-20250228/api_v2.py -a 127.0.0.1 -p 9880
```

The server will start on `http://127.0.0.1:9880`

### 3. Configure AI Companion

Edit `config/default_config.yaml`:

```yaml
tts:
  engine: gpt_sovits
  
  # GPT-SoVITS settings
  gpt_sovits_api_url: http://127.0.0.1:9880
  gpt_sovits_ref_audio: SOVITS/reference.wav
  gpt_sovits_prompt_text: "Hello, this is a test."  # What the reference audio says
  gpt_sovits_prompt_lang: en  # Language: en, zh, ja, etc.
  gpt_sovits_text_lang: en  # Language to synthesize
  
  output_dir: Audio/
```

**Important:** `gpt_sovits_prompt_text` should match what is said in your reference audio.

### 4. Run AI Companion

```bash
python main.py --mode text
```

The AI will now use GPT-SoVITS for voice synthesis!

## Configuration Options

### Basic Settings

- `gpt_sovits_api_url`: API server address (default: `http://127.0.0.1:9880`)
- `gpt_sovits_ref_audio`: Path to reference audio file
- `gpt_sovits_prompt_text`: Transcription of reference audio
- `gpt_sovits_prompt_lang`: Language of reference audio (`en`, `zh`, `ja`, etc.)
- `gpt_sovits_text_lang`: Language to synthesize

### Advanced Settings

- `gpt_sovits_top_k`: Top-k sampling (default: 5)
- `gpt_sovits_top_p`: Top-p sampling (default: 1.0)
- `gpt_sovits_temperature`: Sampling temperature (default: 1.0)
- `gpt_sovits_speed_factor`: Speech speed multiplier (default: 1.0)
  - `0.5` = half speed (slower)
  - `1.0` = normal speed
  - `2.0` = double speed (faster)

## Supported Languages

GPT-SoVITS supports multiple languages:

- `en` - English
- `zh` - Chinese
- `ja` - Japanese
- `ko` - Korean
- `es` - Spanish
- `fr` - French
- `de` - German
- And more...

## Tips for Best Quality

### Reference Audio

1. **Length**: 3-10 seconds is ideal
2. **Quality**: Clear, no background noise
3. **Content**: Natural speech, not reading
4. **Format**: WAV, 16-bit, 22050Hz or 44100Hz

### Prompt Text

- Must accurately match what's said in reference audio
- Include punctuation for better prosody
- Use the same language as the reference audio

### Speed Factor

- Use `0.8-0.9` for more natural, slower speech
- Use `1.0` for normal speed
- Use `1.1-1.2` for faster speech
- Avoid extreme values (< 0.5 or > 2.0)

## Troubleshooting

### "Cannot connect to GPT-SoVITS API server"

**Solution:** Start the API server first:
```bash
python GPT-SoVITS-v3lora-20250228/api_v2.py
```

### "GPT-SoVITS API timeout"

**Causes:**
- Text is too long
- Server is overloaded
- GPU/CPU is slow

**Solutions:**
- Reduce `max_tokens` in LLM config
- Use shorter responses
- Upgrade hardware or use GPU

### Poor Voice Quality

**Solutions:**
1. Use better reference audio (clear, no noise)
2. Ensure prompt text matches reference audio exactly
3. Adjust `temperature` (try 0.8-1.2)
4. Try different reference audio samples

### Wrong Voice/Accent

**Solution:** The synthesized voice depends on the reference audio. Use a different reference audio file with the desired voice/accent.

## Using Multiple Voices

To switch voices dynamically:

```python
from services.tts.gpt_sovits_engine import GPTSoVITSEngine

# In your code
tts_engine.set_voice("SOVITS/voice1.wav")
tts_engine.set_prompt("This is voice one.", "en")

# Later, switch to another voice
tts_engine.set_voice("SOVITS/voice2.wav")
tts_engine.set_prompt("This is voice two.", "en")
```

## Performance

### CPU vs GPU

- **CPU**: Slower (5-15 seconds per sentence)
- **GPU**: Faster (1-3 seconds per sentence)

To use GPU, ensure PyTorch with CUDA is installed in the GPT-SoVITS environment.

### Memory Usage

- Typical: 2-4 GB RAM
- With GPU: 2-4 GB VRAM

## Advanced: Custom Models

GPT-SoVITS supports custom trained models:

1. Train your model using GPT-SoVITS training tools
2. Place models in `SOVITS/models/`
3. Update API server to use your models:

```bash
python api_v2.py -c path/to/your/config.yaml
```

## See Also

- [GPT-SoVITS GitHub](https://github.com/RVC-Boss/GPT-SoVITS)
- [Configuration Guide](configuration.md)
- [Troubleshooting](troubleshooting.md)
