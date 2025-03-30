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
    "GBP/USD": "https://www.poundsterlinglive.com/data/currencies/gbp-pairs/GBPUSD-exchange-rate",
    "EUR/USD": "https://www.reuters.com/markets/quote/EURUSD=X/"
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
            bid_container = xau_soup.find("div", class_="border-b border-ktc-borders")
            xau_bid = "N/A"
            if bid_container:
                bid_element = bid_container.find("h3", class_="font-mulish mb-[3px] text-4xl font-bold leading-normal tracking-[1px]")
                xau_bid = bid_element.text.strip() if bid_element else "N/A"
            ask_element = xau_soup.find("div", class_="mr-0.5 text-[19px] font-normal")
            xau_ask = ask_element.text.strip() if ask_element else "N/A"
            results["XAU/USD"] = {"bid": xau_bid, "ask": xau_ask}

            # Scrape GBP/USD from PoundSterlingLive
            gbp_response = requests.get(PAIRS["GBP/USD"], headers=headers, timeout=10)
            gbp_response.raise_for_status()
            gbp_soup = BeautifulSoup(gbp_response.content, "html.parser")
            gbp_table = gbp_soup.find("div", class_="quote-data")
            gbp_bid, gbp_ask = "N/A", "N/A"
            if gbp_table:
                rows = gbp_table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        label = cells[0].text.strip().lower()
                        if "bid" in label:
                            gbp_bid = cells[1].text.strip()
                        if "ask" in label or "offer" in label:  # Sometimes "Ask" is "Offer"
                            gbp_ask = cells[1].text.strip()
            results["GBP/USD"] = {"bid": gbp_bid, "ask": gbp_ask}

            # Scrape EUR/USD from Reuters
            # eur_response = requests.get(PAIRS["EUR/USD"], headers=headers, timeout=10)
            # eur_response.raise_for_status()
            # eur_soup = BeautifulSoup(eur_response.content, "html.parser")
            # eur_price_div = eur_soup.find("div", class_="ticker__price-details__2n8S")
            # eur_bid, eur_ask = "N/A", "N/A"
            # if eur_price_div:
            #     spans = eur_price_div.find_all("span")
            #     for i, span in enumerate(spans):
            #         text = span.text.strip().lower()
            #         if "bid" in text and i + 1 < len(spans):
            #             eur_bid = spans[i + 1].text.strip()
            #         if "ask" in text and i + 1 < len(spans):
            #             eur_ask = spans[i + 1].text.strip()
            # # Fallback: Reuters sometimes shows a single "Last" price
            # if eur_bid == "N/A" and eur_ask == "N/A":
            #     last_price = eur_soup.find("span", class_="ticker-price__price")
            #     if last_price:
            #         last = last_price.text.strip()
            #         eur_bid = last  # Approximate bid/ask if only last price is available
            #         eur_ask = last
            # results["EUR/USD"] = {"bid": eur_bid, "ask": eur_ask}

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