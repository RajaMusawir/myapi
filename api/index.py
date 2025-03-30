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
    "GBP/USD": "https://www1.oanda.com/currency/live-exchange-rates/",
    "EUR/USD": "https://www1.oanda.com/currency/live-exchange-rates/"
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

            # Scrape GBP/USD and EUR/USD from OANDA
            oanda_response = requests.get(PAIRS["GBP/USD"], headers=headers, timeout=10)
            oanda_response.raise_for_status()
            oanda_soup = BeautifulSoup(oanda_response.content, "html.parser")

            # Find all tables with class cc_live_rates22
            tables = oanda_soup.find_all("table", class_="cc_live_rates22")
            if not tables:
                raise Exception("OANDA rates table not found")

            # GBP/USD
            gbp_bid, gbp_ask = "N/A", "N/A"
            for table in tables:
                for row in table.find("tbody").find_all("tr"):
                    cells = row.find_all("td")
                    if len(cells) == 3 and "GBP/USD" in cells[0].text.strip():
                        # Bid: concatenate parts
                        bid_parts = cells[1].find("div", class_="cc_live_rates11").find_all("div")
                        gbp_bid = "".join(part.text.strip() for part in bid_parts)
                        # Ask: concatenate parts
                        ask_parts = cells[2].find("div", class_="cc_live_rates11").find_all("div")
                        gbp_ask = "".join(part.text.strip() for part in ask_parts)
                        break
            results["GBP/USD"] = {"bid": gbp_bid, "ask": gbp_ask}

            # EUR/USD
            eur_bid, eur_ask = "N/A", "N/A"
            for table in tables:
                for row in table.find("tbody").find_all("tr"):
                    cells = row.find_all("td")
                    if len(cells) == 3 and "EUR/USD" in cells[0].text.strip():
                        # Bid: concatenate parts
                        bid_parts = cells[1].find("div", class_="cc_live_rates11").find_all("div")
                        eur_bid = "".join(part.text.strip() for part in bid_parts)
                        # Ask: concatenate parts
                        ask_parts = cells[2].find("div", class_="cc_live_rates11").find_all("div")
                        eur_ask = "".join(part.text.strip() for part in ask_parts)
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