# api/index.py
import json
from http.server import BaseHTTPRequestHandler
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import SB  # Simplifies headless Chrome setup

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Store results
        results = {}
        timestamp = datetime.utcnow().isoformat() + "Z"

        try:
            # Set up Selenium with headless Chrome
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            # Use SeleniumBase for easier Chrome setup
            with SB(uc=True, headless=True, driver_args=chrome_options) as driver:
                # Scrape XAU/USD from Kitco
                driver.get("https://www.kitco.com/charts/livegold.html")
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "border-b"))
                )
                xau_bid_elem = driver.find_element(By.CSS_SELECTOR, "div.border-b h3.font-mulish")
                xau_ask_elem = driver.find_element(By.CSS_SELECTOR, "div.mr-0.5.text-[19px]")
                xau_bid = xau_bid_elem.text.strip() if xau_bid_elem else "N/A"
                xau_ask = xau_ask_elem.text.strip() if xau_ask_elem else "N/A"
                results["XAU/USD"] = {"bid": xau_bid, "ask": xau_ask}

                # Scrape GBP/USD and EUR/USD from FXStreet
                driver.get("https://www.fxstreet.com/rates-charts/forex-rates")
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "tbody"))
                )
                rows = driver.find_elements(By.TAG_NAME, "tr")

                # GBP/USD
                gbp_bid, gbp_ask = "N/A", "N/A"
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4 and "GBP/USD" in cells[0].text.strip():
                        gbp_bid = cells[2].text.strip()  # Bid
                        gbp_ask = cells[3].text.strip()  # Ask
                        break
                results["GBP/USD"] = {"bid": gbp_bid, "ask": gbp_ask}

                # EUR/USD
                eur_bid, eur_ask = "N/A", "N/A"
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4 and "EUR/USD" in cells[0].text.strip():
                        eur_bid = cells[2].text.strip()  # Bid
                        eur_ask = cells[3].text.strip()  # Ask
                        break
                results["EUR/USD"] = {"bid": eur_bid, "ask": eur_ask}

            # Prepare JSON response
            data = {
                "data": results,
                "timestamp": timestamp
            }
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))

        except Exception as e:
            error_data = {
                "error": f"Error fetching data: {str(e)}",
                "timestamp": timestamp
            }
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(error_data).encode("utf-8"))