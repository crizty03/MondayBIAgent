import pandas as pd
import numpy as np

class BIEngine:
    def __init__(self, deals_df, work_orders_df):
        self.deals_df = deals_df
        self.work_orders_df = work_orders_df

    def deals_kpis(self, timeframe=None, sector=None):
        df = self.deals_df.copy()
        if df.empty:
            return {}
            
        if sector and sector.lower() != 'all':
            df = df[df['sector'].str.lower() == sector.lower()]
            
        if timeframe and timeframe.lower() != 'all':
            now = pd.Timestamp.now()
            if 'month' in timeframe.lower() or 'this_month' in timeframe.lower():
                df = df[df['close_date'] >= now - pd.DateOffset(months=1)]
            elif 'quarter' in timeframe.lower() or 'this_quarter' in timeframe.lower():
                df = df[df['close_date'] >= now - pd.DateOffset(months=3)]
            elif 'year' in timeframe.lower() or 'this_year' in timeframe.lower():
                df = df[df['close_date'] >= now - pd.DateOffset(years=1)]

        df['stage'] = df['stage'].astype(str).str.strip().str.lower()
        
        closed_mask = df['stage'].str.contains('closed|won', regex=True, na=False)
        closed_revenue = float(df.loc[closed_mask, 'deal_value'].sum())
        
        open_mask = df['stage'].str.contains('open|hold', regex=True, na=False)
        open_pipeline_value = float(df.loc[open_mask, 'deal_value'].sum())
        
        df['weighted_value'] = df['deal_value'] * df['probability_score']
        weighted_pipeline = float(df.loc[open_mask, 'weighted_value'].sum())
        
        closed_lost = int(df['stage'].str.contains('Lost|Cancelled', case=False, na=False).sum())
        closed_won = int(closed_mask.sum())
        total_closed = closed_won + closed_lost
        win_rate = float(closed_won / total_closed) if total_closed > 0 else 0.0
        
        avg_deal_size = float(df.loc[closed_mask, 'deal_value'].mean()) if closed_won > 0 else 0.0
        
        now = pd.Timestamp.now()
        closing_soon_mask = open_mask & (df['close_date'] >= now) & (df['close_date'] <= now + pd.Timedelta(days=30))
        closing_soon_val = float(df.loc[closing_soon_mask, 'deal_value'].sum())
        
        sector_dist = {str(k): float(v) for k, v in df.groupby('sector')['deal_value'].sum().to_dict().items()}
        stage_dist = {str(k): int(v) for k, v in df['stage'].value_counts().to_dict().items()}

        return {
            "closed_revenue": closed_revenue,
            "open_pipeline_value": open_pipeline_value,
            "weighted_pipeline": weighted_pipeline,
            "win_rate": win_rate,
            "average_deal_size": avg_deal_size,
            "closing_next_30_days_value": closing_soon_val,
            "revenue_by_sector": sector_dist,
            "stage_distribution": stage_dist
        }

    def work_orders_kpis(self, timeframe=None, sector=None):
        df = self.work_orders_df.copy()
        if df.empty:
            return {}
            
        if sector and sector.lower() != 'all':
            df = df[df['sector'].str.lower() == sector.lower()]
            
        active_mask = ~df['execution_status'].str.contains('Done|Complete|Delivered|Cancelled', case=False, na=False)
        active_projects = int(active_mask.sum())
        
        delayed_projects = 0
        if 'is_delayed' in df.columns:
            delayed_projects = int(df['is_delayed'].sum())
        
        sector_load = {str(k): int(v) for k, v in df[active_mask].groupby('sector').size().to_dict().items()}
        
        return {
            "active_projects": active_projects,
            "delayed_projects": delayed_projects,
            "execution_load_by_sector": sector_load
        }
        
    def cross_board_intelligence(self, timeframe=None, sector=None):
        deals = self.deals_kpis(timeframe=timeframe, sector=sector)
        wo = self.work_orders_kpis(timeframe=timeframe, sector=sector)
        
        if not deals or not wo:
            return {"insight": "Insufficient data for cross-board intelligence."}
            
        open_pipeline = deals.get("open_pipeline_value", 0)
        active_projects = wo.get("active_projects", 0)
        delayed_projects = wo.get("delayed_projects", 0)
        
        insight = "Operational capacity seems healthy."
        is_overloaded = False
        if delayed_projects > 0 and (delayed_projects / max(active_projects, 1)) > 0.3:
            insight = f"Warning: {delayed_projects} projects delayed. Operations are overloaded."
            is_overloaded = True
            
        all_deals = self.deals_kpis()
        all_wo = self.work_orders_kpis()
        
        pipe_ratio = 1.0
        active_ratio = 1.0
        
        if sector and sector.lower() != 'all':
            pipe_ratio = open_pipeline / max(all_deals.get("open_pipeline_value", 1), 1)
            active_ratio = active_projects / max(all_wo.get("active_projects", 1), 1)
            
            if pipe_ratio > 0.4 and active_ratio > 0.4:
                insight += f" The {sector} sector represents {pipe_ratio:.1%} of pipeline and {active_ratio:.1%} of active work. High concentration risk."
            elif pipe_ratio > 0.4 and active_ratio < 0.2:
                insight += f" The {sector} sector is an upcoming wave ({pipe_ratio:.1%} of pipeline) but current execution load is low."
                
        return {
            "pipeline_ratio": float(pipe_ratio),
            "active_ratio": float(active_ratio),
            "is_overloaded": is_overloaded,
            "strategic_insight": insight
        }
