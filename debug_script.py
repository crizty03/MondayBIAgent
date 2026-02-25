import os
import pandas as pd
from monday_client import MondayClient
from data_cleaner import DataCleaner

client = MondayClient()
client.api_key = os.environ.get("MONDAY_API_KEY")

print("--- STEP 1: Fetching API Data ---")
deals = client.fetch_board_data("Deals")
print(f"Total Deals Fetched: {len(deals)}")
wo = client.fetch_board_data("Work")
print(f"Total Work Orders Fetched: {len(wo)}")

print("\n--- Deals First 5 Rows ---")
for d in deals[:5]:
    print(d['id'], d['name'])
    
print("\n--- Work Orders First 5 Rows ---")
for w in wo[:5]:
    print(w['id'], w['name'])

cleaner = DataCleaner()
d_rows = cleaner._extract_column_dicts(deals)
df = pd.DataFrame(d_rows)

print("\n--- Unique Values ---")
print("Deal Statuses:", df['Deal Status'].unique() if 'Deal Status' in df else "Missing 'Deal Status' col")
w_rows = cleaner._extract_column_dicts(wo)
wdf = pd.DataFrame(w_rows)
print("Execution Statuses:", wdf['Execution Status'].unique() if 'Execution Status' in wdf else "Missing 'Execution Status' col")

print("\n--- STEP 2: Inspecting Column Structure ---")
if deals:
    print("Sample Deal column values:")
    for c in deals[0]['column_values']:
        if c['column']['title'] in ['Deal Status', 'Masked Deal value', 'Close Date (A)']:
            print(f"Title: {c['column']['title']}")
            print(f"  text: {c.get('text')}")
            print(f"  value: {c.get('value')}")
            
print("\n--- STEP 3: Validate Cleaning Layer ---")
clean_d = cleaner.clean_deals_data(deals)
print("Missing deal values:", clean_d['deal_value'].isna().sum())
print("Missing close dates:", clean_d['close_date'].isna().sum())

print("\n--- STEP 4 & 5: Filtering and Metrics ---")
clean_d['stage'] = clean_d['stage'].astype(str).str.strip().str.lower()
closed_mask = clean_d['stage'].str.contains('closed|won', na=False)
open_mask = clean_d['stage'].str.contains('open|hold', na=False)

print("Total Deals:", len(clean_d))
print("Closed Deals:", closed_mask.sum())
print("Open Deals:", open_mask.sum())

rev = clean_d.loc[closed_mask, 'deal_value'].sum()
pipe = clean_d.loc[open_mask, 'deal_value'].sum()
print(f"Closed Revenue: ${rev:,.2f}")
print(f"Open Pipeline: ${pipe:,.2f}")

clean_w = cleaner.clean_work_orders_data(wo)
clean_w['execution_status'] = clean_w['execution_status'].astype(str).str.strip().str.lower()
active_mask = ~clean_w['execution_status'].str.contains('done|complete|delivered|cancelled', na=False)
print("Total Work Orders:", len(clean_w))
print("Active Projects:", active_mask.sum())
