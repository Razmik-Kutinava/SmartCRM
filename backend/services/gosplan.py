"""
ГосПлан API v2 - официальный API ЕИС Закупок
Полные данные по 44-ФЗ, 223-ФЗ, ПП РФ 615
"""

import httpx
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Тестовый сервер: 10 запросов/минуту бесплатно
GOSPLAN_TEST_URL = "https://v2test.gosplan.info"
GOSPLAN_PROD_URL = "https://v2.gosplan.info"


class GosplanAPI:
    def __init__(self, use_prod: bool = False):
        self.base_url = GOSPLAN_PROD_URL if use_prod else GOSPLAN_TEST_URL
        self.timeout = httpx.Timeout(30.0)
        self.headers = {"User-Agent": "SmartCRM/1.0"}

    async def search_purchases(
        self,
        kwords: str,
        fz: str = "44",  # 44, 223, или 615
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """
        Поиск закупок в ГосПлан API

        Args:
            kwords: Ключевые слова
            fz: Закон (44, 223, 615)
            limit: Количество результатов
            skip: Смещение

        Returns:
            Результаты поиска с метаданными
        """
        if fz == "44":
            endpoint = f"{self.base_url}/fz44/purchases"
        elif fz == "223":
            endpoint = f"{self.base_url}/fz223/purchases"
        elif fz == "615":
            endpoint = f"{self.base_url}/pprf615/purchases"
        else:
            endpoint = f"{self.base_url}/fz44/purchases"

        params = {
            "limit": min(limit, 100),  # API лимит
            "skip": skip,
            "q": kwords,  # ключевые слова для поиска
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                data = response.json()

                logger.debug(f"GosplanAPI raw response: {data}")

                # Парсим ответ - может быть список или словарь
                purchases = []
                total = 0
                if isinstance(data, dict):
                    purchases = data.get('data', []) or data.get('purchases', [])
                    total = data.get("total", len(purchases))
                elif isinstance(data, list):
                    purchases = data
                    total = len(data)

                logger.info(f"GosplanAPI: found {len(purchases)} purchases for '{kwords}'")

                return {
                    "source": "gosplan",
                    "fz": fz,
                    "total": total,
                    "limit": limit,
                    "offset": skip,
                    "purchases": purchases,
                    "metadata": {
                        "last_update": datetime.now().isoformat(),
                        "api_version": "2.3",
                        "data_delay_hours": 2,
                    }
                }

        except httpx.HTTPError as e:
            # str(e) может содержать сырой URL с внутренностями — в клиентский ответ не кладём.
            logger.error(f"GosplanAPI error: {type(e).__name__}: {e}")
            return {
                "source": "gosplan",
                "total": 0,
                "purchases": [],
                "error": "ГосПлан API временно недоступен",
            }

    @staticmethod
    def format_purchase(purchase: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматирование записи закупки из ГосПлан в стандартный формат

        Args:
            purchase: Сырая запись из API

        Returns:
            Форматированные данные
        """
        # Извлекаем основные данные из ГосПлан API v2
        purchase_number = purchase.get("purchase_number", "")
        object_info = purchase.get("object_info", "")
        max_price = purchase.get("max_price")
        collecting_finished_at = purchase.get("collecting_finished_at")

        customer_raw = purchase.get("customer")
        customer_name = ""
        customer_inn = ""
        if isinstance(customer_raw, dict):
            customer_name = str(customer_raw.get("name") or "")
            customer_inn = str(customer_raw.get("inn") or "")
        elif isinstance(customer_raw, str):
            customer_name = customer_raw

        customers = purchase.get("customers")
        if (not customer_name or customer_name.isdigit()) and isinstance(customers, list) and customers:
            customer_name = str(customers[0] or customer_name)
        if not customer_inn and isinstance(customers, list) and customers:
            first = str(customers[0] or "")
            if first.isdigit():
                customer_inn = first

        responsible = str(purchase.get("responsible") or "")
        if not customer_name:
            customer_name = responsible
        if not customer_inn and responsible.isdigit():
            customer_inn = responsible

        law_value = str(purchase.get("__law") or purchase.get("fz") or purchase.get("law") or "44")
        tender_id = purchase_number or purchase.get("id") or responsible
        tender_id = str(tender_id)

        return {
            "id": tender_id,
            "name": object_info or purchase.get("name", purchase.get("title", "")),
            "description": purchase.get("description", object_info or ""),
            "customer": customer_name,
            "customer_inn": customer_inn,
            "region": purchase.get("region", ""),
            "budget": max_price or purchase.get("price", {}).get("value"),
            "currency": purchase.get("currency_code", purchase.get("price", {}).get("currency", "RUB")),
            "deadline": collecting_finished_at or purchase.get("deadline"),
            "published_date": purchase.get("published_at", purchase.get("publishedDate")),
            "platform": "ГосПлан ЕИС",
            "law": law_value,
            "source": "gosplan",
            "external_url": f"https://zakupki.gov.ru/epz/order/notice/{purchase_number or tender_id}",
            # Полнота данных
            "data_completeness": {
                "has_description": bool(object_info or purchase.get("description")),
                "has_requirements": bool(purchase.get("requirements")),
                "has_docs": bool(purchase.get("docs", [])),
                "has_price": bool(max_price or purchase.get("price", {}).get("value")),
                "source_is_official": True,
            }
        }

    @staticmethod
    def get_data_gaps(purchase: Dict[str, Any]) -> List[str]:
        """
        Выявление недостающих данных для полного анализа

        Args:
            purchase: Данные закупки (из ГосПлан API v2)

        Returns:
            Список недостающей информации
        """
        gaps = []

        # ГосПлан v2 может не иметь всех полей
        if not purchase.get("object_info") and not purchase.get("description"):
            gaps.append("Полное описание закупки")
        if not purchase.get("requirements"):
            gaps.append("Технические требования")
        if not purchase.get("docs", []):
            gaps.append("Документация (ТЗ, договор)")
        if not purchase.get("max_price") and not purchase.get("price", {}).get("value"):
            gaps.append("НМЦК (начальная максимальная цена контракта)")
        if not purchase.get("collecting_finished_at") and not purchase.get("deadline"):
            gaps.append("Срок подачи заявок")
        if not purchase.get("customers") and not purchase.get("responsible") and not purchase.get("customer"):
            gaps.append("Информация о заказчике")

        return gaps
