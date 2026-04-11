"""
Тесты веб-поиска SmartCRM.
Запуск: cd backend && python tests/test_search.py
"""
from __future__ import annotations
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_root, ".env"))

GREEN = "\033[92m"
RED   = "\033[91m"
BOLD  = "\033[1m"
RESET = "\033[0m"

def ok(msg):   print(f"  {GREEN}[PASS]{RESET}  {msg}")
def fail(msg): print(f"  {RED}[FAIL]{RESET}  {msg}")


TEST_CASES = [
    {
        "id": "S1",
        "name": "Базовый поиск — Сбербанк (analyst)",
        "company": "Сбербанк",
        "agent": "analyst",
        "industry": "финансы",
        "checks": [
            ("raw_results не пустые",        lambda r: len(r.get("raw_results", [])) > 0),
            ("formatted_block не пустой",    lambda r: len(r.get("formatted_block", "")) > 50),
            ("providers_used заполнены",     lambda r: len(r.get("providers_used", [])) > 0),
            ("cached=False (первый запуск)", lambda r: r.get("cached") is False),
            ("результатов ≥ 3",              lambda r: len(r.get("raw_results", [])) >= 3),
        ],
    },
    {
        "id": "S2",
        "name": "Кэш — повторный запрос возвращает из кэша",
        "company": "Сбербанк",
        "agent": "analyst",
        "industry": "финансы",
        "checks": [
            ("cached=True (из кэша)",   lambda r: r.get("cached") is True),
            ("результаты не пустые",    lambda r: len(r.get("raw_results", [])) > 0),
        ],
    },
    {
        "id": "S3",
        "name": "Поиск для маркетолога — другие запросы",
        "company": "Яндекс",
        "agent": "marketer",
        "industry": "IT",
        "checks": [
            ("raw_results не пустые",     lambda r: len(r.get("raw_results", [])) > 0),
            ("formatted_block есть",      lambda r: bool(r.get("formatted_block"))),
            ("нет дублей по домену",      lambda r: _check_no_domain_dupes(r.get("raw_results", []))),
        ],
    },
    {
        "id": "S4",
        "name": "Дедупликация — нет дублей в результатах",
        "company": "Газпром",
        "agent": "economist",
        "industry": "энергетика",
        "checks": [
            ("результаты есть",             lambda r: len(r.get("raw_results", [])) > 0),
            ("нет дублей сниппетов",        lambda r: _check_no_snippet_dupes(r.get("raw_results", []))),
            ("нет дублей доменов (≤2)",     lambda r: _check_no_domain_dupes(r.get("raw_results", []))),
        ],
    },
    {
        "id": "S5",
        "name": "Конфиг — загрузка и структура",
        "company": "",
        "agent": "",
        "industry": "",
        "checks": [
            ("providers в конфиге",         lambda r: "providers" in r),
            ("serper/brave/tavily есть",    lambda r: all(p in r.get("providers", {}) for p in ["serper","brave","tavily"])),
            ("query_templates есть",        lambda r: "query_templates" in r),
            ("analyst шаблоны есть",        lambda r: bool(r.get("query_templates", {}).get("analyst"))),
            ("reranking в конфиге",         lambda r: "reranking" in r),
            ("cache_ttl_hours есть",        lambda r: "cache_ttl_hours" in r),
        ],
    },
]


def _check_no_domain_dupes(results: list) -> bool:
    from urllib.parse import urlparse
    domain_counts: dict = {}
    for r in results:
        url = r.get("url", "")
        if not url:
            continue
        try:
            domain = urlparse(url).netloc.lower().replace("www.", "")
        except Exception:
            continue
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        if domain_counts[domain] > 2:
            return False
    return True


def _check_no_snippet_dupes(results: list) -> bool:
    seen = set()
    for r in results:
        key = r.get("snippet", "")[:80].lower().strip()
        if not key:
            continue
        if key in seen:
            return False
        seen.add(key)
    return True


async def run_test(tc: dict) -> dict:
    from rag.search import search_company, load_config, cache_clear

    # Тест конфига
    if tc["id"] == "S5":
        cfg = load_config()
        passed, failed = [], []
        for name, fn in tc["checks"]:
            try:
                if fn(cfg):
                    passed.append(name)
                else:
                    failed.append(name)
            except Exception:
                failed.append(name)
        return {"id": tc["id"], "name": tc["name"], "passed": passed, "failed": failed,
                "score": len(passed), "total": len(tc["checks"]), "result": cfg}

    # Для S1 — сбрасываем кэш
    if tc["id"] == "S1":
        cache_clear()

    t0 = time.monotonic()
    try:
        result = await search_company(
            company=tc["company"],
            agent=tc["agent"],
            industry=tc["industry"],
        )
    except Exception as e:
        result = {"_error": str(e), "raw_results": [], "formatted_block": "",
                  "providers_used": [], "cached": False}
    elapsed = round((time.monotonic() - t0) * 1000)

    passed, failed = [], []
    for name, fn in tc["checks"]:
        try:
            if fn(result):
                passed.append(name)
            else:
                failed.append(name)
        except Exception:
            failed.append(name)

    return {
        "id": tc["id"], "name": tc["name"],
        "elapsed_ms": elapsed,
        "passed": passed, "failed": failed,
        "score": len(passed), "total": len(tc["checks"]),
        "result": result,
    }


async def main():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  SmartCRM — Тесты веб-поиска{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    all_results = []

    for i, tc in enumerate(TEST_CASES):
        if i > 0:
            await asyncio.sleep(3)
        print(f"{BOLD}[{tc['id']}] {tc['name']}{RESET}")

        r = await run_test(tc)
        all_results.append(r)

        for c in r["passed"]:
            ok(c)
        for c in r["failed"]:
            fail(c)

        status = f"{GREEN}PASSED{RESET}" if not r["failed"] else f"{RED}FAILED{RESET}"
        elapsed_str = f" | {r['elapsed_ms']} мс" if r.get("elapsed_ms") else ""
        print(f"  → {r['score']}/{r['total']} проверок{elapsed_str} | {status}")

        if r.get("result", {}).get("_error"):
            print(f"  {RED}ERROR: {r['result']['_error']}{RESET}")

        res = r.get("result", {})
        if res.get("providers_used"):
            print(f"  Провайдеры: {res['providers_used']}")
        if res.get("raw_results") and tc["id"] not in ("S5",):
            n = len(res["raw_results"])
            first = res["raw_results"][0] if n else {}
            print(f"  Результатов: {n} | Первый: {first.get('title','')[:60]}")
        print()

    # Итог
    total_checks = sum(r["total"] for r in all_results)
    total_passed = sum(r["score"] for r in all_results)
    tests_ok     = sum(1 for r in all_results if not r["failed"])

    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  ИТОГ{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"  Тестов:   {tests_ok}/{len(all_results)} прошли полностью")
    print(f"  Проверок: {total_passed}/{total_checks} ({round(total_passed/total_checks*100)}%)")
    print()
    for r in all_results:
        status = f"{GREEN}OK{RESET}" if not r["failed"] else f"{RED}FAIL{RESET}"
        print(f"  [{r['id']}] {r['name'][:48]:<48} {r['score']}/{r['total']} {status}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
