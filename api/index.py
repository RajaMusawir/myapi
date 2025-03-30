# api/index.py
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

ua = UserAgent()

# URLs for each pair
PAIRS = {
    "XAU/USD": "https://www.kitco.com/charts/livegold.html",
    "GBP/USD": "https://www.dailyfx.com/forex-rates",
    "EUR/USD": "https://www.dailyfx.com/forex-rates"
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Rotate user agent
        headers = {"User-Agent": ua.random}
        
        # Store results
        results = {}
        timestamp = datetime.utcnow().isoformat() + "Z"

        try:
            # Scrape XAU/USD from Kitco
            xau_response = requests.get(PAIRS["XAU/USD"], headers=headers, timeout=10)
            xau_response.raise_for_status()
            xau_soup = BeautifulSoup(xau_response.content, "html.parser")

            # XAU/USD bid
            bid_container = xau_soup.find("div", class_="border-b border-ktc-borders")
            xau_bid = "N/A"
            if bid_container:
                bid_element = bid_container.find("h3", class_="font-mulish mb-[3px] text-4xl font-bold leading-normal tracking-[1px]")
                xau_bid = bid_element.text.strip() if bid_element else "N/A"

            # XAU/USD ask
            ask_element = xau_soup.find("div", class_="mr-0.5 text-[19px] font-normal")
            xau_ask = ask_element.text.strip() if ask_element else "N/A"

            results["XAU/USD"] = {"bid": xau_bid, "ask": xau_ask}

            # Scrape GBP/USD and EUR/USD from DailyFX
            dfx_response = requests.get(PAIRS["GBP/USD"], headers=headers, timeout=10)
            dfx_response.raise_for_status()
            dfx_soup = BeautifulSoup(dfx_response.content, "html.parser")

            # Find the rates table
            table = dfx_soup.find("table", class_="dfx-tableRates")
            if not table:
                raise Exception("DailyFX rates table not found")

            # GBP/USD
            gbp_bid, gbp_ask = "N/A", "N/A"
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 3 and "GBP/USD" in cells[0].text.strip():
                    gbp_bid = cells[1].text.strip()  # Bid
                    gbp_ask = cells[2].text.strip()  # Ask
                    break
            results["GBP/USD"] = {"bid": gbp_bid, "ask": gbp_ask}

            # EUR/USD
            eur_bid, eur_ask = "N/A", "N/A"
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 3 and "EUR/USD" in cells[0].text.strip():
                    eur_bid = cells[1].text.strip()  # Bid
                    eur_ask = cells[2].text.strip()  # Ask
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

        except requests.RequestException as e:
            error_data = {
                "error": f"Error fetching data: {str(e)}",
                "timestamp": timestamp
            }
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(error_data).encode("utf-8"))
        except Exception as e:
            error_data = {
                "error": f"Parsing error: {str(e)}",
                "timestamp": timestamp
            }
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(error_data).encode("utf-8"))