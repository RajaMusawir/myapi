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
    "XAU/USD": "https://www.kitco.com/charts/livegold.html",           # Kitco for XAU/USD
    "GBP/USD": "https://www.investing.com/currencies/gbp-usd",        # Investing.com for GBP/USD
    "EUR/USD": "https://www.investing.com/currencies/eur-usd"         # Investing.com for EUR/USD
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

            # Scrape GBP/USD from Investing.com
            gbp_response = requests.get(PAIRS["GBP/USD"], headers=headers, timeout=10)
            gbp_response.raise_for_status()
            gbp_soup = BeautifulSoup(gbp_response.content, "html.parser")

            # GBP/USD bid and ask (Investing.com uses spans with data-test attributes)
            gbp_bid_element = gbp_soup.find("span", {"data-test": "instrument-price-bid"})
            gbp_ask_element = gbp_soup.find("span", {"data-test": "instrument-price-ask"})
            gbp_bid = gbp_bid_element.text.strip() if gbp_bid_element else "N/A"
            gbp_ask = gbp_ask_element.text.strip() if gbp_ask_element else "N/A"
            results["GBP/USD"] = {"bid": gbp_bid, "ask": gbp_ask}

            # Scrape EUR/USD from Investing.com
            eur_response = requests.get(PAIRS["EUR/USD"], headers=headers, timeout=10)
            eur_response.raise_for_status()
            eur_soup = BeautifulSoup(eur_response.content, "html.parser")

            # EUR/USD bid and ask
            eur_bid_element = eur_soup.find("span", {"data-test": "instrument-price-bid"})
            eur_ask_element = eur_soup.find("span", {"data-test": "instrument-price-ask"})
            eur_bid = eur_bid_element.text.strip() if eur_bid_element else "N/A"
            eur_ask = eur_ask_element.text.strip() if eur_ask_element else "N/A"
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