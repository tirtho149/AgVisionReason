#!/usr/bin/env python3
"""
Convert a PDF file to well-formatted Markdown using Claude's PDF support API.
source ~/miniconda3/etc/profile.d/conda.sh && conda activate vl-reasoning && python /Users/muhammadarbabarshad/build2026-local/reasoning/pdf_to_markdown.py /Users/muhammadarbabarshad/build2026-local/reasoning/soybean-compressed.pdf
"""

import os
import sys
import base64
import argparse
from pathlib import Path
from dotenv import dotenv_values
import anthropic

# Load environment variables from .env file
env_file = Path(__file__).parent / ".env"
env_vars = dotenv_values(env_file)
for key, value in env_vars.items():
    if value:
        os.environ[key] = value

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 8192

SYSTEM_PROMPT = (
    "You are a document conversion assistant. Convert the provided PDF content "
    "into clean, well-structured Markdown. Preserve all headings, lists, tables, "
    "code blocks, bold/italic formatting, and document structure. Do not add any "
    "commentary — output only the Markdown conversion of the document."
)


def convert_pdf_to_markdown(pdf_path: Path, model: str) -> str:
    pdf_data = base64.standard_b64encode(pdf_path.read_bytes()).decode("utf-8")

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Convert this PDF to Markdown.",
                    },
                ],
            }
        ],
    )

    return message.content[0].text


def main():
    parser = argparse.ArgumentParser(description="Convert a PDF file to Markdown using Claude.")
    parser.add_argument("pdf", type=Path, help="Path to the input PDF file")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output Markdown file path")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Claude model to use (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"Error: PDF file not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or args.pdf.with_suffix(".md")

    print(f"Converting {args.pdf} -> {output_path} (model: {args.model})")
    markdown = convert_pdf_to_markdown(args.pdf, args.model)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Done. Output written to {output_path}")


if __name__ == "__main__":
    main()
