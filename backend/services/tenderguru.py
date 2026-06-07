"""
TenderGuru API Integration
Поиск и мониторинг государственных и коммерческих закупок
"""

import httpx
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

TENDERGURU_API_URL = "https://www.tenderguru.ru/api2.3/export"


class TenderGuruClient:
    def __init__(self, api_code: str):
        """
        Инициализация клиента TenderGuru

        Args:
            api_code: API ключ для доступа к TenderGuru
        """
        self.api_code = api_code
        self.api_url = TENDERGURU_API_URL
        self.timeout = httpx.Timeout(30.0)

    async def search_tenders(
        self,
        kwords: str,
        fz: Optional[str] = None,
        region: Optional[str] = None,
        city_id: Optional[int] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        page: int = 1,
        sort_by: str = "by_date_end",
        actual: int = 1,
    ) -> Dict[str, Any]:
        """
        Поиск тендеров по ключевым словам и фильтрам

        Args:
            kwords: Ключевые слова для поиска
            fz: Закон (44, 223, kom) или None для всех
            region: Код региона (77 - Москва и т.д.)
            city_id: ID города
            price_min: Минимальная цена
            price_max: Максимальная цена
            date_start: Дата начала в формате дд.мм.гггг
            date_end: Дата окончания в формате дд.мм.гггг
            page: Номер страницы
            sort_by: Сортировка (by_date, by_date_end, by_price)
            actual: 1 для актуальных данных, 0 для архива

        Returns:
            Словарь с результатами поиска
        """
        params = {
            "kwords": kwords,
            "dtype": "json",
            "api_code": self.api_code,
            "page": page,
            "sort_by": sort_by,
            "actual": actual,
        }

        # Добавляем опциональные параметры
        if fz:
            params["f"] = fz
        if region:
            params[f"r{region}"] = 1
        if city_id:
            params["city_id"] = city_id
        if price_min:
            params["price1"] = price_min
        if price_max:
            params["price2"] = price_max
        if date_start:
            params["date_start"] = date_start
        if date_end:
            params["date_end"] = date_end

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()
                # TenderGuru может возвращать список или словарь
                total = len(data) if isinstance(data, list) else data.get('Total', 0) if isinstance(data, dict) else 0
                logger.info(f"TenderGuru search: {kwords}, found: {total}")
                return data
        except httpx.HTTPError as e:
            logger.error(f"TenderGuru API error: {e}")
            raise

    async def get_tender_detail(self, tender_id: int) -> Dict[str, Any]:
        """
        Получить детальную информацию о тендере по ID

        Args:
            tender_id: Внутренний ID тендера в TenderGuru

        Returns:
            Детальная информация о тендере
        """
        params = {
            "id": tender_id,
            "dtype": "json",
            "api_code": self.api_code,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.info(f"TenderGuru detail loaded: {tender_id}")
                return data
        except httpx.HTTPError as e:
            logger.error(f"TenderGuru detail error: {e}")
            raise

    async def get_tender_by_number(self, tend_num: str) -> Dict[str, Any]:
        """
        Получить информацию о тендере по номеру закупки (ЕИС/площадка)

        Args:
            tend_num: Номер тендера в ЕИС/источнике

        Returns:
            Информация о тендере
        """
        params = {
            "tend_num": tend_num,
            "dtype": "json",
            "api_code": self.api_code,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.info(f"TenderGuru by number: {tend_num}")
                return data
        except httpx.HTTPError as e:
            logger.error(f"TenderGuru by number error: {e}")
            raise

    async def search_by_documentation(self, kwords: str, page: int = 1) -> Dict[str, Any]:
        """
        Поиск по тексту документации закупок

        Args:
            kwords: Ключевые слова для поиска в документах
            page: Номер страницы

        Returns:
            Результаты поиска по документам
        """
        url = f"{TENDERGURU_API_URL}/documentation"
        params = {
            "kwords": kwords,
            "dtype": "json",
            "api_code": self.api_code,
            "page": page,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.info(f"TenderGuru docs search: {kwords}")
                return data
        except httpx.HTTPError as e:
            logger.error(f"TenderGuru docs search error: {e}")
            raise

    async def search_by_products(
        self,
        okpd_code: Optional[str] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Поиск тендеров в разрезе продукции (ОКПД2)

        Args:
            okpd_code: Код ОКПД2 (например 21.20.23.110)
            page: Номер страницы

        Returns:
            Тендеры с детализацией по позициям ОКПД2
        """
        url = f"{TENDERGURU_API_URL}/products"
        params = {
            "dtype": "json",
            "api_code": self.api_code,
            "page": page,
        }

        if okpd_code:
            # Преобразуем ОКПД2 код в параметры d1, d2, d3, d4
            parts = okpd_code.split(".")
            if len(parts) >= 1:
                params["d1"] = parts[0]
            if len(parts) >= 2:
                params["d2"] = parts[1]
            if len(parts) >= 3:
                params["d3"] = parts[2]
            if len(parts) >= 4:
                params["d4"] = parts[3]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.info(f"TenderGuru products search: {okpd_code}")
                return data
        except httpx.HTTPError as e:
            logger.error(f"TenderGuru products search error: {e}")
            raise

    async def get_online_tenders(
        self,
        kwords: Optional[str] = None,
        region: Optional[str] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Получить оперативные (сегодняшние) тендеры

        Args:
            kwords: Ключевые слова (опционально)
            region: Код региона (опционально)
            page: Номер страницы

        Returns:
            Тендеры, объявленные сегодня
        """
        url = f"{TENDERGURU_API_URL}/online"
        params = {
            "dtype": "json",
            "api_code": self.api_code,
            "page": page,
        }

        if kwords:
            params["kwords"] = kwords
        if region:
            params[f"r{region}"] = 1

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.info(f"TenderGuru online tenders loaded")
                return data
        except httpx.HTTPError as e:
            logger.error(f"TenderGuru online tenders error: {e}")
            raise

    async def resolve_customer_inn(
        self,
        user_id: int | str,
        fz_hint: str | None = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Резолв ИНН/имени заказчика по User_id из TenderGuru search-результата.

        Free-tier TenderGuru скрывает Customer и CustomerINN напрямую,
        но эндпоинты /api2.0/export?mode=(kom)zakazinfo&id=<user_id>
        возвращают открытое имя и ИНН. Используется для того, чтобы
        передать ИНН дальше в DataNewton для обогащения карточки.

        Args:
            user_id: Внутренний ID заказчика TenderGuru (User_id поля).
            fz_hint: "223" → komzakazinfo, иначе zakazinfo.

        Returns:
            {"customer": str, "customer_inn": str} или None, если не резолвится.
        """
        if not user_id or str(user_id) in ("0", ""):
            return None

        url = "https://www.tenderguru.ru/api2.0/export"
        mode = "komzakazinfo" if str(fz_hint) == "223" else "zakazinfo"
        params = {
            "mode": mode,
            "id": user_id,
            "api_code": self.api_code,
            "dtype": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(url, params=params)
                if r.status_code != 200:
                    return None
                data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.debug(f"TenderGuru resolve_customer_inn({user_id}, {fz_hint}): {e}")
            return None

        item: Optional[Dict[str, Any]] = None
        if isinstance(data, list) and data and isinstance(data[0], dict):
            item = data[0]
        elif isinstance(data, dict):
            item = data

        if not item:
            return None

        inn = str(item.get("INN") or item.get("inn") or "").strip()
        name = str(item.get("Customer") or item.get("customer") or "").strip()
        # HTML-entities → обычный текст
        name = name.replace("&#034;", '"').replace("&quot;", '"').replace("&amp;", "&")

        if not inn.isdigit() or len(inn) not in (10, 12):
            # Возможно попали не в тот режим — попробуем зеркальный
            alt_mode = "zakazinfo" if mode == "komzakazinfo" else "komzakazinfo"
            params["mode"] = alt_mode
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    r = await client.get(url, params=params)
                    if r.status_code == 200:
                        data = r.json()
                        if isinstance(data, list) and data and isinstance(data[0], dict):
                            item = data[0]
                        elif isinstance(data, dict):
                            item = data
                        inn = str(item.get("INN") or item.get("inn") or "").strip()
                        new_name = str(item.get("Customer") or item.get("customer") or "").strip()
                        if new_name:
                            name = new_name.replace("&#034;", '"').replace("&quot;", '"').replace("&amp;", "&")
            except (httpx.HTTPError, ValueError):
                pass

        if not inn.isdigit() or len(inn) not in (10, 12):
            return None

        return {"customer": name, "customer_inn": inn}

    async def search_plans(
        self,
        kwords: Optional[str] = None,
        org_inn: Optional[str] = None,
        fz: Optional[str] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        purchase_planned_date_start: Optional[str] = None,
        purchase_planned_date_end: Optional[str] = None,
        purchase_execution_date_start: Optional[str] = None,
        purchase_execution_date_end: Optional[str] = None,
        region: Optional[str] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Поиск планов закупок (/planzakup).
        """
        url = f"{self.api_url}/planzakup"
        params: Dict[str, Any] = {
            "dtype": "json",
            "api_code": self.api_code,
            "page": page,
        }
        if kwords:
            params["kwords"] = kwords
        if org_inn:
            params["org_inn"] = org_inn
        if fz:
            params["fz"] = fz
        if price_min is not None:
            params["price1"] = price_min
        if price_max is not None:
            params["price2"] = price_max
        if purchase_planned_date_start:
            params["purchasePlannedDate_start"] = purchase_planned_date_start
        if purchase_planned_date_end:
            params["purchasePlannedDate_end"] = purchase_planned_date_end
        if purchase_execution_date_start:
            params["purchaseExecutionDate_start"] = purchase_execution_date_start
        if purchase_execution_date_end:
            params["purchaseExecutionDate_end"] = purchase_execution_date_end
        if region:
            params[f"r{region}"] = 1

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                total = len(data) if isinstance(data, list) else data.get("Total", 0) if isinstance(data, dict) else 0
                logger.info(f"TenderGuru plans search: kwords={kwords}, org_inn={org_inn}, found={total}")
                return data
        except httpx.HTTPError as e:
            logger.error(f"TenderGuru plans search error: {e}")
            raise

    async def get_plan_detail(
        self,
        *,
        plan_id: Optional[int] = None,
        reestr_number: Optional[str] = None,
        lot_number: Optional[str] = None,
        inn: Optional[str] = None,
        spz: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Карточка плана закупки (/plans).
        """
        url = f"{self.api_url}/plans"
        params: Dict[str, Any] = {
            "dtype": "json",
            "api_code": self.api_code,
        }
        if plan_id is not None:
            params["id"] = plan_id
        if reestr_number:
            params["reestr_number"] = reestr_number
        if lot_number:
            params["lot_number"] = lot_number
        if inn:
            params["inn"] = inn
        if spz:
            params["spz"] = spz

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.info("TenderGuru plan detail loaded")
                return data
        except httpx.HTTPError as e:
            logger.error(f"TenderGuru plan detail error: {e}")
            raise

    @staticmethod
    def format_plans_response(raw_data) -> Dict[str, Any]:
        """
        Приведение /planzakup и /plans к единому формату для UI.
        """
        items: list[dict[str, Any]] = []
        if isinstance(raw_data, list):
            items = [x for x in raw_data if isinstance(x, dict)]
        elif isinstance(raw_data, dict):
            for _k, val in raw_data.items():
                if isinstance(val, dict) and (val.get("PlanName") or val.get("ReestrNumber") or val.get("Customer")):
                    items.append(val)
                elif isinstance(val, list):
                    items.extend([x for x in val if isinstance(x, dict)])

        def parse_date(raw: str | None):
            if not raw:
                return None
            s = str(raw).strip()
            if not s:
                return None
            try:
                if len(s) == 10 and s[2] == "-" and s[5] == "-":
                    d, m, y = s.split("-")
                    return datetime(int(y), int(m), int(d))
                if len(s) == 10 and s[4] == "-" and s[7] == "-":
                    return datetime.fromisoformat(s)
                return datetime.fromisoformat(s.replace("Z", "+00:00"))
            except Exception:
                return None

        formatted = []
        for item in items:
            name = str(item.get("PlanName") or item.get("name") or "").strip()
            customer = str(item.get("Customer") or "").strip()
            if not name and not customer:
                continue

            deadline_dt = parse_date(item.get("DateEnd") or item.get("SrokRazmZakaza"))
            published_dt = parse_date(item.get("Date") or item.get("DateStart"))
            budget = item.get("Price")
            budget_num = None
            try:
                if budget is not None and budget != "":
                    budget_num = float(str(budget).replace(" ", "").replace(",", "."))
            except Exception:
                budget_num = None

            formatted.append({
                "id": item.get("ID") or item.get("id") or item.get("planID") or item.get("ReestrNumber"),
                "name": name or f"План закупки {item.get('ReestrNumber') or ''}".strip(),
                "description": item.get("Fragment") or item.get("Info") or "",
                "customer": customer,
                "customer_inn": str(item.get("CustomerInn") or item.get("inn") or ""),
                "region": item.get("Region") or "",
                "budget": budget_num,
                "deadline": deadline_dt.isoformat() if deadline_dt else None,
                "published_date": published_dt.isoformat() if published_dt else None,
                "platform": "TenderGuru",
                "law": str(item.get("Law") or ""),
                "source": "tenderguru_plan",
                "external_url": item.get("CustomerPlanLink") or item.get("ApiLink") or item.get("ApiLotLink") or "",
                "plan_number": item.get("planNumber"),
                "plan_id": item.get("planID"),
                "lot_id": item.get("lotID"),
                "reestr_number": item.get("ReestrNumber"),
                "okpd2": item.get("Okpd2"),
                "year": item.get("Year"),
                "status": "planned",
                "relevance": 100,
                "raw": item,
            })

        return {"total": len(formatted), "plans": formatted, "page": 1}

    @staticmethod
    def format_search_response(raw_data) -> Dict[str, Any]:
        """
        Форматирование ответа API для фронтенда

        Args:
            raw_data: Сырые данные от API (список или словарь)

        Returns:
            Форматированные данные
        """
        items = []

        if isinstance(raw_data, list):
            # TenderGuru возвращает список тендеров
            items = [item for item in raw_data if isinstance(item, dict) and item.get("TenderName")]
        elif isinstance(raw_data, dict):
            # Ответ от поиска - словарь с индексами как строки
            for key, item in raw_data.items():
                if isinstance(item, dict) and item.get("TenderName"):
                    items.append(item)
                elif isinstance(item, list):
                    # Может быть список внутри словаря
                    items.extend([x for x in item if isinstance(x, dict) and x.get("TenderName")])

        formatted = []
        for item in items:
            if not isinstance(item, dict):
                continue

            # Фильтруем результаты - пропускаем "только для подписчиков" в названии
            name = item.get("TenderName", "").strip()
            if not name or "подписчик" in name.lower() or "только" in name.lower():
                continue

            # Парсим дату (TenderGuru возвращает "дд-мм-гггг" или ISO)
            deadline_str = item.get("EndTime", "")
            deadline = None
            days_left = None
            try:
                if deadline_str:
                    # Формат "дд-мм-гггг" (TenderGuru)
                    if len(deadline_str) == 10 and deadline_str[2] == "-" and deadline_str[5] == "-":
                        day, month, year = deadline_str.split("-")
                        deadline = datetime(int(year), int(month), int(day))
                    elif "T" in deadline_str:
                        deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                    else:
                        deadline = datetime.fromisoformat(deadline_str)
                    if deadline:
                        days_left = (deadline - datetime.now()).days
            except (ValueError, TypeError) as e:
                logger.debug(f"TenderGuru: не удалось распарсить дату '{deadline_str}': {e}")
                deadline = None

            # Чистим поля от "Только для подписчиков"
            def clean_field(val, fallback=""):
                if not val or "подписчик" in str(val).lower() or "tariffs" in str(val).lower():
                    return fallback
                return val

            def as_number(v):
                if v is None or v == "":
                    return None
                try:
                    return float(str(v).replace(" ", "").replace(",", "."))
                except Exception:
                    return None

            raw_link = clean_field(item.get("TenderLink"))
            inner_link = item.get("TenderLinkInner")
            external_url = raw_link if isinstance(raw_link, str) and raw_link.startswith("http") else inner_link

            formatted_item = {
                "id": item.get("ID"),
                "name": name,
                "customer": clean_field(item.get("Customer", "")),
                "region": clean_field(item.get("Region", "")),
                "budget": as_number(item.get("Price")),
                "deadline": deadline.isoformat() if deadline else None,
                "days_left": days_left,
                "platform": clean_field(item.get("Etp", "")),
                "law": item.get("Fz"),  # 44, 223, com
                "status": "active" if days_left is not None and days_left > 0 else "closed",
                "relevance": 100,
                "source": "tenderguru",
                "external_url": external_url,
                "inner_url": inner_link,
                "tender_num": clean_field(item.get("TenderNumOuter")),
                "category": item.get("Category", ""),
                "info": item.get("Info", ""),
                "published_date": item.get("Date"),  # дата публикации "дд-мм-гггг"
            }
            formatted.append(formatted_item)

        return {
            "total": len(formatted),
            "tenders": formatted,
            "page": 1,
        }
