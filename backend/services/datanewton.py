"""
DataNewton API v1 — обогащение карточек тендеров данными о заказчиках.
https://api.datanewton.ru/v1

Используется для enrichment: после того, как основные источники (ГосПлан,
TenderGuru) вернули тендеры, мы дёргаем DataNewton по ИНН заказчика и
прикрепляем к карточке:
  - counterparty (ЕГРЮЛ/ЕГРИП: статус, адрес, ОГРН, дата регистрации, ОКВЭД)
  - risks        (признаки однодневки, банкротства и пр.)
  - scoring      (скоринг надёжности)
  - governmentContractsStat (сводка по госконтрактам заказчика)

Лимиты:
  - 200 запросов/мин на API-ключ
  - 100 запросов/мин на batch-методы
  - 10 TCP-соединений с одного IP

Бесплатный доступ, ключ в DATANEWTON_API_KEY.
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

DATANEWTON_BASE = "https://api.datanewton.ru"
DEFAULT_TIMEOUT = httpx.Timeout(15.0)
# Общий семафор на модуль: уважаем лимит 10 TCP-соединений с IP.
_tcp_semaphore = asyncio.Semaphore(8)


class DataNewtonClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv("DATANEWTON_API_KEY") or "").strip()
        self.base = DATANEWTON_BASE
        self.timeout = DEFAULT_TIMEOUT

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _params(self, **extra: Any) -> Dict[str, Any]:
        p: Dict[str, Any] = {"key": self.api_key}
        for k, v in extra.items():
            if v is None or v == "" or v == []:
                continue
            p[k] = v
        return p

    async def _get(
        self,
        client: httpx.AsyncClient,
        path: str,
        params: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Единая точка GET-запросов к DataNewton.

        Возвращает распарсенный JSON или None при любой ошибке
        (не хотим из-за одного обогащения валить весь поиск).
        """
        async with _tcp_semaphore:
            try:
                r = await client.get(f"{self.base}{path}", params=params)
            except httpx.HTTPError as e:
                logger.warning("DataNewton %s network error: %s: %s", path, type(e).__name__, e)
                return None

        if r.status_code == 429:
            logger.warning("DataNewton %s: rate limit (429)", path)
            return None
        if r.status_code == 404:
            # 404 = по этому ИНН данных нет, это нормальный кейс
            return None
        if r.status_code >= 400:
            logger.info("DataNewton %s status=%s", path, r.status_code)
            return None
        try:
            return r.json()
        except ValueError:
            logger.warning("DataNewton %s: non-JSON response", path)
            return None

    # ── Индивидуальные методы ────────────────────────────────────────────

    async def counterparty(
        self,
        client: httpx.AsyncClient,
        *,
        inn: Optional[str] = None,
        ogrn: Optional[str] = None,
        filters: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Общая информация о контрагенте из ЕГРЮЛ/ЕГРИП (/v1/counterparty)."""
        params = self._params(
            inn=inn,
            ogrn=ogrn,
            filters=",".join(filters) if filters else None,
        )
        return await self._get(client, "/v1/counterparty", params)

    async def risks(
        self, client: httpx.AsyncClient, *, inn: Optional[str] = None, ogrn: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        return await self._get(client, "/v1/risks", self._params(inn=inn, ogrn=ogrn))

    async def scoring(
        self, client: httpx.AsyncClient, *, inn: Optional[str] = None, ogrn: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        return await self._get(client, "/v1/scoring", self._params(inn=inn, ogrn=ogrn))

    async def gov_contracts_stat(
        self, client: httpx.AsyncClient, *, inn: Optional[str] = None, ogrn: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Статистика по госконтрактам заказчика (/v1/governmentContractsStat)."""
        return await self._get(client, "/v1/governmentContractsStat", self._params(inn=inn, ogrn=ogrn))

    async def suggestions(
        self, client: httpx.AsyncClient, query: str
    ) -> Optional[Dict[str, Any]]:
        """Быстрый поиск до 10 контрагентов (/v1/suggestions)."""
        return await self._get(client, "/v1/suggestions", self._params(query=query))

    # ── Высокоуровневый enrichment ───────────────────────────────────────

    async def enrich(self, inn: str) -> Dict[str, Any]:
        """Параллельно дернуть 4 метода и вернуть сырые данные.

        Возвращает словарь с ключами counterparty/risks/scoring/gov_contracts_stat
        (каждый может быть None, если метод упал/не нашёл).
        """
        if not self.configured:
            return {"error": "api_key_missing"}

        inn_str = str(inn or "").strip()
        if not inn_str.isdigit() or len(inn_str) not in (10, 12):
            return {}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            cp, risks, scoring, gc_stat = await asyncio.gather(
                self.counterparty(client, inn=inn_str),
                self.risks(client, inn=inn_str),
                self.scoring(client, inn=inn_str),
                self.gov_contracts_stat(client, inn=inn_str),
                return_exceptions=False,  # _get сам глотает исключения
            )

        return {
            "counterparty": cp,
            "risks": risks,
            "scoring": scoring,
            "gov_contracts_stat": gc_stat,
        }

    async def enrich_many(self, inns: List[str]) -> Dict[str, Dict[str, Any]]:
        """Обогатить сразу список ИНН.

        Выполняется в параллель; TCP-лимит соблюдается модульным семафором.
        Уникализируем входные ИНН, чтобы не дёргать одно и то же N раз.
        """
        if not self.configured:
            return {}

        unique: List[str] = []
        seen = set()
        for inn in inns:
            s = str(inn or "").strip()
            if not s.isdigit() or len(s) not in (10, 12):
                continue
            if s in seen:
                continue
            seen.add(s)
            unique.append(s)

        if not unique:
            return {}

        tasks = [self.enrich(inn) for inn in unique]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        out: Dict[str, Dict[str, Any]] = {}
        for inn, res in zip(unique, results):
            if isinstance(res, Exception):
                logger.debug("DataNewton enrich(%s) failed: %s", inn, res)
                continue
            if isinstance(res, dict) and res and "error" not in res:
                out[inn] = res
        return out

    # ── Форматтер под UI ──────────────────────────────────────────────────

    @staticmethod
    def format_enrichment(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Компактная сводка для карточки тендера в UI.

        На вход — результат enrich(). На выход — плоский словарь с ключами
        `customer_*`, готовыми для склейки с tender-объектом.
        """
        if not isinstance(raw, dict) or not raw:
            return {}

        out: Dict[str, Any] = {}

        # --- counterparty ---------------------------------------------------
        # Реальный формат DataNewton: {"inn", "ogrn", "company": {company fields}}
        cp_raw = raw.get("counterparty") or {}
        company = cp_raw.get("company") if isinstance(cp_raw, dict) else None
        if not isinstance(company, dict):
            company = cp_raw if isinstance(cp_raw, dict) else {}

        out["customer_inn"] = cp_raw.get("inn") if isinstance(cp_raw, dict) else None
        out["customer_ogrn"] = cp_raw.get("ogrn") if isinstance(cp_raw, dict) else None

        if company:
            # Имена — обычно лежат внутри company_names
            names = company.get("company_names") or {}
            if isinstance(names, dict):
                out["customer_full_name"] = (
                    names.get("full_name")
                    or names.get("fullName")
                    or company.get("full_name")
                )
                out["customer_short_name"] = (
                    names.get("short_name")
                    or names.get("shortName")
                    or company.get("short_name")
                    or company.get("name")
                )
            else:
                out["customer_full_name"] = company.get("full_name")
                out["customer_short_name"] = company.get("short_name") or company.get("name")

            # Статус: {"status": {"name": "ACTIVE", "desc": "Действующая"}}
            status_raw = company.get("status")
            if isinstance(status_raw, dict):
                out["customer_status"] = status_raw.get("desc") or status_raw.get("name")
            elif isinstance(status_raw, str):
                out["customer_status"] = status_raw

            # Адрес: {"address": {"line_address": "..."}}
            addr_raw = company.get("address")
            if isinstance(addr_raw, dict):
                out["customer_address"] = (
                    addr_raw.get("line_address")
                    or addr_raw.get("address")
                    or addr_raw.get("full_address")
                )
            elif isinstance(addr_raw, str):
                out["customer_address"] = addr_raw

            out["customer_registration_date"] = company.get("registration_date")
            if company.get("years_from_registration") is not None:
                out["customer_years_from_registration"] = company.get("years_from_registration")

            # Основной ОКВЭД: okveds — список, первый — основной
            okveds = company.get("okveds")
            if isinstance(okveds, list) and okveds and isinstance(okveds[0], dict):
                primary = okveds[0]
                out["customer_okved"] = primary.get("code")
                out["customer_okved_name"] = primary.get("name")

            # ОПФ
            opf = company.get("opf")
            if isinstance(opf, dict):
                out["customer_opf"] = opf.get("full") or opf.get("short")

            # Сотрудники
            workers = company.get("workers_count")
            if isinstance(workers, dict):
                out["customer_workers"] = workers.get("count")
            elif isinstance(workers, int):
                out["customer_workers"] = workers

            # Уставной капитал
            capital = company.get("charter_capital")
            if isinstance(capital, dict):
                out["customer_charter_capital"] = capital.get("sum") or capital.get("value")
            elif isinstance(capital, (int, float)):
                out["customer_charter_capital"] = capital

        # --- scoring --------------------------------------------------------
        # Реальный формат: {"ogrn", "scoring": {"score": 0, "status": {"desc": "...", "name": "HIGH"}}}
        scoring_raw = raw.get("scoring")
        scoring_obj = (scoring_raw or {}).get("scoring") if isinstance(scoring_raw, dict) else None
        if isinstance(scoring_obj, dict):
            out["customer_score"] = scoring_obj.get("score")
            st = scoring_obj.get("status")
            if isinstance(st, dict):
                out["customer_reliability"] = st.get("desc") or st.get("name")
            elif isinstance(st, str):
                out["customer_reliability"] = st

        # --- risks ----------------------------------------------------------
        # Реальный формат: {"ogrn", "flags": [{"value": bool, "color": "NEGATIVE", "details": [[{name,value},...]]}]}
        risks_raw = raw.get("risks") or {}
        risk_items: List[str] = []
        negative_count = 0
        if isinstance(risks_raw, dict):
            flags = risks_raw.get("flags") or risks_raw.get("risks") or []
            if isinstance(flags, list):
                for f in flags:
                    if not isinstance(f, dict):
                        continue
                    if not f.get("value"):
                        continue
                    is_negative = str(f.get("color") or "").upper() == "NEGATIVE"
                    if is_negative:
                        negative_count += 1
                    # details — список списков объектов {name, value}
                    label = None
                    details = f.get("details")
                    if isinstance(details, list) and details:
                        first = details[0] if isinstance(details[0], list) else details
                        if isinstance(first, list):
                            for d in first:
                                if isinstance(d, dict) and d.get("name") in ("Тип", "тип", "title"):
                                    label = d.get("value")
                                    break
                    if not label:
                        label = f.get("name") or f.get("title") or f.get("description")
                    if label:
                        risk_items.append(str(label))
        out["customer_risks"] = risk_items[:10]
        out["customer_risks_count"] = len(risk_items)
        if negative_count:
            out["customer_risks_negative"] = negative_count

        # --- gov contracts stat ---------------------------------------------
        gcs = raw.get("gov_contracts_stat") or {}
        if isinstance(gcs, dict) and gcs:
            out["customer_gov_contracts_total"] = (
                gcs.get("totalContracts")
                or gcs.get("total_contracts")
                or gcs.get("total")
            )
            out["customer_gov_contracts_sum"] = (
                gcs.get("totalSum") or gcs.get("total_sum") or gcs.get("sum")
            )
            out["customer_gov_contracts_last_year"] = (
                gcs.get("last_year_contracts") or gcs.get("lastYearContracts")
            )

        # Выкидываем пустые ключи — UI не захламляем
        return {k: v for k, v in out.items() if v not in (None, "", [], 0)}
