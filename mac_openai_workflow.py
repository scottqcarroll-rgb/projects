#!/usr/bin/env python3
"""
Workflow for dual LLM verification:
1. Get answer from Mac (local Hermes 4 14B LLM)
2. Get answer from OpenAI (via OpenRouter)
3. Compare and present both results

Usage: python mac_openai_workflow.py "Your question here"
"""

import json
import requests
import sys
from typing import Dict, Any

def query_mac_llm(question: str) -> Dict[str, Any]:
    """Query the local Mac LLM"""
    url = "http://100.75.240.39:11434/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "hermes-4-14b",
        "messages": [{"role": "user", "content": question}],
        "max_tokens": 500
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return {
            "source": "Mac LLM (Hermes 4 14B)",
            "response": response.json()
        }
    except Exception as e:
        return {
            "source": "Mac LLM (Hermes 4 14B)",
            "error": str(e)
        }

def query_openai(question: str) -> Dict[str, Any]:
    """Query OpenAI via OpenRouter"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    api_key = "4aa10f03a61e484189d1c8e1baa34d70.kvYiU58dcgybDEZw"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-Title": "HERMES Workflow"
    }
    data = {
        "model": "gpt-3.5-turbo",  # You can change this to other models
        "messages": [{"role": "user", "content": question}],
        "max_tokens": 500
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return {
            "source": "OpenAI (via OpenRouter)",
            "response": response.json()
        }
    except Exception as e:
        return {
            "source": "OpenAI (via OpenRouter)",
            "error": str(e)
        }

def extract_content(result: Dict[str, Any]) -> str:
    """Extract the content from an LLM response"""
    if "error" in result:
        return f"ERROR ({result['source']}): {result['error']}"
    
    try:
        return result["response"]["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        return f"UNPARSEABLE RESPONSE ({result['source']}): {str(e)}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python mac_openai_workflow.py \"Your question here\"")
        print("Example: python mac_openai_workflow.py \"What is the capital of France?\"")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    
    print(f"🔍 Question: {question}")
    print("\n" + "="*60)
    print("MAC LLM RESULT:")
    print("="*60)
    
    mac_result = query_mac_llm(question)
    mac_content = extract_content(mac_result)
    print(mac_content)
    
    print("\n" + "="*60)
    print("OPENAI RESULT:")
    print("="*60)
    
    openai_result = query_openai(question)
    openai_content = extract_content(openai_result)
    print(openai_content)
    
    print("\n" + "="*60)
    print("COMPARISON:")
    print("="*60)
    
    # Simple comparison metrics
    mac_words = len(mac_content.split()) if mac_content else 0
    openai_words = len(openai_content.split()) if openai_content else 0
    
    print(f"Mac LLM word count: {mac_words}")
    print(f"OpenAI word count: {openai_words}")
    
    if "ERROR" not in mac_content and "ERROR" not in openai_content:
        # Check if content is similar (basic check)
        mac_lower = mac_content.lower().strip()
        openai_lower = openai_content.lower().strip()
        
        if mac_lower == openai_lower:
            print("✅ CONTENT MATCH: Both LLMs provided identical responses")
        else:
            # Check if answers are logically consistent
            mac_sentences = mac_content.split('.')[:2]
            openai_sentences = openai_content.split('.')[:2]
            
            if mac_sentences and openai_sentences:
                print("📊 SIDE-BY-SIDE COMPARISON:")
                print(f"Mac LLM: {mac_sentences[0]}")
                print(f"OpenAI:  {openai_sentences[0]}")

if __name__ == "__main__":
    main()