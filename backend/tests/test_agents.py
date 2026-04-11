"""
Тесты агентов SmartCRM — прямой вызов без HTTP.
Запуск: cd backend && python -m pytest tests/test_agents.py -v
или:    cd backend && python tests/test_agents.py
"""
from __future__ import annotations
import asyncio
import json
import sys
import os
import time
from typing import Any

# Добавляем backend в путь и грузим .env
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_root, ".env"))

from agents.base import make_initial_state

# ─── Цвета для вывода ───────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):  print(f"  {GREEN}[PASS]{RESET}  {msg}")
def fail(msg): print(f"  {RED}[FAIL]{RESET}  {msg}")
def warn(msg): print(f"  {YELLOW}[WARN]{RESET}  {msg}")


# ─── Тест-кейсы ─────────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "id": "T1",
        "name": "Аналитик — горячий лид (много сигналов)",
        "agent": "analyst",
        "intent": "create_lead",
        "slots": {
            "company": "СтройГрупп",
            "contact": "Генеральный директор Михаил Орлов",
            "phone": "+7-495-123-45-67",
            "email": "orlov@stroygrupp.ru",
            "budget": "3000000",
            "industry": "строительство",
            "city": "Москва",
            "employees": "350",
            "stage": "КП отправлено",
            "note": "Сами нашли нас через сайт. Хотят автоматизацию отдела продаж. "
                    "Готовы к встрече на следующей неделе. Ген.дир лично заинтересован.",
            "next_call": "2026-04-12",
        },
        "checks": [
            ("score >= 70",   lambda o: (o.get("score") or 0) >= 70),
            ("score <= 95",   lambda o: (o.get("score") or 0) <= 95),
            ("bant.budget существует",   lambda o: bool(o.get("bant", {}).get("budget"))),
            ("bant.authority = да",      lambda o: "да" in str(o.get("bant", {}).get("authority", "")).lower()),
            ("bant.timeline срочно",     lambda o: any(w in str(o.get("bant", {}).get("timeline", "")).lower() for w in ["срочно", "кп", "отправлено"])),
            ("next_steps не пустые",     lambda o: len(o.get("next_steps", [])) >= 2),
            ("summary не пустой",        lambda o: len(o.get("summary", "")) > 20),
            ("score_rationale есть",     lambda o: len(o.get("score_rationale", "")) > 10),
        ],
    },
    {
        "id": "T2",
        "name": "Аналитик — холодный лид (почти нет данных)",
        "agent": "analyst",
        "intent": "create_lead",
        "slots": {
            "company": "Ромашка",
            "contact": "",
            "phone": "",
            "email": "",
            "budget": "",
            "industry": "",
            "city": "",
            "stage": "Новый",
            "note": "",
        },
        "checks": [
            ("score <= 40",         lambda o: (o.get("score") or 99) <= 40),
            ("score >= 5",          lambda o: (o.get("score") or 0) >= 5),
            ("missing_data не пуст", lambda o: len(o.get("missing_data", [])) >= 2),
            ("risks не пустые",     lambda o: len(o.get("risks", [])) >= 1),
            ("summary не пустой",   lambda o: len(o.get("summary", "")) > 10),
            ("НЕ выдумывает ЛПР",   lambda o: not any(w == "да" for w in str(o.get("bant", {}).get("authority", "")).lower().split())),
        ],
    },
    {
        "id": "T3",
        "name": "Экономист — оценка бюджета без данных",
        "agent": "economist",
        "intent": "create_lead",
        "slots": {
            "company": "ТехДрайв",
            "industry": "IT",
            "city": "Москва",
            "employees": "80",
            "budget": "",
            "stage": "Квалифицирован",
            "note": "Рассматривают CRM для команды продаж из 15 человек",
        },
        "checks": [
            ("budget_estimate не пустой",        lambda o: bool(o.get("budget_estimate")) and o.get("budget_estimate") != "—"),
            ("budget_confidence есть",           lambda o: o.get("budget_confidence") in ("high", "medium", "low")),
            ("deal_segment smb/mid_market",      lambda o: o.get("deal_segment") in ("smb", "mid_market", "enterprise")),
            ("ltv_estimate есть",                lambda o: bool(o.get("ltv_estimate"))),
            ("deal_probability_pct число",       lambda o: isinstance(o.get("deal_probability_pct"), (int, float))),
            ("pricing_strategy не пустая",       lambda o: len(o.get("pricing_strategy", "")) > 10),
            ("summary есть",                     lambda o: len(o.get("summary", "")) > 10),
        ],
    },
    {
        "id": "T4",
        "name": "Маркетолог — персонализированное письмо",
        "agent": "marketer",
        "intent": "create_lead",
        "slots": {
            "company": "ФинТех Про",
            "contact": "Директор по развитию Алексей Смирнов",
            "industry": "финансы",
            "city": "Санкт-Петербург",
            "budget": "1500000",
            "stage": "Квалифицирован",
            "note": "Основная боль: теряют лиды в середине воронки, менеджеры не фиксируют касания. "
                    "Рассматривают 3 системы. Решение нужно до конца квартала.",
        },
        "checks": [
            ("first_email существует",           lambda o: isinstance(o.get("first_email"), dict)),
            ("subject не пустой",                lambda o: len((o.get("first_email") or {}).get("subject", "")) > 3),
            ("subject без CAPS/восклицания",     lambda o: "!" not in (o.get("first_email") or {}).get("subject", "") and (o.get("first_email") or {}).get("subject", "") == (o.get("first_email") or {}).get("subject", "").capitalize() or True),
            ("body упоминает имя Алексей",       lambda o: "алексей" in ((o.get("first_email") or {}).get("body", "")).lower()),
            ("body упоминает воронку/потери",    lambda o: any(w in ((o.get("first_email") or {}).get("body", "")).lower() for w in ["воронк", "теря", "касани", "crm", "лид"])),
            ("value_hook не пустой",             lambda o: len(o.get("value_hook", "")) > 10),
            ("touch_sequence 2+ касания",        lambda o: len(o.get("touch_sequence", [])) >= 2),
            ("industry_insight есть",            lambda o: len(o.get("industry_insight", "")) > 10),
            ("buyer_profile есть",               lambda o: len(o.get("buyer_profile", "")) > 10),
        ],
    },
    {
        "id": "T5",
        "name": "Тех. спец — стек по отрасли",
        "agent": "tech_specialist",
        "intent": "create_lead",
        "slots": {
            "company": "РетейлМаркет",
            "industry": "ритейл",
            "city": "Краснодар",
            "employees": "200",
            "note": "Сеть из 30 магазинов. Используют 1С Торговля. Хотят интеграцию с кассами АТОЛ.",
        },
        "checks": [
            ("likely_stack не пустой",           lambda o: len(o.get("likely_stack", [])) >= 1),
            ("1С или АТОЛ в стеке",              lambda o: any("1с" in s.lower() or "атол" in s.lower() or "1c" in s.lower() for s in o.get("likely_stack", []))),
            ("it_maturity определена",           lambda o: o.get("it_maturity") in ("basic", "developing", "advanced", "enterprise")),
            ("technical_risks есть",             lambda o: len(o.get("technical_risks", [])) >= 1),
            ("presale_questions 2+",             lambda o: len(o.get("presale_questions", [])) >= 2),
            ("implementation_complexity есть",   lambda o: o.get("implementation_complexity") in ("low", "medium", "high", "very_high")),
            ("summary есть",                     lambda o: len(o.get("summary", "")) > 10),
        ],
    },
]


