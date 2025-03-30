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
    "GBP/USD": "https://www.poundsterlinglive.com/data/currencies/gbp-pairs/GBPUSD-exchange-rate"
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
            gbp_table = gbp_soup.find("table", class_="table data_stat_table")
            gbp_bid, gbp_ask = "N/A", "N/A"
            if gbp_table:
                rows = gbp_table.find_all("tr")
                for row in rows:
                    if row.find("div", class_="col-xs-8"):
                        label = row.find("div", class_="col-xs-8").text.strip().lower()
                        if "bid" in label:
                            bid_div = row.find("div", class_="col-xs-4 bid_rate")
                            gbp_bid = bid_div.text.strip() if bid_div else "N/A"
                        if "ask" in label:
                            ask_div = row.find("div", class_="col-xs-4")
                            gbp_ask = ask_div.text.strip() if ask_div else "N/A"
            results["GBP/USD"] = {"bid": gbp_bid, "ask": gbp_ask}

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