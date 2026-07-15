# Hermes-4-14B Installation on Mac Studio (Session: 2026-07-14)

## Overview
Installed Hermes-4-14B (NousResearch, Qwen3-14B based, native function calling) on Mac Studio via Ollama with custom GGUF from Hugging Face.

## Steps Executed

### 1. Download GGUF from Hugging Face
```bash
# On Mac Studio (via SSH)
pip3 install huggingface_hub -q
python3 -c "
from huggingface_hub import hf_hub_download
path = hf_hub_download(
    repo_id='bartowski/NousResearch_Hermes-4-14B-GGUF',
    filename='NousResearch_Hermes-4-14B-Q4_K_M.gguf',
    local_dir='/Users/scott/models',
    local_dir_use_symlinks=False
)
print('Downloaded to:', path)
"
```
**Result**: `NousResearch_Hermes-4-14B-Q4_K_M.gguf` (9.0 GB) downloaded to `/Users/scott/models/`

### 2. Create Modelfile with Qwen3 Chat Template
```python
content = """FROM /Users/scott/models/NousResearch_Hermes-4-14B-Q4_K_M.gguf
TEMPLATE "{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
{{ end }}<|assistant|>"
PARAMETER stop "<|end|>"
PARAMETER stop "<|user|>"
PARAMETER stop "<|system|>"
PARAMETER stop "<|assistant|>"
"""
```
Written to `/tmp/Modelfile`

### 3. Create Ollama Model
```bash
/Applications/Ollama.app/Contents/Resources/ollama create hermes-4-14b -f /tmp/Modelfile
```
**Output**: Successfully created `hermes-4-14b:latest` (9.0 GB)

### 4. Verify Function Calling
```bash
# Via Ollama API with tools parameter
curl -X POST http://localhost:11434/api/chat -d '{
  "model": "hermes-4-14b",
  "messages": [{"role": "user", "content": "What is the weather in Atlanta?"}],
  "tools": [{"type": "function", "function": {"name": "get_weather", "description": "Get current weather", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}}],
  "stream": false
}'
```
**Result**: Returns `tool_calls` array with `function.name: "get_weather"` and `arguments: {"location": "Atlanta"}` — **native function calling works**.

### 5. Clean Up Old Models
```bash
ollama rm llama3.2:3b qwen3:14b nous-hermes:13b
```

### 6. Dashboard Integration
- API endpoint `/api/mac-studio/ollama` now shows:
```json
{
  "models": [{"name": "hermes-4-14b:latest", "size": "9.0 GB", "size_gb": 9.0}],
  "models_installed": 1,
  "ollama_running": true
}
```

## Key Learnings

1. **Hermes-4-14B is Qwen3-based** — use Qwen3 chat template (`<|system|>`, `<|user|>`, `<|assistant|>`, `<|end|>` tokens)
2. **Ollama supports custom GGUF via Modelfile** — `FROM` points to local file path
3. **Function calling is native** — model outputs structured `tool_calls` when `tools` parameter provided in API request
4. **Hugging Face `bartowski` quantizations are reliable** — Q4_K_M worked perfectly
5. **Ollama on Mac Studio runs at `/Applications/Ollama.app/Contents/Resources/ollama`** (not brew)

## Files Created/Modified
- `/Users/scott/models/NousResearch_Hermes-4-14B-Q4_K_M.gguf` (9 GB)
- `/tmp/Modelfile` (template)
- Ollama model: `hermes-4-14b:latest` (9.0 GB)

## Verification Commands
```bash
# List models
ollama list

# Test inference
ollama run hermes-4-14b "What is 2+2?"

# Test function calling via API
curl -X POST http://localhost:11434/api/chat -d '{...}' | python3 -m json.tool
```