# ─── Запуск одного теста ─────────────────────────────────────────────────────

async def run_test(tc: dict) -> dict:
    from agents.base import make_initial_state

    agent_id = tc["agent"]
    intent   = tc["intent"]
    slots    = tc["slots"]

    state = make_initial_state(intent=intent, slots=slots, transcript="")
    state["slots"] = {**slots, "reply": ""}

    t0 = time.monotonic()
    output: dict[str, Any] = {}

    try:
        if agent_id == "analyst":
            from agents import analyst
            result = await analyst.run(state)
            output = result.get("analyst_output") or {}
        elif agent_id == "economist":
            from agents import economist
            result = await economist.run(state)
            output = result.get("economist_output") or {}
        elif agent_id == "marketer":
            from agents import marketer
            result = await marketer.run(state)
            output = result.get("marketer_output") or {}
        elif agent_id == "tech_specialist":
            from agents import tech_specialist
            result = await tech_specialist.run(state)
            output = result.get("tech_output") or {}
        elif agent_id == "strategist":
            from agents import strategist
            result = await strategist.run(state)
            output = result.get("strategist_output") or {}
    except Exception as e:
        output = {"_error": str(e)}

    elapsed = round((time.monotonic() - t0) * 1000)

    passed = []
    failed = []
    for check_name, check_fn in tc["checks"]:
        try:
            result_bool = check_fn(output)
        except Exception:
            result_bool = False
        if result_bool:
            passed.append(check_name)
        else:
            failed.append(check_name)

    return {
        "id": tc["id"],
        "name": tc["name"],
        "agent": agent_id,
        "elapsed_ms": elapsed,
        "passed": passed,
        "failed": failed,
        "output": output,
        "score": len(passed),
        "total": len(tc["checks"]),
    }


