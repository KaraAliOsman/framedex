"""Repository-root entry point for the local outcome evaluation module."""

from pathlib import Path
import runpy
import sys

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root / "backend"), str(root / "engine" / "src")]
runpy.run_module("ai_gateway.evals.run", run_name="__main__")
