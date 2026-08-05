#!/usr/bin/env python3
"""
summarize.py - Windows-native replacement for the summarize CLI.

Supports:
  - URL summarization via requests + html text extraction
  - Local file summarization (text, PDF)
  - YouTube video summarization (via yt-dlp or transcript API)
  - Multiple LLM backends: Google Gemini, OpenAI, Anthropic, xAI
  - Command-line flags compatible with the original summarize CLI

Environment variables:
  GEMINI_API_KEY, GOOGLE_GENERATIVE_AI_API_KEY, GOOGLE_API_KEY
  OPENAI_API_KEY
  ANTHROPIC_API_KEY
  XAI_API_KEY
"""

import argparse
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Optional dependencies: try to import, degrade gracefully if missing
try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore[misc,assignment]

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None  # type: ignore[misc,assignment]

try:
    import yt_dlp
except ImportError:
    yt_dlp = None  # type: ignore[misc,assignment]


DEFAULT_MODEL = "google/gemini-3-flash-preview"
CONFIG_PATH = Path.home() / ".summarize" / "config.json"

# Length presets mapped to approximate max chars of summary output
LENGTH_MAP = {
    "short": 150,
    "medium": 300,
    "long": 600,
    "xl": 1200,
    "xxl": 2400,
}


def load_config() -> dict[str, Any]:
    """Load optional ~/.summarize/config.json."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def resolve_model(cli_model: str | None) -> str:
    """Resolve model from CLI arg, config file, or default."""
    if cli_model:
        return cli_model
    cfg = load_config()
    return cfg.get("model", DEFAULT_MODEL)


def resolve_api_key(model: str) -> str | None:
    """Extract provider prefix and return first available API key."""
    provider = model.split("/")[0].lower()

    key_map: dict[str, list[str]] = {
        "google": ["GEMINI_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY", "GOOGLE_API_KEY"],
        "gemini": ["GEMINI_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY", "GOOGLE_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "xai": ["XAI_API_KEY"],
    }

    for env_var in key_map.get(provider, []):
        key = os.environ.get(env_var)
        if key:
            return key
    return None


def extract_text_from_html(html: str) -> str:
    """Extract readable text from raw HTML."""
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        # Remove script/style tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
    else:
        # Fallback: strip tags with regex
        text = re.sub(r"<[^>]+>", " ", html)

    # Collapse whitespace
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text


def fetch_url(url: str) -> str:
    """Fetch URL and return extracted text."""
    if requests is None:
        sys.stderr.write("Error: 'requests' is required for URL fetching.\n")
        sys.stderr.write("Install: pip install requests beautifulsoup4\n")
        sys.exit(1)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        sys.stderr.write(f"Error fetching URL: {exc}\n")
        sys.exit(1)

    return extract_text_from_html(resp.text)


def extract_pdf_text(path: Path) -> str:
    """Extract text from a PDF file."""
    if PyPDF2 is None:
        sys.stderr.write("Error: 'PyPDF2' is required for PDF extraction.\n")
        sys.stderr.write("Install: pip install PyPDF2\n")
        sys.exit(1)

    text_parts: list[str] = []
    try:
        with open(path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as exc:
        sys.stderr.write(f"Error reading PDF: {exc}\n")
        sys.exit(1)

    return "\n".join(text_parts)


def extract_youtube_text(url: str) -> str:
    """Extract transcript / description from a YouTube URL."""
    if yt_dlp is not None:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "zh", "zh-Hans", "zh-Hant"],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "")
                description = info.get("description", "")
                parts = [f"Title: {title}", f"Description: {description}"]

                # Attempt to get transcript
                subtitles = info.get("subtitles", {})
                auto_subs = info.get("automatic_captions", {})
                for lang in ["en", "zh", "zh-Hans", "zh-Hant"]:
                    subs = subtitles.get(lang) or auto_subs.get(lang)
                    if subs:
                        # Prefer vtt/srt/json3 formats
                        sub_url = None
                        for fmt in subs:
                            if fmt.get("ext") in ("vtt", "srt", "json3"):
                                sub_url = fmt.get("url")
                                break
                        if sub_url:
                            r = requests.get(sub_url, timeout=30)
                            parts.append(f"Transcript ({lang}):\n{r.text[:8000]}")
                            break
                return "\n\n".join(parts)
        except Exception as exc:
            sys.stderr.write(f"Warning: yt-dlp extraction failed: {exc}\n")

    # Fallback: return URL and ask user for transcript if yt-dlp unavailable
    sys.stderr.write(
        "Warning: yt-dlp not available. Returning basic metadata only.\n"
        "Install yt-dlp for full transcript extraction: pip install yt-dlp\n"
    )
    return f"YouTube URL: {url}\n(Install yt-dlp for transcript extraction)"


def read_local_file(path: Path) -> str:
    """Read a local file (text or PDF)."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(path)

    # Treat everything else as text
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="gbk") as fh:
                return fh.read()
        except Exception as exc:
            sys.stderr.write(f"Error reading file: {exc}\n")
            sys.exit(1)


