"""
python -m claude_util         → start web UI (default)
python -m claude_util --cli   → start CLI agent
python -m claude_util --web   → start web UI explicitly
"""
import sys

args = sys.argv[1:]

if "--cli" in args:
    from claude_util.cli import run
    run()
else:
    from claude_util.web.app import serve
    serve()
