import os
from monday_client import MondayClient
client = MondayClient()
client.api_key = os.environ.get("MONDAY_API_KEY")
import logging
logging.basicConfig(level=logging.INFO)

print("Fetching Deals")
deals = client.fetch_board_data("Deals")
print(f"Got {len(deals) if deals else 0} deal rows")

print("Fetching Work Orders")
wo = client.fetch_board_data("Work Orders")
print(f"Got {len(wo) if wo else 0} work order rows")
