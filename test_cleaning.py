import os
import pandas as pd
from monday_client import MondayClient
from data_cleaner import DataCleaner
import logging
logging.basicConfig(level=logging.INFO)

client = MondayClient()
client.api_key = os.environ.get("MONDAY_API_KEY")

deals = client.fetch_board_data("Deals")
cleaner = DataCleaner()
deals_rows = cleaner._extract_column_dicts(deals)
print("Deals columns:", list(deals_rows[0].keys()) if deals_rows else "Empty")

df = cleaner.clean_deals_data(deals)
print("Cleaned Deals Data:\n", df.head(3))
