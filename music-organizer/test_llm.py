#!/usr/bin/env python3
"""Test Ollama LLM for artist identification"""

import requests
import json

OLLAMA_URL = "http://100.75.240.39:11434"
MODEL = "hermes-4-14b:latest"

filenames = [
    "Dr. Feelgood.mp3",
    "Kickstart My Heart.mp3",
    "Shout at the Devil.MP3",
    "Looks That Kill.mp3",
    "Too Young to Fall in Love.mp3",
    "Wild Side.mp3",
    "Neon Knights.mp3",
    "Play That Funky music white boy.mp3",
    "Passion Rules The Game Scorpions Savage Amusement.wma",
    "Same 'Ol Situation.mp3",
    "I Walk Alone .m4a",
    "Blue Murder Valley of the Kings .mp3",
    "Nothin' at All.wma",
    "Lights.mp3",
    "Passion Rules The Game.m4a",
    "Whenever You Remember.wma",
    "Love Song (rare).mp3",
    "Starts with Goodbye.wma"
]

prompt = f"""Identify the artist for each filename. Return ONLY the artist name per line.

{chr(10).join(filenames)}

Return only the 18 artist names, one per line. No extra text."""

try:
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.1
        },
        timeout=120
    )
    response.raise_for_status()
    result = response.json()
    print(result.get("response", ""))
except Exception as e:
    print(f"Error: {e}")