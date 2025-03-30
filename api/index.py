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
    "XAU/USD": "https://www.kitco.com/charts/livegold.html",  # Kitco for XAU/USD
    "GBP/USD": "https://www.fxstreet.com/rates-charts/forex-rates",  # FXStreet for GBP/USD and EUR/USD
    "EUR/USD": "https://www.fxstreet.com/rates-charts/forex-rates"
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

            # Scrape GBP/USD and EUR/USD from FXStreet
            fx_response = requests.get(PAIRS["GBP/USD"], headers=headers, timeout=10)
            fx_response.raise_for_status()
            fx_soup = BeautifulSoup(fx_response.content, "html.parser")

            # Find all table rows
            rows = fx_soup.find_all("tr")

            # GBP/USD
            gbp_bid, gbp_ask = "N/A", "N/A"
            for row in rows:
                pair_cell = row.find("td", id=lambda x: x and "Asset" in x)
                if pair_cell and "GBP/USD" in pair_cell.text.strip():
                    bid_cell = row.find("td", id=lambda x: x and "Bid" in x)
                    ask_cell = row.find("td", id=lambda x: x and "Ask" in x)
                    gbp_bid = bid_cell.text.strip() if bid_cell else "N/A"
                    gbp_ask = ask_cell.text.strip() if ask_cell else "N/A"
                    break
            results["GBP/USD"] = {"bid": gbp_bid, "ask": gbp_ask}

            # EUR/USD
            eur_bid, eur_ask = "N/A", "N/A"
            for row in rows:
                pair_cell = row.find("td", id=lambda x: x and "Asset" in x)
                if pair_cell and "EUR/USD" in pair_cell.text.strip():
                    bid_cell = row.find("td", id=lambda x: x and "Bid" in x)
                    ask_cell = row.find("td", id=lambda x: x and "Ask" in x)
                    eur_bid = bid_cell.text.strip() if bid_cell else "N/A"
                    eur_ask = ask_cell.text.strip() if ask_cell else "N/A"
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