def build_prompt(text: str, length: str, extract_only: bool) -> str:
    """Build the summarization prompt."""
    if extract_only:
        return (
            "Extract the main content from the following text. "
            "Remove navigation, ads, and boilerplate. "
            "Preserve the original language.\n\n" + text
        )

    max_chars = LENGTH_MAP.get(length)
    if max_chars is None:
        # Try to parse as raw char count
        try:
            max_chars = int(length)
        except ValueError:
            max_chars = LENGTH_MAP["medium"]

    return (
        f"Summarize the following text concisely. "
        f"The summary should be approximately {max_chars} characters or less. "
        f"Preserve the original language.\n\n{text}"
    )


def call_gemini(api_key: str, prompt: str, max_tokens: int | None) -> str:
    """Call Google Gemini API."""
    if requests is None:
        raise RuntimeError("requests library required")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.0-flash:generateContent"
    )
    payload: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {},
    }
    if max_tokens:
        payload["generationConfig"]["maxOutputTokens"] = max_tokens

    resp = requests.post(
        url,
        params={"key": api_key},
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Gemini response format: {data}") from exc


def call_openai(api_key: str, model: str, prompt: str, max_tokens: int | None) -> str:
    """Call OpenAI-compatible API."""
    if requests is None:
        raise RuntimeError("requests library required")

    model_name = model.split("/", 1)[1] if "/" in model else model
    url = "https://api.openai.com/v1/chat/completions"
    payload: dict[str, Any] = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected OpenAI response format: {data}") from exc


def call_anthropic(api_key: str, model: str, prompt: str, max_tokens: int | None) -> str:
    """Call Anthropic Claude API."""
    if requests is None:
        raise RuntimeError("requests library required")

    model_name = model.split("/", 1)[1] if "/" in model else model
    url = "https://api.anthropic.com/v1/messages"
    payload: dict[str, Any] = {
        "model": model_name,
        "max_tokens": max_tokens or 1024,
        "messages": [{"role": "user", "content": prompt}],
    }

    resp = requests.post(
        url,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    try:
        return data["content"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Anthropic response format: {data}") from exc


def summarize_with_llm(
    text: str,
    model: str,
    length: str,
    max_tokens: int | None,
    extract_only: bool,
) -> str:
    """Route to the correct LLM backend and return summary."""
    api_key = resolve_api_key(model)
    if not api_key:
        provider = model.split("/")[0].lower()
        sys.stderr.write(
            f"Error: No API key found for provider '{provider}'.\n"
            f"Set one of the following environment variables:\n"
        )
        if provider in ("google", "gemini"):
            sys.stderr.write("  GEMINI_API_KEY, GOOGLE_GENERATIVE_AI_API_KEY, GOOGLE_API_KEY\n")
        elif provider == "openai":
            sys.stderr.write("  OPENAI_API_KEY\n")
        elif provider == "anthropic":
            sys.stderr.write("  ANTHROPIC_API_KEY\n")
        elif provider == "xai":
            sys.stderr.write("  XAI_API_KEY\n")
        sys.exit(1)

    prompt = build_prompt(text, length, extract_only)
    provider = model.split("/")[0].lower()

    try:
        if provider in ("google", "gemini"):
            return call_gemini(api_key, prompt, max_tokens)
        elif provider == "openai":
            return call_openai(api_key, model, prompt, max_tokens)
        elif provider == "anthropic":
            return call_anthropic(api_key, model, prompt, max_tokens)
        else:
            # Default to OpenAI-compatible for unknown providers
            return call_openai(api_key, model, prompt, max_tokens)
    except requests.HTTPError as exc:
        sys.stderr.write(f"API error: {exc}\n")
        if exc.response is not None:
            sys.stderr.write(f"Response: {exc.response.text}\n")
        sys.exit(1)
    except Exception as exc:
        sys.stderr.write(f"Error calling LLM API: {exc}\n")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize URLs or files with LLM (Windows-native).",
        usage='summarize "URL_OR_PATH" [options]',
    )
    parser.add_argument("input", help="URL or local file path to summarize")
    parser.add_argument(
        "--model",
        default=None,
        help='LLM model, e.g., google/gemini-3-flash-preview (default)',
    )
    parser.add_argument(
        "--length",
        default="medium",
        help="Summary length: short, medium, long, xl, xxl, or raw char count",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=None,
        dest="max_output_tokens",
        help="Maximum output tokens",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Extract main content without summarizing (URLs only)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output result as JSON",
    )
    parser.add_argument(
        "--firecrawl",
        default="off",
        help="Firecrawl fallback (ignored in this implementation)",
    )
    parser.add_argument(
        "--youtube",
        default=None,
        help="YouTube extraction mode (auto uses yt-dlp if available)",
    )
    parser.add_argument(
        "--print-content",
        action="store_true",
        dest="print_content",
        help="Extract and print content only, skip LLM summarization",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write extracted content or summary to file",
    )

    args = parser.parse_args()

    model = resolve_model(args.model)
    raw_input = args.input.strip('"').strip("'")

    # Determine input type
    parsed = urlparse(raw_input)
    is_url = bool(parsed.scheme) and bool(parsed.netloc)

    if is_url:
        if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
            text = extract_youtube_text(raw_input)
        else:
            text = fetch_url(raw_input)
    else:
        path = Path(raw_input)
        if not path.exists():
            sys.stderr.write(f"Error: File not found: {path}\n")
            sys.exit(1)
        text = read_local_file(path)

    # Truncate very long inputs to avoid token limits
    if len(text) > 60000:
        text = text[:60000] + "\n\n[Content truncated due to length]"

    # Determine if we should skip LLM and just print content
    api_key = resolve_api_key(model)
    if args.print_content or (not api_key and not args.extract_only):
        if not api_key and not args.print_content:
            sys.stderr.write(
                "\n[Info] No API key found. Switching to --print-content mode.\n"
                "Content extracted below. Copy and ask your AI assistant (Kimi) to summarize.\n\n"
            )
        result = text
    elif args.extract_only:
        result = text
    else:
        result = summarize_with_llm(
            text=text,
            model=model,
            length=args.length,
            max_tokens=args.max_output_tokens,
            extract_only=args.extract_only,
        )

    # Output
    if args.json_output:
        output = json.dumps(
            {
                "summary" if not args.print_content else "content": result,
                "model": model,
                "length": args.length,
                "input": raw_input,
            },
            ensure_ascii=False,
            indent=2,
        )
        payload = output
    else:
        payload = result

    if args.output:
        out_path = Path(args.output)
        try:
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(payload)
            sys.stderr.write(f"Output written to: {out_path.resolve()}\n")
        except OSError as exc:
            sys.stderr.write(f"Error writing to {out_path}: {exc}\n")
            sys.exit(1)
    else:
        print(payload)


if __name__ == "__main__":
    main()
