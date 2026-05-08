#!/usr/bin/env python3
"""
AI Assessment Analyzer
Reads a transcript file, sends it to Claude, outputs a structured Markdown report.

Usage:
    python3 analyze.py <transcript_file>
    python3 analyze.py sample_transcripts/amazon_seller.txt
"""

import sys
import os
import anthropic
from pathlib import Path
from datetime import date

PROMPT_TEMPLATE_PATH = Path(__file__).parent / "prompt_template.md"
REPORTS_DIR = Path(__file__).parent / "reports"


def load_prompt_template() -> str:
    with open(PROMPT_TEMPLATE_PATH) as f:
        content = f.read()
    # Return only the prompt portion (before the transcript placeholder)
    parts = content.split("## THE PROMPT")
    return parts[1].split("## TRANSCRIPT TO ANALYZE:")[0].strip()


def analyze_transcript(transcript_path: str) -> str:
    transcript = Path(transcript_path).read_text()
    prompt = load_prompt_template()

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\n## TRANSCRIPT TO ANALYZE:\n\n{transcript}"
            }
        ]
    )

    return message.content[0].text


def save_report(report: str, transcript_path: str) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    stem = Path(transcript_path).stem
    output_path = REPORTS_DIR / f"{stem}_{date.today().isoformat()}.md"
    output_path.write_text(report)
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze.py <transcript_file>")
        sys.exit(1)

    transcript_path = sys.argv[1]

    if not Path(transcript_path).exists():
        print(f"Error: File not found: {transcript_path}")
        sys.exit(1)

    print(f"Analyzing transcript: {transcript_path}")
    print("Sending to Claude... (this may take 30–60 seconds)")

    report = analyze_transcript(transcript_path)
    output_path = save_report(report, transcript_path)

    print(f"\nReport saved to: {output_path}")
    print("\n" + "="*60)
    print(report)


if __name__ == "__main__":
    main()
