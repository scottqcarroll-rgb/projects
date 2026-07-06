# Dual-Model Performance Benchmarks

## Test Environment
- **Local:** Mac Studio M2 Max, 32GB, llama.cpp (Metal), Gemma 4 E4B Q4_K_M
- **Remote:** OpenRouter OWL-Alpha (openrouter/owl-alpha)
- **Network:** Direct HTTP (no SSH) for local; internet API for OpenRouter

## Benchmark Results

### Test 1: Research Task (USS Drum history)
| Metric | Gemma 4 E4B (Local) | OpenRouter |
|--------|---------------------|------------|
| Method | Subagent via SSH | Direct |
| Time | 302s (5 min) | ~10s |
| Accuracy | ✅ Complete | ✅ Complete |
| Detail | More granular battle details | Better formatting, officer table |

**Lesson:** Subagent + SSH overhead dominated. Model quality was equivalent.

### Test 2: Prime Palindromes (1 to 10M) — Unfair (different algorithms)
| Metric | Gemma 4 E4B | OpenRouter |
|--------|-------------|------------|
| Time | 39.3s | 0.76s |
| Algorithm | Trial division | Sieve of Eratosthenes |
| Results | 781 / 9,989,899 / 3,502,233,298 | Identical |

**Lesson:** Algorithm choice dominated. Not a fair model comparison.

### Test 3: Prime Palindromes — Fair (both Sieve)
| Metric | Gemma 4 E4B (HTTP) | OpenRouter |
|--------|---------------------|------------|
| Time | 16.98s | 0.77s |
| Prompt processing | 639ms | — |
| Generation | 16,343ms (1,148 tokens) | — |
| Speed | ~60 tok/s | — |
| Results | Identical | Identical |

**Lesson:** OpenRouter ~22x faster for generation. Local model bottleneck is pure compute on M2 Max (no GPU). Local wins on privacy, zero cost, no internet dependency.

### Test 4: Simple Query ("Say hello")
| Metric | Gemma 4 E4B (HTTP) |
|--------|---------------------|
| Time | 0.22s |
| Prompt | 137ms |
| Generation | 19ms (2 tokens) |

**Lesson:** For short responses, local HTTP is extremely fast. Overhead is negligible.

## Key Takeaways
- **Local model speed:** ~100ms prompt + ~16ms/token. Good for long-form reasoning.
- **OpenRouter speed:** Faster for generation (GPU clusters), but adds network round-trip.
- **When to use local:** Privacy-sensitive work, no internet, full control, zero API cost.
- **When to use OpenRouter:** Speed-critical tasks, complex reasoning that benefits from larger models.
- **Never use SSH for local LLM calls** — adds 30-40s overhead per request.
