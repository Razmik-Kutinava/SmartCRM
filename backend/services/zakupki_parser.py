"""
Парсер закупок с zakupki.gov.ru (открытый источник, без авторизации)
Использует Selenium для JavaScript rendering
"""

import hashlib
import logging
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ZAKUPKI_SEARCH_URL = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"

# Try to import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
    logger.warning(f"Selenium not installed - zakupki.gov.ru scraping disabled: {e}")


class ZakupkiParser:
    def __init__(self, use_selenium: bool = False):
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        if not SELENIUM_AVAILABLE and use_selenium:
            logger.warning("Selenium requested but not available. Install: pip install selenium")

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def search_tenders(
        self,
        kwords: str,
        law: str = "44",  # 44 или 223
        region: str = None,
        price_min: int = None,
        price_max: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Поиск тендеров на zakupki.gov.ru

        Args:
            kwords: Ключевые слова
            law: "44" или "223"
            region: Регион (опционально)
            price_min: Минимальная цена
            price_max: Максимальная цена

        Returns:
            Список найденных тендеров
        """
        if not SELENIUM_AVAILABLE:
            logger.warning(
                "ZakupkiParser: Selenium not available. "
                "zakupki.gov.ru requires JavaScript rendering. "
                "Install Selenium: pip install selenium"
            )
            return []

        if not self.use_selenium:
            logger.info("ZakupkiParser: Selenium disabled")
            return []

        driver = None
        try:
            # Setup Chrome options for headless mode
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")

            # Create driver with automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Build URL with parameters
            params = {
                "searchString": kwords,
                "fz44": "on" if law == "44" else "off",
                "fz223": "on" if law == "223" else "off",
                "pageNumber": 1,
            }

            if price_min:
                params["priceFromGeneral"] = price_min
            if price_max:
                params["priceToGeneral"] = price_max

            # Build query string
            from urllib.parse import urlencode
            query_string = urlencode(params)
            url = f"{ZAKUPKI_SEARCH_URL}?{query_string}"

            logger.info(f"ZakupkiParser: Loading {url}")
            driver.get(url)

            # Wait for page to load with timeout fallback
            try:
                wait = WebDriverWait(driver, 10)
                # Wait for either table rows or search results container
                wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))
                logger.info("ZakupkiParser: Table rows found")
            except Exception as wait_error:
                logger.warning(f"ZakupkiParser: Timeout waiting for table rows: {wait_error}. Continuing with page source as-is...")

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            tenders = []

            # Find table rows
            rows = soup.find_all("tr")
            rows = [r for r in rows if r.find("a")]  # Only rows with links

            logger.info(f"ZakupkiParser: found {len(rows)} rows in HTML after parsing")

            for row in rows[:50]:  # Take first 50
                try:
                    cells = row.find_all("td")
                    if len(cells) < 3:
                        continue

                    tender_link = cells[0].find("a")
                    if not tender_link:
                        continue

                    tender_name = tender_link.text.strip()
                    tender_url = tender_link.get("href", "")

                    customer = cells[1].text.strip() if len(cells) > 1 else ""

                    price_str = cells[2].text.strip() if len(cells) > 2 else ""
                    try:
                        price = int(price_str.replace(" ", "").split(",")[0]) if price_str and price_str != "—" else None
                    except (ValueError, AttributeError):
                        price = None

                    deadline_str = cells[3].text.strip() if len(cells) > 3 else ""
                    region_name = cells[4].text.strip() if len(cells) > 4 else ""

                    # Стабильный ID между процессами (builtin hash() рандомизирован PYTHONHASHSEED).
                    stable_id = hashlib.sha1(tender_name.encode("utf-8")).hexdigest()[:16]

                    tender_data = {
                        "id": f"zakupki_{stable_id}",
                        "name": tender_name,
                        "customer": customer,
                        "budget": price,
                        "deadline": deadline_str,
                        "region": region_name,
                        "platform": "zakupki.gov.ru",
                        "law": law,
                        "source": "zakupki",
                        "external_url": f"https://zakupki.gov.ru{tender_url}" if tender_url else "",
                    }

                    tenders.append(tender_data)
                except Exception as e:
                    logger.debug(f"ZakupkiParser: Error parsing row: {e}")
                    continue

            logger.info(f"ZakupkiParser: found {len(tenders)} tenders for '{kwords}'")
            return tenders

        except Exception as e:
            logger.error(f"ZakupkiParser error: {type(e).__name__}: {e}", exc_info=True)
            return []
        finally:
            if driver:
                try:
                    logger.info("ZakupkiParser: Closing browser")
                    driver.quit()
                except Exception as cleanup_error:
                    logger.warning(f"ZakupkiParser: Error closing browser: {cleanup_error}")
