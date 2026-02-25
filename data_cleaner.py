import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self):
        self.stats = {
            "deals": {"missing_close_dates": 0, "missing_values": 0, "total_records": 0},
            "work_orders": {"delayed": 0, "missing_dates": 0, "incomplete": 0, "total_records": 0}
        }
        
    def _extract_column_dicts(self, items):
        """Convert monday column values into flat dicts."""
        rows = []
        for item in items:
            row = {"id": item["id"], "name": item["name"]}
            for col in item.get("column_values", []):
                title = col.get("column", {}).get("title")
                if title:
                    row[title] = col.get("text")
            rows.append(row)
        return rows

    def clean_deals_data(self, items):
        if not items:
            return pd.DataFrame()
            
        rows = self._extract_column_dicts(items)
        df = pd.DataFrame(rows)
        self.stats["deals"]["total_records"] = len(df)
        
        df.columns = [str(c).lower().strip().replace(' ', '_') for c in df.columns]
        
        expected_cols = ['sector', 'probability', 'deal_value', 'actual_close_date', 'tentative_close_date', 'stage']
        
        rename_map = {
            'sector/service': 'sector',
            'closure_probability': 'probability',
            'masked_deal_value': 'deal_value',
            'close_date_(a)': 'actual_close_date',
            'tentative_close_date': 'tentative_close_date',
            'deal_stage': 'stage'
        }
        df.rename(columns=rename_map, inplace=True)
        
        for col in expected_cols:
            if col not in df.columns:
                 plausible = [c for c in df.columns if col.replace('_', '') in c.replace('_', '')]
                 if plausible:
                     df.rename(columns={plausible[0]: col}, inplace=True)
                 else:
                     df[col] = np.nan

        df['sector'] = df['sector'].astype(str).str.strip().str.title()
        df['sector'] = df['sector'].replace('Nan', 'Unknown', regex=False)
        
        def parse_prob(x):
            x = str(x).lower().strip()
            if 'high' in x: return 0.8
            if 'medium' in x: return 0.5
            if 'low' in x: return 0.2
            try:
                if '%' in x:
                    return float(x.replace('%', '')) / 100.0
                return float(x)
            except:
                return 0.1
                
        df['probability_score'] = df['probability'].apply(parse_prob)
        
        missing_val_mask = df['deal_value'].isna() | (df['deal_value'] == '') | (df['deal_value'] == 'None') | (df['deal_value'] == 'nan')
        self.stats["deals"]["missing_values"] = int(missing_val_mask.sum())
        
        df['deal_value'] = pd.to_numeric(df['deal_value'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        df['deal_value'].fillna(0, inplace=True)
        
        df['close_date'] = df['actual_close_date']
        df['close_date'] = df['close_date'].fillna(df['tentative_close_date'])
        
        missing_dates_mask = df['close_date'].isna() | (df['close_date'] == '') | (df['close_date'] == 'None') | (df['close_date'] == 'nan')
        self.stats["deals"]["missing_close_dates"] = int(missing_dates_mask.sum())
        
        df['close_date'] = pd.to_datetime(df['close_date'], errors='coerce')
        
        df['stage'] = df['stage'].astype(str).str.strip()
        df['stage'] = df['stage'].replace({'nan': 'Unknown', 'None': 'Unknown', '': 'Unknown'})
        
        return df

    def clean_work_orders_data(self, items):
        if not items:
            return pd.DataFrame()
            
        rows = self._extract_column_dicts(items)
        df = pd.DataFrame(rows)
        self.stats["work_orders"]["total_records"] = len(df)
        
        df.columns = [str(c).lower().strip().replace(' ', '_') for c in df.columns]
        
        expected_cols = ['execution_status', 'delivery_date', 'billing_status', 'sector']
        
        if 'data_delivery_date' in df.columns:
            df.rename(columns={'data_delivery_date': 'delivery_date'}, inplace=True)
        elif 'probable_end_date' in df.columns:
            df.rename(columns={'probable_end_date': 'delivery_date'}, inplace=True)
            
        for col in expected_cols:
            if col not in df.columns:
                plausible = [c for c in df.columns if col.replace('_', '') in c.replace('_', '')]
                if plausible:
                    df.rename(columns={plausible[0]: col}, inplace=True)
                else:
                    df[col] = np.nan

        df['execution_status'] = df['execution_status'].astype(str).str.strip().str.title()
        
        missing_dates = df['delivery_date'].isna() | (df['delivery_date'] == '') | (df['delivery_date'] == 'None') | (df['delivery_date'] == 'nan')
        self.stats["work_orders"]["missing_dates"] = int(missing_dates.sum() if isinstance(missing_dates.sum(), (int, float, np.number)) else missing_dates.sum().iloc[0] if not missing_dates.empty else 0)
        df['delivery_date'] = pd.to_datetime(df['delivery_date'], errors='coerce')
        
        now = pd.Timestamp.now()
        df['is_delayed'] = (df['delivery_date'] < now) & (~df['execution_status'].astype(str).str.lower().str.contains('done|complete|delivered', regex=True, na=False))
        self.stats["work_orders"]["delayed"] = int(df['is_delayed'].sum())
        
        df['billing_status'] = df['billing_status'].astype(str).str.strip().str.title()
        
        incomplete_mask = df['execution_status'].astype(str).str.contains('Nan|Unknown|None', case=False) | df['sector'].astype(str).str.contains('Nan|Unknown|None', case=False)
        self.stats["work_orders"]["incomplete"] = int(incomplete_mask.sum())
        
        return df
        
    def get_data_quality_report(self):
        return self.stats
