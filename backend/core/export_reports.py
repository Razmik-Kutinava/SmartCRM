"""Экспорт отчётов Excel/PDF: воронка, карточка лида, тендеры."""
from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.analytics_metrics import analytics_to_csv

_FONT_CANDIDATES = (
    Path(__file__).resolve().parent.parent / "data" / "fonts" / "DejaVuSans.ttf",
    Path(r"C:\Windows\Fonts\arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)


def _pdf_setup_font(pdf: Any) -> str:
    for path in _FONT_CANDIDATES:
        if path.is_file():
            pdf.add_font("ExpFont", "", str(path))
            pdf.set_font("ExpFont", size=11)
            return "ExpFont"
    pdf.set_font("Helvetica", size=11)
    return "Helvetica"


def _pdf_line(pdf: Any, text: str, font_name: str, h: float = 7) -> None:
    line = text or ""
    if font_name == "Helvetica":
        line = line.encode("latin-1", "replace").decode("latin-1")
    pdf.multi_cell(0, h, line)


def _pdf_bytes(title: str, lines: list[str]) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    font = _pdf_setup_font(pdf)
    pdf.set_font(font, size=14)
    _pdf_line(pdf, title, font, h=9)
    pdf.ln(4)
    pdf.set_font(font, size=11)
    for row in lines:
        _pdf_line(pdf, row, font)
        pdf.ln(1)
    out = pdf.output()
    if isinstance(out, bytes):
        return out
    if isinstance(out, bytearray):
        return bytes(out)
    return str(out).encode("latin-1")


def analytics_to_xlsx(metrics: dict[str, Any]) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "KPI"
    ws.append(["metric", "value"])
    ws.append(["total", metrics.get("total")])
    ws.append(["conversionPct", metrics.get("conversionPct")])
    ws.append(["wonCount", metrics.get("wonCount")])
    ws.append(["lostCount", metrics.get("lostCount")])
    ws.append(["avgDealRub", metrics.get("avgDealRub")])
    ws.append(["avgCycleDays", metrics.get("avgCycleDays")])
    ws.append([])
    ws.append(["stage", "count", "pct"])
    for row in metrics.get("funnel") or []:
        ws.append([row.get("stage"), row.get("count"), row.get("pct")])
    ws2 = wb.create_sheet("Sources")
    ws2.append(["source", "total", "won", "conversionPct"])
    for row in metrics.get("conversionBySource") or []:
        ws2.append([row.get("source"), row.get("total"), row.get("won"), row.get("conversionPct")])
    ws3 = wb.create_sheet("Forecast")
    fc = metrics.get("closureForecast") or {}
    ws3.append(["activeLeads", fc.get("activeLeads")])
    ws3.append(["avgProbabilityPct", fc.get("avgProbabilityPct")])
    ws3.append(["expectedPipelineRub", fc.get("expectedPipelineRub")])
    ws3.append([])
    ws3.append(["company", "stage", "score", "closeProbabilityPct", "expectedRub"])
    for row in fc.get("topOpportunities") or []:
        ws3.append([
            row.get("company"),
            row.get("stage"),
            row.get("score"),
            row.get("closeProbabilityPct"),
            row.get("expectedRub"),
        ])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def analytics_to_pdf(metrics: dict[str, Any]) -> bytes:
    lines = [
        f"Дата: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Лидов: {metrics.get('total')}",
        f"Конверсия: {metrics.get('conversionPct')}%",
        f"Выиграно / проиграно: {metrics.get('wonCount')} / {metrics.get('lostCount')}",
        "",
        "Воронка:",
    ]
    for row in metrics.get("funnel") or []:
        lines.append(f"  {row.get('stage')}: {row.get('count')} ({row.get('pct')}%)")
    lines.append("")
    lines.append("По источникам:")
    for row in metrics.get("conversionBySource") or []:
        lines.append(f"  {row.get('source')}: {row.get('conversionPct')}% ({row.get('won')}/{row.get('total')})")
    fc = metrics.get("closureForecast") or {}
    if fc.get("activeLeads"):
        lines.extend([
            "",
            f"Прогноз: активных {fc.get('activeLeads')}, ср. {fc.get('avgProbabilityPct')}%",
        ])
    return _pdf_bytes("SmartCRM — аналитика воронки", lines)


def lead_card_to_pdf(lead: dict[str, Any]) -> bytes:
    lines = [
        f"Компания: {lead.get('company')}",
        f"Контакт: {lead.get('contact')}",
        f"Email: {lead.get('email')}",
        f"Телефон: {lead.get('phone')}",
        f"Стадия: {lead.get('stage')}",
        f"Балл: {lead.get('score')}",
        f"Источник: {lead.get('source')}",
        f"Бюджет: {lead.get('budget')}",
        f"Сумма ₽: {lead.get('amountRub') or '—'}",
        f"Отрасль: {lead.get('industry')}",
        f"Город: {lead.get('city')}",
        f"Ответственный: {lead.get('responsible')}",
        "",
        f"Описание: {(lead.get('description') or '—')[:800]}",
    ]
    return _pdf_bytes(f"Карточка лида — {lead.get('company') or 'SmartCRM'}", lines)


def tenders_to_xlsx(items: list[dict[str, Any]]) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Tenders"
    ws.append(["id", "title", "customer", "budget", "deadline", "source", "status", "url"])
    for it in items:
        snap = it.get("snapshot") or it
        ws.append([
            it.get("id"),
            it.get("title") or snap.get("title"),
            it.get("customer") or snap.get("customer"),
            it.get("budget") or snap.get("budget"),
            it.get("deadline") or snap.get("deadline"),
            it.get("source") or snap.get("source"),
            it.get("status"),
            it.get("url") or snap.get("url"),
        ])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def tenders_to_pdf(items: list[dict[str, Any]]) -> bytes:
    lines = [f"Тендеров: {len(items)}", ""]
    for it in items[:40]:
        snap = it.get("snapshot") or it
        title = it.get("title") or snap.get("title") or "—"
        lines.append(f"• {title}")
        lines.append(
            f"  {snap.get('customer') or '—'} | {snap.get('budget') or '—'} | до {snap.get('deadline') or '—'}"
        )
    if len(items) > 40:
        lines.append(f"... и ещё {len(items) - 40}")
    return _pdf_bytes("SmartCRM — список тендеров", lines)


def analytics_export_bytes(metrics: dict[str, Any], fmt: str) -> tuple[bytes, str, str]:
    """Возвращает (content, media_type, filename)."""
    f = (fmt or "csv").lower()
    if f == "csv":
        text = analytics_to_csv(metrics)
        return text.encode("utf-8-sig"), "text/csv; charset=utf-8", "analytics-report.csv"
    if f == "xlsx":
        return (
            analytics_to_xlsx(metrics),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "analytics-report.xlsx",
        )
    if f == "pdf":
        return (
            analytics_to_pdf(metrics),
            "application/pdf",
            "analytics-report.pdf",
        )
    raise ValueError(f"unsupported format: {fmt}")
