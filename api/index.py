# api/index.py
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

ua = UserAgent()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Rotate user agent
        headers = {"User-Agent": ua.random}
        url = "https://www.kitco.com/charts/livegold.html"

        try:
            # Fetch the webpage
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Find bid price
            bid_container = soup.find("div", class_="border-b border-ktc-borders")
            bid_price = None
            if bid_container:
                bid_element = bid_container.find("h3", class_="font-mulish mb-[3px] text-4xl font-bold leading-normal tracking-[1px]")
                bid_price = bid_element.text.strip() if bid_element else "N/A"

            # Find ask price
            ask_element = soup.find("div", class_="mr-0.5 text-[19px] font-normal")
            ask_price = ask_element.text.strip() if ask_element else "N/A"

            # Get current timestamp
            timestamp = datetime.utcnow().isoformat() + "Z"  # ISO 8601 format with UTC

            # Prepare JSON response
            if bid_price != "N/A" and ask_price != "N/A":
                data = {
                    "bid": bid_price,
                    "ask": ask_price,
                    "timestamp": timestamp
                }
            else:
                data = {
                    "error": "Couldn’t fetch data. Check selectors or site availability.",
                    "timestamp": timestamp
                }

            # Send response as JSON
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))

        except requests.RequestException as e:
            # Error response
            error_data = {
                "error": f"Error fetching data: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(error_data).encode("utf-8"))