---
name: macstudio-ollama-setup
description: Installing and managing Ollama models on Mac Studio for local LLM inference
version: 1.0.0
author: Scott
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [ollama, macstudio, qwen3, hermes, local-llm, function-calling]
    category: mlops
---

# Mac Studio Ollama Setup Reference

## Session Context
Date: 2026-07-14
Task: Install Hermes-4-14B (Qwen3-14B based, native function calling) on Mac Studio, remove old LLM

### Key Findings

### Hermes-4-14B Availability (UPDATE: 2026-07-15)
**NOW AVAILABLE as custom Ollama model** on Mac Studio at 100.75.240.39:11434

Installed as custom model `hermes-4-14b` from GGUF (bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M):
```bash
# Created via Modelfile with Qwen3 chat template
FROM /Users/scott/models/NousResearch_Hermes-4-14B-Q4_K_M.gguf
TEMPLATE "{{ if .System }}<|system|>\n{{ .System }}<|end|>\n{{ end }}{{ if .Prompt }}<|user|>\n{{ .Prompt }}<|end|>\n{{ end }}<|assistant|>"
PARAMETER stop "<|end|>"
PARAMETER stop "<|user|>"
PARAMETER stop "<|system|>"
PARAMETER stop "<|assistant|>"
```
```bash
ollama create hermes-4-14b -f /tmp/Modelfile
```

Verified running at `http://100.75.240.39:11434/v1` with native function calling support.

### Previous Best Alternatives (Historical)

| Model | Size | Base | Function Calling | Notes |
|-------|------|------|------------------|-------|
| `qwen3:14b` | 9.3 GB | Qwen3-14B | ✅ Native (Qwen3 has built-in tool use) | **Closest match** — same base as Hermes-4-14B |
| `nous-hermes:13b` | 7.4 GB | Llama 2 | ⚠️ Limited | Hermes family, but Llama-based not Qwen |
| `nous-hermes:7b` | 4.1 GB | Llama 2 | ⚠️ Limited | Smaller variant |

### hermes-4-14b Verification
```bash
curl -s http://100.75.240.39:11434/v1/chat/completions -X POST -d '{"model": "hermes-4-14b", "messages": [{"role": "user", "content": "Call get_weather with location=NYC"}], "tools": [{"type": "function", "function": {"name": "get_weather", "description": "Get weather", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}]}, "stream": false}'
```
→ Returns `tool_calls` with function name and arguments (native function calling works)

## Commands Reference

### Install Ollama
```bash
ssh macstudio "curl -fsSL https://ollama.com/install.sh | sh"
```

### Start Ollama Service
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama serve &"
# Or launch via GUI: open /Applications/Ollama.app
```

### Pull Models
```bash
# Qwen3 14B (recommended for function calling)
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama pull qwen3:14b"

# Nous Hermes 13B
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama pull nous-hermes:13b"
```

### List Models
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama list"
```

### Remove Models
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama rm llama3.2:3b"
```

### Test Model
```bash
ssh macstudio "/Applications/Ollama.app/Contents/Resources/ollama run qwen3:14b 'What is 2+2?'"
```

## Dashboard Integration

### API Endpoint
`GET /api/mac-studio/ollama`

### Response Format
```json
{
  "status": "ok",
  "ollama_running": true,
  "models_installed": 2,
  "models": [
    {
      "name": "qwen3:14b",
      "size": "9.3 GB",
      "size_gb": 9.3,
      "modified": "2 minutes ago",
      "running": false
    },
    {
      "name": "nous-hermes:13b",
      "size": "7.4 GB",
      "size_gb": 7.4,
      "modified": "30 seconds ago",
      "running": false
    }
  ],
  "running_models": []
}
```

### Data Fetcher Function
`get_mac_studio_ollama_status()` in `data_fetcher.py`
- Parses `ollama list` text output via SSH
- Checks running models via `curl http://localhost:11434/api/tags`

## Next Steps (When Hermes-4-14B Becomes Available)

1. Watch Ollama library: `ollama search hermes` periodically
2. Check HuggingFace: `NousResearch/Hermes-4-14B-GGUF` for GGUF releases
3. When available: `ollama pull nousresearch/hermes-4-14b` (or similar name)
4. Test function calling: `ollama run hermes-4-14b 'Call get_weather with location=NYC'`
5. Update dashboard if model name changes

## Hardware Context
- Mac Studio M2 Max, 32 GB RAM
- Models stored in Ollama's default location (~/.ollama/models)
- 9.3 GB model fits comfortably with 32 GB RAM