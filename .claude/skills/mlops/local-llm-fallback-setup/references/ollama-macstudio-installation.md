# Ollama Installation & Model Management on Mac Studio

## Overview
This reference documents the process of installing Ollama on Mac Studio, pulling models, and managing them — specifically for the task of replacing a local LLM with a function-calling capable model (Hermes-4-14B / Qwen3-14B based).

## Prerequisites
- SSH access to Mac Studio via alias `macstudio`
- macOS 26.5.2 (or compatible)
- At least 16 GB RAM for 14B models

## Installation

### Install Ollama
```bash
ssh macstudio "curl -fsSL https://ollama.com/install.sh | sh"
```

### Start Ollama Service
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama serve &"
```

### Verify Installation
```bash
ssh macstudio "curl -s http://localhost:11434/api/tags"
# Should return: {"models":[]}
```

## Model Management

### List Available Models on Ollama Library
```bash
# View available nous-hermes tags
ssh macstudio "curl -s https://ollama.com/library/nous-hermes | grep -o 'href=\"/library/nous-hermes:[^\"]*' | sed 's/href=\"//g'"

# Output:
# /library/nous-hermes:latest
# /library/nous-hermes:7b
# /library/nous-hermes:13b
```

### Pull Recommended Models for Function Calling

#### Qwen3 14B (Base model for Hermes-4-14B, native tool calling)
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama pull qwen3:14b"
# Size: ~9.3 GB
```

#### Nous Hermes 13B (Llama-based Hermes)
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama pull nous-hermes:13b"
# Size: ~7.4 GB
```

### List Installed Models
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama list"
# Output:
# NAME           ID              SIZE      MODIFIED      
# qwen3:14b      bdbd181c33f2    9.3 GB    3 minutes ago   
# nous-hermes:13b e6251854aa4c   7.4 GB    4 seconds ago   
```

### Remove Unused Models
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama rm llama3.2:3b"
# Output: deleted 'llama3.2:3b'
```

## Testing Function Calling

### Test Qwen3 Tool Calling
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama run qwen3:14b 'Call a function called get_weather with arguments {\"location\": \"New York\"}'"
```
- Qwen3 outputs JSON-style function calls in its response
- Native function calling support built-in

### Test Model Response
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama run qwen3:14b 'What is 2+2?'"
```

## Current Limitations

### Hermes-4-14B Not Yet on Ollama Library
As of 2026-07-14:
- `ollama pull hermes-4-14b` → "file does not exist"
- `ollama pull nousresearch/hermes-4-14b` → "file does not exist"
- `ollama pull bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M` → "file does not exist"
- HuggingFace GGUF downloads return 401 (requires auth) or 404

### Workaround: Use Base Model
**Qwen3:14b is the best available option** — it's the exact base model (Qwen3-14B) that Hermes-4-14B is fine-tuned from, and Qwen3 has native function calling support.

## Dashboard Integration

### API Endpoint: `/api/mac-studio/ollama`
Added to dashboard to monitor Ollama models on Mac Studio:

```python
def get_mac_studio_ollama_status():
    # Parses `ollama list` text output
    # Checks running models via `curl localhost:11434/api/tags`
    return {
        'status': 'ok',
        'ollama_running': True,
        'models_installed': 2,
        'models': [
            {'name': 'qwen3:14b', 'size': '9.3 GB', 'size_gb': 9.3, 'running': False},
            {'name': 'nous-hermes:13b', 'size': '7.4 GB', 'size_gb': 7.4, 'running': False}
        ],
        'running_models': []
    }
```

### Frontend Display
```javascript
async function loadMacStudioOllama() {
    const res = await fetch('/api/mac-studio/ollama');
    const data = await res.json();
    // Render model list with sizes and running status
}
```

## Troubleshooting

### Ollama Not Running
```bash
# Check if process exists
ssh macstudio "ps aux | grep ollama"

# Start if needed
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama serve &"
```

### Model Pull Fails
- Check disk space: `ssh macstudio "df -h /Users/scott"`
- Check network: `ssh macstudio "curl -I https://ollama.com"`
- Try different tag: `:latest`, `:7b`, `:13b`, `:14b`

### SSH Connection Issues
```bash
# Test SSH alias
ssh macstudio "echo connected"

# If fails, check ~/.ssh/config for macstudio entry
```

## Future: When Hermes-4-14B Becomes Available

Watch for Ollama library additions:
```bash
# Periodically check
ssh macstudio "curl -s https://ollama.com/library/nous-hermes | grep -i hermes-4"

# Or search all Ollama models
ssh macstudio "curl -s https://ollama.com/library | grep -i hermes"
```

When available, pull and test:
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama pull nous-hermes:14b"
# or
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama pull hermes-4-14b"
```