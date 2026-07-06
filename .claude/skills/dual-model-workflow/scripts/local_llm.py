#!/usr/bin/env python3
"""
Local LLM Client — calls Gemma 4 E4B on Mac Studio via HTTP API
Usage: python3 local_llm.py "Your prompt here" [--max-tokens 512] [--temperature 0.7] [--raw]

NEVER use SSH to reach the local LLM. Always use this script or direct HTTP calls.
"""
import sys
import json
import argparse
import urllib.request
import urllib.error
import time

LLM_URL = "http://192.168.1.174:8081/v1/chat/completions"
MODEL = "gemma-4-E4B-it-Q4_K_M.gguf"

def chat(prompt, max_tokens=512, temperature=0.7, system=None):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        LLM_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - start
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                return {
                    "content": content,
                    "time": elapsed,
                    "tokens": usage.get("total_tokens", 0),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "model": result.get("model", MODEL),
                    "timings": result.get("timings", {})
                }
            else:
                return {"error": "No response", "raw": result, "time": elapsed}
    except urllib.error.URLError as e:
        return {"error": f"Connection failed: {e.reason}", "time": time.time() - start}
    except Exception as e:
        return {"error": str(e), "time": time.time() - start}

def main():
    parser = argparse.ArgumentParser(description="Query local Gemma 4 E4B model")
    parser.add_argument("prompt", nargs="?", help="Prompt to send")
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--system", type=str, default=None)
    parser.add_argument("--raw", action="store_true", help="Output raw JSON")
    
    args = parser.parse_args()
    
    if not args.prompt:
        args.prompt = sys.stdin.read().strip()
    
    if not args.prompt:
        print("Error: No prompt provided", file=sys.stderr)
        sys.exit(1)
    
    result = chat(args.prompt, max_tokens=args.max_tokens, 
                   temperature=args.temperature, system=args.system)
    
    if args.raw:
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        else:
            print(result["content"])
            timings = result.get("timings", {})
            gen_t = timings.get("predicted_ms", 0)
            prompt_t = timings.get("prompt_ms", 0)
            print(f"\n--- [{result['time']:.2f}s total | prompt: {prompt_t:.0f}ms | gen: {gen_t:.0f}ms | {result['tokens']} tokens | {result['model']}]",
                  file=sys.stderr)

if __name__ == "__main__":
    main()
