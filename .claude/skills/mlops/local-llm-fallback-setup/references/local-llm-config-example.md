---
name: local-llm-config-example
description: Example configuration for local LLM fallback setup in Hermes Agent
version: 1.0.0
author: Scott
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [local-llm, fallback, gemma, config, example]
    category: mlops
---
# Local LLM Fallback Configuration Example

## Configuration Example

```yaml
# Primary model configuration
model:
  provider: openrouter
  base_url: https://openrouter.ai/api/v1
  context_length: 65536
  default: openrouter/free

# Fallback provider configuration (local LLM on Mac Studio)
fallback_providers:
  - provider: local
    base_url: http://[IP_ADDRESS]:8081/v1
    model: gemma-4-E4B-it-Q4_K_M.gguf
    api_key: ""
```

## Configuration Details

### Primary Provider
- Provider: openrouter
- Base URL: https://openrouter.ai/api/v1
- Default Model: openrouter/free

### Fallback Provider
- Provider: local
- Base URL: http://[IP_ADDRESS]:8081/v1
- Model: gemma-4-E4B-it-Q4_K_M.gguf
- API Key: (empty string)

## Configuration Notes

1. **Network Requirements**: The Mac Studio must be reachable via the specified IP address through Tailscale
2. **Model Requirements**: Gemma 4 E4B model must be loaded and ready to serve requests at the specified endpoint
3. **API Key**: Local LLM services typically don't require API keys, hence the empty string
4. **Fallback Priority**: The local model will be used when available, with OpenRouter as the secondary fallback

## Configuration Validation

To verify the setup works:

1. Check configuration file:
```bash
grep -A5 "fallback_providers" ~/.hermes/config.yaml
```

2. Test connectivity:
```bash
curl -s http://[IP_ADDRESS]:8081/v1/models | head -20
```

## Common Issues & Solutions

1. **Connection refused**: Verify the local LLM server is running and listening on port 8081
2. **Invalid model name**: Confirm the model file name matches exactly (case-sensitive)
3. **Timeout errors**: Check if the local LLM server is responding within reasonable timeframe