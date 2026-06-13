"""
Quality gate всех 6 агентов через Ollama (hermes3).

  cd backend
  python scripts/run_agents_quality_gate.py --check-only
  python scripts/run_agents_quality_gate.py
  python scripts/run_agents_quality_gate.py --hermes-limit 5 --agent-limit 3

Требует: ollama serve + ollama pull hermes3:latest
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

# Force Ollama до импорта core.llm (кэш Groq-ключа).
os.environ.setdefault("HERMES_MODEL", "hermes3:latest")
os.environ.setdefault("EVAL_OLLAMA_TIMEOUT", "600")
os.environ.setdefault("OLLAMA_CHAT_TIMEOUT", "600")
os.environ["GROQ_API_KEY"] = ""
os.environ["OLLAMA_MODEL"] = os.environ["HERMES_MODEL"]

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv

    _backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(os.path.dirname(_backend), ".env"))
    load_dotenv(os.path.join(_backend, ".env"))
except ImportError:
    pass

from core.agent_eval.acceptance_sync import patch_acceptance_md  # noqa: E402
from core.agent_eval.gate import run_agents_quality_gate, save_gate_artifact  # noqa: E402
from core.agent_eval.ollama_check import check_ollama_ready  # noqa: E402

_LOG_FH = None


def _emit(msg: str, *, err: bool = False) -> None:
    stream = sys.stderr if err else sys.stdout
    enc = getattr(stream, "encoding", None) or "utf-8"
    safe = msg.encode(enc, errors="replace").decode(enc)
    print(safe, file=stream, flush=True)
    if _LOG_FH:
        _LOG_FH.write(msg + "\n")
        _LOG_FH.flush()


async def _main(args: argparse.Namespace) -> int:
    if args.check_only:
        info = await check_ollama_ready()
        _emit(json.dumps({"ok": True, **info}, ensure_ascii=False, indent=2))
        return 0

    _emit(f"Quality gate: Ollama {os.getenv('OLLAMA_HOST', 'http://localhost:11434')} / {os.environ['OLLAMA_MODEL']}")
    if os.getenv("SMARTCRM_API_KEY"):
        _emit("Backend auth: SMARTCRM_API_KEY loaded (agents -> /api/leads)")
    else:
        _emit("WARN: SMARTCRM_API_KEY missing — agents may get 401 if API requires key", err=True)
    if _LOG_FH:
        from core.agent_eval import gate as gate_module

        gate_module.set_gate_logger(lambda m: _emit(m))
    report = await run_agents_quality_gate(
        hermes_limit=args.hermes_limit,
        agent_limit=args.agent_limit,
        skip_agents=args.hermes_only,
        skip_hermes=args.agents_only,
    )
    path = save_gate_artifact(report)
    if args.write_acceptance:
        patch_acceptance_md(report, path.name)
        _emit("Acceptance updated: docs/operations/phase2/agents/AGENTS_QUALITY_GATE_ACCEPTANCE.md")
    _emit(json.dumps(report, ensure_ascii=True, indent=2))
    _emit(f"\nArtifact: {path}")
    _emit(f"Overall gate: {report['overall_gate']}")
    if report.get("gaps"):
        _emit("\n--- Gaps ---")
        for g in report["gaps"]:
            _emit(f"  - {g}")
    return 0 if report["overall_gate"] != "fail" else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="Agents quality gate (Ollama)")
    ap.add_argument("--check-only", action="store_true", help="Только проверка Ollama + модели")
    ap.add_argument("--hermes-limit", type=int, default=0, help="Лимит кейсов Hermes (0=все)")
    ap.add_argument("--agent-limit", type=int, default=0, help="Лимит кейсов на агента (0=все)")
    ap.add_argument("--hermes-only", action="store_true", help="Только Hermes, без 5 агентов")
    ap.add_argument("--agents-only", action="store_true", help="Только 5 агентов, без Hermes")
    ap.add_argument("--write-acceptance", action="store_true", help="Обновить acceptance-таблицу в docs")
    ap.add_argument(
        "--log-file",
        default="",
        help="Путь к лог-файлу (line-buffered), напр. data/artifacts/eval/gate_run.log",
    )
    args = ap.parse_args()
    global _LOG_FH
    if args.log_file:
        os.makedirs(os.path.dirname(args.log_file) or ".", exist_ok=True)
        _LOG_FH = open(args.log_file, "w", encoding="utf-8", buffering=1)
    try:
        raise SystemExit(asyncio.run(_main(args)))
    except RuntimeError as e:
        _emit(f"BLOCKED: {e}", err=True)
        _emit("Run: ollama serve && ollama pull hermes3:latest", err=True)
        raise SystemExit(2) from e
    finally:
        if _LOG_FH:
            _LOG_FH.close()
            _LOG_FH = None


if __name__ == "__main__":
    main()
