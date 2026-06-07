"""
HermesLab — Dr. QA CLI.

Одна точка входа для всех экспериментов с Hermes NLU.

Commands:
  chat                    — интерактивный чат с Dr. QA
  run  "name" [--prompt]  — автоматический пайплайн: AA → AB → gate → canary
  status [--status X]     — таблица гипотез
  add  "name"             — добавить гипотезу в реестр
  rollback <id>           — откатить canary
  canary <id> <pct>       — выкатить на N% (с TTL)
  stats                   — текущие baseline KPI

Usage (из backend/):
  python scripts/hermeslab.py chat
  python scripts/hermeslab.py run "новый компактный промпт"
  python scripts/hermeslab.py run "промпт с chain-of-thought" --prompt "Ты JSON-роутер..."
  python scripts/hermeslab.py status
  python scripts/hermeslab.py status --status canary
  python scripts/hermeslab.py add "тест без few-shot примеров"
  python scripts/hermeslab.py rollback 3
  python scripts/hermeslab.py canary 4 5 --ttl 24
  python scripts/hermeslab.py stats
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("PYTHONPATH", str(ROOT))

# Load .env if present (same logic as backend entrypoint)
_env_path = ROOT.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

from core.qa_agent import QAAgent, HypothesisRegistry, get_current_kpis  # noqa: E402


# ─── formatting helpers ───────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
GRAY   = "\033[90m"


def _status_color(s: str) -> str:
    colors = {
        "draft":    GRAY,
        "running":  YELLOW,
        "canary":   CYAN,
        "accepted": GREEN,
        "rejected": RED,
        "killed":   RED,
    }
    return colors.get(s, RESET) + s + RESET


def _fmt_ts(ts: float | None) -> str:
    if not ts:
        return "—"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def _print_hypothesis_table(hypotheses: list) -> None:
    if not hypotheses:
        print(f"{GRAY}Гипотез нет.{RESET}")
        return

    header = f"{'ID':>4}  {'METHOD':>9}  {'STATUS':>10}  {'CREATED':>16}  NAME"
    print(f"\n{BOLD}{header}{RESET}")
    print("─" * 70)
    for h in hypotheses:
        canary_suffix = f" [{h.canary_pct}%]" if h.canary_pct else ""
        print(
            f"{h.id:>4}  {h.method:>9}  "
            f"{_status_color(h.status):>10}{canary_suffix}  "
            f"{_fmt_ts(h.created_at):>16}  {h.name}"
        )
    print()


def _print_pipeline_result(result: dict) -> None:
    decision = result.get("decision", "?")
    color = {
        "ACCEPT": GREEN, "REJECT": RED, "INSUFFICIENT DATA": YELLOW,
        "ABORT": RED, "ERROR": RED,
    }.get(decision, RESET)

    print(f"\n{'═'*60}")
    print(f"{BOLD}HYPOTHESIS #{result.get('hypothesis_id')}: {result.get('name')}{RESET}")
    print(f"{'═'*60}")

    steps = result.get("steps", {})

    if "aa" in steps:
        aa = steps["aa"]
        aa_ok = aa.get("stable", False)
        aa_icon = "✓" if aa_ok else "✗"
        print(f"\n[{aa_icon}] A/A  drift={aa.get('drift_pp')}pp  → {aa.get('verdict', '')}")

    if "ab" in steps:
        ab = steps["ab"]
        deltas = ab.get("deltas", {})
        stats  = ab.get("stats", {})
        n      = ab.get("n", 0)
        p      = stats.get("p_value", "?")
        print(f"\n[~] A/B  n={n}")
        print(f"     accuracy Δ = {deltas.get('accuracy_pp', 0):+.2f}pp")
        print(f"     latency Δ  = {deltas.get('latency_pct', 0):+.1f}%")
        print(f"     error   Δ  = {deltas.get('error_rate_pp', 0):+.2f}pp")
        print(f"     p-value    = {p}  {'✓ significant' if stats.get('significant') else '✗ not significant'}")

    if "gate" in steps:
        gate = steps["gate"]
        decisions = gate.get("decisions", [])
        passed = sum(1 for d in decisions if d.get("accept"))
        print(f"\n[~] KPI gate  {passed}/{len(decisions)} features passed")

    if "canary" in steps:
        c = steps["canary"]
        print(f"\n[→] Canary  {c['pct']}% traffic  TTL={c['ttl_hours']}h")

    print(f"\n{'─'*60}")
    print(f"{BOLD}{color}DECISION: {decision}{RESET}")
    print(f"Reason: {result.get('reason', '—')}")
    print(f"{'═'*60}\n")


# ─── commands ─────────────────────────────────────────────────────────────────

async def cmd_chat() -> None:
    agent = QAAgent()
    print(f"\n{BOLD}{CYAN}Dr. QA — Experimentation Engineer{RESET}")
    print(f"{GRAY}Введи гипотезу, вопрос или задачу. 'exit' для выхода.{RESET}\n")

    while True:
        try:
            user_input = input(f"{BOLD}You:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if user_input.lower() in ("exit", "quit", "q"):
            break
        if not user_input:
            continue

        print(f"\n{BOLD}{CYAN}Dr. QA:{RESET} ", end="", flush=True)
        try:
            response = await agent.chat(user_input)
            print(response)
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
        print()


async def cmd_run(args: argparse.Namespace) -> None:
    agent = QAAgent()
    print(f"\n{BOLD}[Dr.QA]{RESET} Запускаю пайплайн: {CYAN}{args.name}{RESET}")
    print(f"{GRAY}AA={'skip' if args.skip_aa else 'yes'}  canary={args.canary_pct}%  TTL={args.ttl}h{RESET}\n")

    result = await agent.run_pipeline(
        hypothesis_name=args.name,
        variant_prompt=args.prompt or "",
        skip_aa=args.skip_aa,
        canary_pct=args.canary_pct,
        canary_ttl_hours=args.ttl,
    )

    _print_pipeline_result(result)

    # Save full result
    out = ROOT / "data" / f"hermeslab_run_{result['hypothesis_id']}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{GRAY}Full result saved: {out.name}{RESET}\n")


def cmd_status(args: argparse.Namespace) -> None:
    reg = HypothesisRegistry()
    hs = reg.list(status=args.status if args.status != "all" else None)
    _print_hypothesis_table(hs)

    # Check expired canaries
    expired = reg.check_expired_canaries()
    if expired:
        print(f"{YELLOW}⚠ Просроченные canary (TTL истёк): {expired}{RESET}")
        print(f"{GRAY}  Запусти: python scripts/hermeslab.py rollback <id>{RESET}\n")


def cmd_add(args: argparse.Namespace) -> None:
    reg = HypothesisRegistry()
    h = reg.add(name=args.name, description=args.desc or "", method=args.method)
    print(f"\n{GREEN}✓ Гипотеза #{h.id} добавлена: {h.name}{RESET}")
    print(f"  method={h.method}  status={h.status}\n")


def cmd_rollback(args: argparse.Namespace) -> None:
    reg = HypothesisRegistry()
    h = reg.get(args.id)
    if not h:
        print(f"{RED}Гипотеза #{args.id} не найдена.{RESET}")
        return
    reg.rollback(args.id)
    print(f"\n{GREEN}✓ Rollback выполнен: #{args.id} {h.name}{RESET}")
    print(f"  canary_pct=0  status=killed\n")


def cmd_canary(args: argparse.Namespace) -> None:
    reg = HypothesisRegistry()
    h = reg.get(args.id)
    if not h:
        print(f"{RED}Гипотеза #{args.id} не найдена.{RESET}")
        return
    reg.set_canary(args.id, args.pct, args.ttl)
    print(f"\n{CYAN}✓ Canary set: #{args.id} {h.name}{RESET}")
    print(f"  traffic={args.pct}%  TTL={args.ttl}h\n")


def cmd_stats(_args: argparse.Namespace) -> None:
    kpis = get_current_kpis()
    if "error" in kpis:
        print(f"{RED}{kpis['error']}{RESET}")
        return
    print(f"\n{BOLD}Latest KPIs — {kpis.get('file')}{RESET}\n")
    data = kpis.get("data", {})
    decisions = data.get("decisions", [])
    if decisions:
        for d in decisions:
            icon = "✓" if d.get("accept") else "✗"
            stage = d.get("stage", "?")
            k = d.get("kpi", {})
            print(
                f"  [{icon}] {stage:<30}  "
                f"acc={k.get('accuracy_pct', '?')}%  "
                f"avg={k.get('avg_ms', '?')}ms  "
                f"err={k.get('error_rate_pct', '?')}%"
            )
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    print()


# ─── CLI entry ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hermeslab",
        description="Dr. QA — HermesLab Experimentation CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # chat
    sub.add_parser("chat", help="Интерактивный чат с Dr. QA")

    # run
    p_run = sub.add_parser("run", help="Автоматический пайплайн AA→AB→gate→canary")
    p_run.add_argument("name", help="Название гипотезы")
    p_run.add_argument("--prompt", default="", help="Системный промпт варианта (если пусто — тестирует compact-modular)")
    p_run.add_argument("--skip-aa", action="store_true", help="Пропустить A/A валидацию")
    p_run.add_argument("--canary-pct", type=int, default=5, help="% трафика для canary (default: 5)")
    p_run.add_argument("--ttl", type=int, default=24, help="TTL canary в часах (default: 24)")

    # status
    p_status = sub.add_parser("status", help="Таблица гипотез")
    p_status.add_argument("--status", default="all",
                          choices=["all", "draft", "running", "canary", "accepted", "rejected", "killed"])

    # add
    p_add = sub.add_parser("add", help="Добавить гипотезу")
    p_add.add_argument("name", help="Название")
    p_add.add_argument("--desc", default="", help="Описание")
    p_add.add_argument("--method", default="ab",
                       choices=["aa", "ab", "mvt", "bandit", "canary", "fake_door", "blue_green"])

    # rollback
    p_rb = sub.add_parser("rollback", help="Откатить canary")
    p_rb.add_argument("id", type=int, help="ID гипотезы")

    # canary
    p_can = sub.add_parser("canary", help="Выкатить на N% трафика")
    p_can.add_argument("id", type=int, help="ID гипотезы")
    p_can.add_argument("pct", type=int, help="% трафика")
    p_can.add_argument("--ttl", type=int, default=24, help="TTL в часах")

    # stats
    sub.add_parser("stats", help="Текущие baseline KPI")

    args = parser.parse_args()

    if args.command == "chat":
        asyncio.run(cmd_chat())
    elif args.command == "run":
        asyncio.run(cmd_run(args))
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "add":
        cmd_add(args)
    elif args.command == "rollback":
        cmd_rollback(args)
    elif args.command == "canary":
        cmd_canary(args)
    elif args.command == "stats":
        cmd_stats(args)


if __name__ == "__main__":
    main()
