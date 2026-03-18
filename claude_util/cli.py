"""
CLI entry point for the CTO Requirements Agent.

Usage:
    # Interactive mode (reads from stdin prompt)
    python -m claude_util.cli

    # Pipe requirements directly
    echo "Build an AI-powered IoT platform" | python -m claude_util.cli

    # Pass via argument
    python -m claude_util.cli --req "Build an AI-powered IoT platform"

    # Use a specific model
    python -m claude_util.cli --model "google/gemini-2.0-flash-exp:free"

    # List available free models
    python -m claude_util.cli --list-models

Environment:
    OPENROUTER_API_KEY  — required (free key at https://openrouter.ai/keys)
    OPENROUTER_MODEL    — optional model override
"""

from __future__ import annotations

import argparse
import sys
import textwrap

from .cto_agent import create_agent, FREE_MODELS, DEFAULT_MODEL


BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║          CTO Requirements Agent  |  SAFe Agile Edition          ║
║          Powered by OpenRouter Free Models                       ║
╚══════════════════════════════════════════════════════════════════╝
"""

SEPARATOR = "─" * 68


def print_banner() -> None:
    print(BANNER)


def print_separator() -> None:
    print(f"\n{SEPARATOR}\n")


def get_requirements(args: argparse.Namespace) -> str:
    """Resolve requirements from CLI arg, stdin pipe, or interactive prompt."""
    if args.req:
        return args.req

    if not sys.stdin.isatty():
        # Piped input
        data = sys.stdin.read().strip()
        if data:
            return data

    # Interactive
    print("Enter your requirements below.")
    print("(Type your text, then press Enter twice or Ctrl+D when done)\n")
    lines: list[str] = []
    try:
        while True:
            line = input()
            lines.append(line)
            if len(lines) >= 2 and lines[-1] == "" and lines[-2] == "":
                break
    except EOFError:
        pass

    return "\n".join(lines).strip()


def run() -> None:
    parser = argparse.ArgumentParser(
        description="CTO Requirements Agent — SAFe Agile breakdown from vague requirements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              python -m claude_util.cli --req "We need an app to manage deliveries"
              python -m claude_util.cli --model "google/gemini-2.0-flash-exp:free"
              python -m claude_util.cli --list-models
              echo "Build a payment system" | python -m claude_util.cli
            """
        ),
    )
    parser.add_argument(
        "--req", "-r",
        type=str,
        default=None,
        help="Requirements string (skip interactive prompt)",
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help=f"OpenRouter model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--api-key", "-k",
        type=str,
        default=None,
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output (wait for full response)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available free models and exit",
    )

    args = parser.parse_args()

    if args.list_models:
        print("\nAvailable free models on OpenRouter:\n")
        for i, m in enumerate(FREE_MODELS, 1):
            marker = " ← default" if m == DEFAULT_MODEL else ""
            print(f"  {i}. {m}{marker}")
        print(
            "\nSet with: --model <id>  or  OPENROUTER_MODEL=<id>\n"
            "More models at: https://openrouter.ai/models?q=free\n"
        )
        return

    print_banner()

    try:
        agent = create_agent(api_key=args.api_key, model=args.model)
    except EnvironmentError as e:
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)

    requirements = get_requirements(args)
    if not requirements:
        print("[ERROR] No requirements provided. Exiting.")
        sys.exit(1)

    print_separator()
    print(f"MODEL : {agent.config.model}")
    print(f"INPUT : {requirements[:120]}{'...' if len(requirements) > 120 else ''}")
    print_separator()

    if args.no_stream:
        try:
            result = agent.analyze(requirements)
        except Exception as e:
            print(f"\n[ERROR] Agent call failed: {e}\n")
            sys.exit(1)

        for w in result.warnings:
            print(f"[WARN] {w}")

        print(f"\n{'═' * 68}")
        print(f"  MODE: {result.mode.upper()}")
        print(f"{'═' * 68}\n")
        print(result.content)
        print(f"\n{SEPARATOR}")
        if result.tokens_used:
            print(f"Tokens used: {result.tokens_used}")
    else:
        # Streaming mode
        try:
            for chunk in agent.analyze_stream(requirements):
                print(chunk, end="", flush=True)
        except KeyboardInterrupt:
            print("\n\n[Interrupted by user]")
        except Exception as e:
            print(f"\n[ERROR] Streaming failed: {e}\n")
            sys.exit(1)
        print(f"\n\n{SEPARATOR}\n")


if __name__ == "__main__":
    run()