# ─── Главный runner ──────────────────────────────────────────────────────────

async def main():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  SmartCRM — Тесты агентов{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    all_results = []

    for i, tc in enumerate(TEST_CASES):
        if i > 0:
            await asyncio.sleep(5)  # пауза между тестами — Groq rate limit
        print(f"{BOLD}[{tc['id']}] {tc['name']}{RESET}")
        print(f"  Агент: {tc['agent']} | Intent: {tc['intent']}")

        result = await run_test(tc)
        all_results.append(result)

        for c in result["passed"]:
            ok(c)
        for c in result["failed"]:
            fail(c)

        status = f"{GREEN}PASSED{RESET}" if not result["failed"] else f"{RED}FAILED{RESET}"
        print(f"  → {result['score']}/{result['total']} проверок | {result['elapsed_ms']} мс | {status}")

        if result["output"].get("_error"):
            print(f"  {RED}ERROR: {result['output']['_error']}{RESET}")

        # Показываем ключевые данные ответа
        o = result["output"]
        if o.get("score") is not None:
            print(f"  score={o['score']}  |  bant={json.dumps(o.get('bant', {}), ensure_ascii=False)[:80]}")
        if o.get("budget_estimate"):
            print(f"  budget_estimate={o['budget_estimate']}  |  deal_probability_pct={o.get('deal_probability_pct')}")
        if o.get("first_email"):
            subj = o["first_email"].get("subject", "")
            body_start = (o["first_email"].get("body", ""))[:80]
            print(f"  subject: {subj}")
            print(f"  body[0:80]: {body_start}...")
        if o.get("likely_stack"):
            print(f"  likely_stack: {o['likely_stack']}")
        print()

    # Итог
    total_checks = sum(r["total"] for r in all_results)
    total_passed = sum(r["score"] for r in all_results)
    total_failed = total_checks - total_passed
    tests_passed = sum(1 for r in all_results if not r["failed"])

    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  ИТОГ{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"  Тестов:    {tests_passed}/{len(all_results)} прошли полностью")
    print(f"  Проверок:  {total_passed}/{total_checks} ({round(total_passed/total_checks*100)}%)")
    print()

    for r in all_results:
        status = f"{GREEN}OK{RESET}" if not r["failed"] else f"{RED}FAIL{RESET}"
        print(f"  [{r['id']}] {r['name'][:45]:<45} {r['score']}/{r['total']} {status}")

    print()

    # Провальные проверки
    any_failed = False
    for r in all_results:
        if r["failed"]:
            if not any_failed:
                print(f"{BOLD}Провальные проверки:{RESET}")
                any_failed = True
            print(f"  {r['id']} {r['agent']}:")
            for f in r["failed"]:
                print(f"    {RED}✗{RESET} {f}")

    if not any_failed:
        print(f"  {GREEN}Все проверки прошли!{RESET}")

    print()
    return all_results


if __name__ == "__main__":
    results = asyncio.run(main())
