"""Tenders routes."""
import asyncio
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from core.stats import track_api
from services.datanewton import DataNewtonClient
from services.gosplan import GosplanAPI
from services.tenderguru import TenderGuruClient
from services.zakupki_parser import ZakupkiParser

from .config import DATANEWTON_API_KEY, ENRICH_TOP_N, TENDERGURU_API_KEY
from .helpers import (
    _estimate_relevance,
    _normalize_item_for_ui,
    _passes_local_filters,
    _query_hits,
    _to_number,
    _tokenize_query,
)
from .web_search import append_web_tenders

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/search")
async def search_tenders(
    q: str = Query(..., description="Ключевые слова для поиска"),
    law: str = Query("all", description="44, 223, kom или all"),
    region: str = Query(None, description="Код региона (77 - Москва)"),
    price_min: int = Query(None, description="Минимальная цена"),
    price_max: int = Query(None, description="Максимальная цена"),
    date_start: str = Query(None, description="Дата начала (дд.мм.гггг)"),
    date_end: str = Query(None, description="Дата окончания (дд.мм.гггг)"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    sort: str = Query("by_date_end", description="Сортировка"),
    okpd: str = Query(None, description="Код ОКПД-2 для подсказки из Мои-Закупки (опционально)"),
) -> dict:
    """
    Поиск тендеров по ключевым словам и фильтрам
    Возвращает результаты из всех доступных источников
    """
    try:
        # Преобразуем 'all' в None для API
        fz = None if law == "all" else law

        # Преобразуем дату в формат API (дд.мм.гггг если передана как ISO).
        # Невалидную дату не глотаем тихо: возвращаем 400 вместо «магически» None.
        try:
            if date_start and len(date_start) == 10 and "-" in date_start:
                date_start = datetime.fromisoformat(date_start).strftime("%d.%m.%Y")
            if date_end and len(date_end) == 10 and "-" in date_end:
                date_end = datetime.fromisoformat(date_end).strftime("%d.%m.%Y")
        except ValueError as e:
            raise HTTPException(400, detail=f"Невалидная дата: {e.args[0] if e.args else 'формат ISO'}")

        logger.info(f"Starting tender search: q={q}, law={law}")
        serper_n = tavily_n = 0

        # Инициализируем клиентов для всех источников
        fz = None if law == "all" else law
        if law == "all":
            gosplan_laws = ["44", "223"]
        elif law in {"44", "223", "615"}:
            gosplan_laws = [law]
        else:
            gosplan_laws = ["44"]

        # Создаём асинхронные задачи для всех источников
        gosplan = GosplanAPI(use_prod=False)  # тестовый сервер
        client = TenderGuruClient(TENDERGURU_API_KEY)

        # Запускаем поиски в параллель
        scheduled = []

        # ГосПлан: при law=all ищем по 44 и 223, чтобы не терять часть рынка
        for gosplan_law in gosplan_laws:
            # Реальный счётчик вызовов Gosplan для панели API-лимитов.
            track_api("gosplan")
            task = asyncio.create_task(gosplan.search_purchases(
                kwords=q,
                fz=gosplan_law,
                limit=50,
                skip=0
            ))
            scheduled.append(("gosplan", gosplan_law, task))

        # TenderGuru
        if TENDERGURU_API_KEY:
            task = asyncio.create_task(client.search_tenders(
                kwords=q,
                fz=fz,
                region=region,
                price_min=price_min,
                price_max=price_max,
                date_start=date_start,
                date_end=date_end,
                page=page,
                sort_by=sort
            ))
            scheduled.append(("tenderguru", "all", task))

        # ZakupkiParser disabled by default.
        # zakupki.gov.ru рендерится JS и требует reverse-engineering внутреннего API
        # (BeautifulSoup/Selenium без этого возвращают 0 строк и +13с латентности).
        # Включается только если явно попросили через ENV ZAKUPKI_USE_SELENIUM=1.
        zakupki_enabled = os.getenv("ZAKUPKI_USE_SELENIUM", "").strip() in ("1", "true", "yes")
        if zakupki_enabled:
            parser = ZakupkiParser(use_selenium=True)
            task = asyncio.create_task(parser.search_tenders(q, gosplan_laws[0], region, price_min, price_max))
            scheduled.append(("zakupki", gosplan_laws[0], task))

        # Получаем результаты
        gosplan_batches = []
        tenderguru_data = []
        zakupki_data = []

        try:
            try:
                raw_results = await asyncio.gather(*[t[2] for t in scheduled], return_exceptions=True)
            except BaseException:
                # Если await отменили снаружи — отменяем все запущенные таски,
                # иначе они продолжат жить и держать httpx-соединения.
                for _src, _law, _t in scheduled:
                    if not _t.done():
                        _t.cancel()
                raise
            for (source, source_law, _task), result in zip(scheduled, raw_results):
                if isinstance(result, Exception):
                    logger.warning("Tender source failed: source=%s law=%s error=%s", source, source_law, result)
                    if source == "gosplan":
                        # Ошибка без доп. инкремента calls_* (count=0),
                        # чтобы не удваивать вызовы в статистике.
                        track_api("gosplan", count=0, error=True)
                    continue
                if source == "gosplan" and isinstance(result, dict):
                    if result.get("error"):
                        track_api("gosplan", count=0, error=True)
                    gosplan_batches.append((source_law, result))
                elif source == "tenderguru":
                    tenderguru_data = result if result else []
                elif source == "zakupki":
                    zakupki_data = result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Error gathering results: {e}")

        # Инициализируем
        formatted_tenders = []
        data_gaps_summary = {}
        gosplan_count = 0
        tenderguru_count = 0
        zakupki_count = 0
        all_ids = set()

        query_tokens = _tokenize_query(q)

        # GosplanAPI v2 (free tier) игнорирует параметр q и возвращает последние
        # закупки без фильтрации по ключевым словам (подтверждено тестом: одинаковый
        # набор при q=SIEM и q=random_garbage). Показываем их как "свежие закупки
        # ЕИС" в хвосте выдачи, но ограничиваем 5 штуками чтобы не засорять экран.
        GOSPLAN_UNFILTERED_CAP = 5
        gosplan_unfiltered = 0

        # 1. ГосПлан результаты (основной источник)
        for gosplan_law, gosplan_data in gosplan_batches:
            purchases = gosplan_data.get("purchases", []) if isinstance(gosplan_data, dict) else []
            for purchase in purchases:
                if not isinstance(purchase, dict):
                    continue
                # Фильтруем пустые записи - нужно хотя бы название или описание
                if not purchase.get("object_info") and not purchase.get("name") and not purchase.get("title") and not purchase.get("description"):
                    continue

                raw_purchase = dict(purchase)
                raw_purchase["__law"] = gosplan_law
                formatted = GosplanAPI.format_purchase(raw_purchase)
                hay_text = f"{formatted.get('name','')} {formatted.get('description','')}"
                match_hits = _query_hits(q, hay_text)

                is_keyword_match = match_hits > 0 or not query_tokens

                if not is_keyword_match:
                    # GosplanAPI не поддерживает keyword-поиск — API игнорирует q.
                    # Показываем до GOSPLAN_UNFILTERED_CAP свежих тендеров из ЕИС
                    # в хвосте, помечаем unfiltered=True чтобы фронт мог лейблить.
                    if gosplan_unfiltered >= GOSPLAN_UNFILTERED_CAP:
                        continue
                    formatted["unfiltered"] = True
                    formatted["relevance"] = 5  # ниже любых релевантных
                    gosplan_unfiltered += 1
                else:
                    formatted["relevance"] = _estimate_relevance(
                        q=q,
                        text=hay_text,
                        has_budget=bool(_to_number(formatted.get("budget"))),
                        has_deadline=bool(formatted.get("deadline")),
                    )

                if not _passes_local_filters(formatted, region, price_min, price_max, date_start, date_end):
                    continue
                gaps = GosplanAPI.get_data_gaps(raw_purchase)
                formatted["data_gaps"] = gaps
                formatted["source"] = "gosplan"

                item_id = f"gosplan:{formatted.get('id')}"
                if item_id in all_ids:
                    continue

                formatted_tenders.append(formatted)
                gosplan_count += 1
                all_ids.add(item_id)
                for gap in gaps:
                    data_gaps_summary[gap] = data_gaps_summary.get(gap, 0) + 1

        # 2. TenderGuru результаты (дополнительный источник)
        if isinstance(tenderguru_data, list) and tenderguru_data:
            tenderguru_formatted = TenderGuruClient.format_search_response(tenderguru_data)
            tenders_list = tenderguru_formatted.get("tenders", [])
            tenderguru_count = len(tenders_list)

            for tender in tenders_list:
                if not _passes_local_filters(tender, region, price_min, price_max, date_start, date_end):
                    continue
                item_id = f"tenderguru:{tender.get('id')}"
                if item_id not in all_ids:
                    tender["source"] = "tenderguru"
                    formatted_tenders.append(tender)
                    all_ids.add(item_id)

        # 3. ZakupkiParser результаты (дополнительный источник)
        if isinstance(zakupki_data, list):
            zakupki_count = len(zakupki_data)
            for tender in zakupki_data:
                if isinstance(tender, dict) and _passes_local_filters(tender, region, price_min, price_max, date_start, date_end):
                    item_id = f"zakupki:{tender.get('id')}"
                    if item_id in all_ids:
                        continue
                    tender["source"] = "zakupki"
                    formatted_tenders.append(tender)
                    all_ids.add(item_id)

        serper_n, tavily_n = await append_web_tenders(
            formatted_tenders,
            all_ids,
            q,
            law,
            region,
            price_min,
            price_max,
            date_start,
            date_end,
        )

        # Сортируем по релевантности
        formatted_tenders.sort(key=lambda x: x.get("relevance", 0), reverse=True)

        # 4. Обогащение через DataNewton: тянем информацию о заказчике
        #    (ЕГРЮЛ, риски, скоринг, статистика госконтрактов) для топ-N
        #    самых релевантных карточек. Работает в параллель, не блокирует
        #    выдачу при фейле (любые ошибки заглушены внутри клиента).
        datanewton_enriched = 0
        if DATANEWTON_API_KEY and formatted_tenders:
            top_tenders = formatted_tenders[:ENRICH_TOP_N]
            inns_to_enrich = [
                str(t.get("customer_inn") or "").strip()
                for t in top_tenders
                if t.get("customer_inn")
            ]
            if inns_to_enrich:
                try:
                    # enrich_many() внутри делает 4 вызова на каждый валидный ИНН:
                    # counterparty + risks + scoring + governmentContractsStat.
                    # Учитываем это в статистике лимитов DataNewton.
                    unique_inns = {
                        inn for inn in inns_to_enrich
                        if inn.isdigit() and len(inn) in (10, 12)
                    }
                    if unique_inns:
                        track_api("datanewton", count=len(unique_inns) * 4)

                    dn_client = DataNewtonClient(DATANEWTON_API_KEY)
                    enrichment_map = await dn_client.enrich_many(inns_to_enrich)
                    for tender in top_tenders:
                        inn = str(tender.get("customer_inn") or "").strip()
                        raw_enr = enrichment_map.get(inn)
                        if raw_enr:
                            summary = DataNewtonClient.format_enrichment(raw_enr)
                            if summary:
                                # Сохраняем сырые данные для детального вью,
                                # а плоские поля — для списка.
                                tender["enrichment"] = summary
                                tender["enrichment_source"] = "datanewton"
                                # Подменяем имя заказчика на полное из ЕГРЮЛ,
                                # если у нас был только ИНН.
                                existing_name = str(tender.get("customer") or "").strip()
                                full_name = summary.get("customer_full_name")
                                short_name = summary.get("customer_short_name")
                                if (not existing_name or existing_name.isdigit()) and (short_name or full_name):
                                    tender["customer"] = short_name or full_name
                                datanewton_enriched += 1
                    logger.info(
                        "DataNewton enrichment: %d/%d tenders enriched",
                        datanewton_enriched, len(top_tenders),
                    )
                except Exception as e:
                    track_api("datanewton", count=0, error=True)
                    logger.warning("DataNewton enrichment skipped due to error: %s", e)

        formatted_tenders = [_normalize_item_for_ui(x) for x in formatted_tenders]

        result = {
            "total": len(formatted_tenders),
            "tenders": formatted_tenders,
            "page": page,
            "sources": {
                "gosplan": {
                    "count": gosplan_count,
                    "status": "success" if gosplan_count > 0 else "no_data",
                    # GosplanAPI free tier не фильтрует по ключевым словам.
                    # unfiltered_count > 0 означает, что часть результатов —
                    # просто последние закупки ЕИС, не связанные с запросом.
                    "unfiltered_count": gosplan_unfiltered,
                    "keyword_filtered": gosplan_count - gosplan_unfiltered,
                    "note": "GosplanAPI free tier не поддерживает keyword-фильтрацию" if gosplan_unfiltered > 0 else None,
                },
                "tenderguru": {
                    "count": tenderguru_count,
                    "status": "success" if tenderguru_count > 0 else "no_data",
                },
                "zakupki": {
                    "count": zakupki_count,
                    "status": "success" if zakupki_count > 0 else "no_data",
                },
                "datanewton": {
                    "count": datanewton_enriched,
                    "status": (
                        "success" if datanewton_enriched > 0
                        else ("not_configured" if not DATANEWTON_API_KEY else "no_data")
                    ),
                    "role": "enrichment",
                    "note": "Обогащает карточки тендеров данными о заказчиках (ЕГРЮЛ, скоринг, риски). Не поисковый источник.",
                },
                "moy_zakupki": {
                    "count": 0,
                    "status": "classifier_only",
                    "role": "classifier",
                    "note": "Справочник ОКПД-2/КТРУ. Поискового эндпоинта по тендерам не предоставляет.",
                },
                "serper": {
                    "count": serper_n,
                    "status": "success" if serper_n else ("not_configured" if not os.getenv("SERPER_API_KEY") else "no_data"),
                    "role": "web_search",
                },
                "tavily": {
                    "count": tavily_n,
                    "status": "success" if tavily_n else ("not_configured" if not os.getenv("TAVILY_API_KEY") else "no_data"),
                    "role": "web_search",
                },
            },
            "message": (
                f"Найдено {len(formatted_tenders)} релевантных тендеров"
                + (f", обогащено {datanewton_enriched}" if datanewton_enriched else "")
                if formatted_tenders else "По запросу не найдено релевантных тендеров"
            ),
        }

        logger.info(
            "Tender search completed: q=%s gosplan=%d tenderguru=%d zakupki=%d enriched=%d total=%d",
            q, gosplan_count, tenderguru_count, zakupki_count, datanewton_enriched, len(formatted_tenders),
        )

        result["classifiers"] = {}
        if (os.getenv("MOY_ZAKUPKI_API_KEY") or "").strip():
            try:
                from services.moy_zakupki import fetch_classifier_hints

                result["classifiers"] = await fetch_classifier_hints(q, okpd)
            except Exception as mz_e:
                logger.warning("Мои-Закупки (подсказки): %s", mz_e)
                result["classifiers"] = {"enabled": True, "error": str(mz_e)}

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tender search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка поиска тендеров")

