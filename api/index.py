# api/index.py
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from http.server import BaseHTTPRequestHandler

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

            # Prepare response
            if bid_price and ask_price:
                result = f"Bid: {bid_price} USD | Ask: {ask_price} USD"
            else:
                result = "Couldn’t fetch data. Check selectors or site availability."

            # Send response
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        except requests.RequestException as e:
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error fetching data: {str(e)}".encode("utf-8"))
