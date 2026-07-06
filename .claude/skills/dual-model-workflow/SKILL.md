---
name: dual-model-workflow
description: Run tasks against both local Gemma 4 E4B (via HTTP) and OpenRouter model simultaneously, then compare outputs
tools: terminal
---

# Dual-Model Workflow — Local LLM vs OpenRouter

## When to Use

When the user asks to "run a dual-model test", "compare models", or "test the local model", use this workflow to dispatch the same prompt to both:
1. **Local Gemma 4 E4B** — via HTTP API at `http://192.168.1.174:8081/v1/chat/completions`
2. **OpenRouter model** — the currently active session model (OWL/nex-agi)

## How It Works

### Step 1: Send to Local Model (parallel)

Run the Python client script directly — no SSH needed:

```bash
python3 ~/.hermes/skills/dual-model-workflow/local_llm.py "PROMPT HERE" --max-tokens 500 2>&1
```

Or use a one-liner curl:

```bash
curl -s http://192.168.1.174:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma-4-E4B-it-Q4_K_M.gguf","messages":[{"role":"user","content":"PROMPT HERE"}],"max_tokens":500}'
```

### Step 2: Generate Local Response

The script returns output with timing info on stderr:
```
--- [X.XXs total | prompt: XXXms | gen: XXXms | XX tokens | gemma-4-E4B-it-Q4_K_M.gguf]
```

### Step 3: Generate OpenRouter Response

Respond to the same prompt using the active session model (OWL/nex-agi via OpenRouter).

### Step 4: Compare

Present results side-by-side:

| Metric | Gemma 4 E4B (Local) | OpenRouter Model |
|---|---|---|
| **Time** | X.XXs | X.XXs |
| **Tokens** | XX | XX |
| **Content** | [summary] | [summary] |
| **Winner** | 🏆 or — | 🏆 or — |

## Key Details

- **Model:** gemma-4-E4B-it-Q4_K_M.gguf (7.5B params)
- **Server:** Mac Studio M2 Max at 192.168.1.174:8081
- **API:** OpenAI-compatible via llama.cpp
- **Speed:** ~100ms prompt, ~16ms/token generation (~60 tok/s)
- **Context:** 64K tokens
- **Thinking:** Gemma 4 uses reasoning tokens (chain-of-thought) — visible in raw responses

## Linked Files

- `scripts/local_llm.py` — Reusable Python client for local Gemma 4 HTTP API
- `references/performance-benchmarks.md` — Speed/quality benchmarks from 4 test runs

## Pitfalls

1. **NEVER SSH for local LLM** — This is a hard rule. Always use HTTP at `http://192.168.1.174:8081`. SSH adds 30-40s of overhead per call and defeats the purpose of fast local inference. SSH is only for server administration.
2. **max_tokens too small** — Gemma 4 will cut off mid-sentence if max_tokens is too low. Use 500+ for paragraphs, 200+ for single sentences.
3. **Thinking tokens** — Gemma 4 may use significant "thinking" tokens before outputting visible content. This increases token usage but improves quality. The raw response includes a `timings` object with `prompt_ms` and `predicted_ms` — use these for accurate billing.
4. **Model name** — Always use `gemma-4-E4B-it-Q4_K_M.gguf` as the model ID.
5. **Subagent vs direct HTTP** — Do NOT use `delegate_task` to query the local model. It adds SSH + agent overhead (30-60s). Call the HTTP API directly from the terminal or via `execute_code`.
6. **Content truncation** — If the response appears empty but timing shows generation happened, the content was likely cut off by max_tokens. Increase to 1000+ for code generation tasks.
7. **Gateway restart required after config changes** — If you change `~/.hermes/.env` (e.g., adding a new platform token), you must restart the gateway from a SEPARATE shell: `systemctl --user restart hermes-gateway`. You cannot restart from inside the running gateway process (SIGTERM propagation kills the command).
