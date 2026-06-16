#!/usr/bin/env python3
"""Live UI smoke B: /email → Массовая (сегмент) через Playwright (аналог DevTools)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

BASE = os.getenv("SMOKE_FRONTEND_URL", "http://127.0.0.1:5173")
LLM_TIMEOUT_MS = int(os.getenv("SMOKE_LLM_TIMEOUT_MS", "120000"))


def run() -> int:
    from playwright.sync_api import sync_playwright

    steps: list[str] = []
    errors: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(f"{BASE}/email", wait_until="networkidle", timeout=60_000)
            steps.append("open /email")

            nav = page.locator('[data-testid="nav-campaign-mass"]')
            nav.wait_for(state="visible", timeout=20_000)
            nav.click()
            panel = page.locator('[data-testid="campaign-mass-panel"]')
            panel.wait_for(state="attached", timeout=20_000)
            panel.scroll_into_view_if_needed()
            steps.append("nav Массовая (сегмент)")

            page.locator('[data-testid="campaign-industry-box"]').wait_for(timeout=15_000)
            with_leads = page.locator('[data-testid="campaign-industry-with-leads"]')
            if with_leads.count():
                with_leads.click()
                steps.append("чекбоксы отраслей: «С лидами»")

            page.get_by_role("button", name="1. Сколько лидов в сегменте?").click()
            page.locator('[data-testid="campaign-segment-count"]').wait_for(timeout=30_000)
            count_text = page.locator('[data-testid="campaign-segment-count"]').inner_text()
            steps.append(f"счётчик сегмента: {count_text.strip()}")

            page.locator('[data-testid="campaign-preview-llm"]').click()
            page.locator('[data-testid="campaign-example-0"]').wait_for(timeout=LLM_TIMEOUT_MS)
            page.locator('[data-testid="campaign-example-1"]').wait_for(timeout=5_000)
            page.locator('[data-testid="campaign-example-2"]').wait_for(timeout=5_000)
            steps.append("3 примера LLM")

            account = page.locator('[data-testid="campaign-account"]')
            options = account.locator("option")
            if options.count() < 2:
                errors.append("нет email-аккаунта в select")
            else:
                account.select_option(index=1)
                steps.append("выбран email-аккаунт")

            if not errors:
                page.locator('[data-testid="campaign-test-ib"]').click()
                page.wait_for_timeout(3_000)
                body = page.locator("body").inner_text()
                if "Тест на" in body or "ib@" in body.lower():
                    steps.append("test ib@ — OK")
                elif page.locator(".text-red-400, [class*='text-red']").count():
                    err = page.locator(".text-red-400").first.inner_text()
                    errors.append(f"test ib@ error UI: {err[:120]}")
                else:
                    steps.append("test ib@ — clicked (ответ без явного success)")

        except Exception as exc:
            errors.append(str(exc)[:200])
        finally:
            browser.close()

    print("SMOKE B UI steps:")
    for s in steps:
        print(f"  + {s}")
    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
