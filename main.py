from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from monday_client import MondayClient
from data_cleaner import DataCleaner
from bi_engine import BIEngine
from query_parser import QueryParser
from report_generator import ReportGenerator

app = FastAPI(title="Monday BI Agent API")

monday_client = MondayClient()
query_parser = QueryParser()

class AppState:
    deals_df = None
    work_orders_df = None
    data_cleaner = None
    bi_engine = None
    last_fetch = None

state = AppState()

def refresh_data():
    raw_deals = monday_client.fetch_board_data("Deals")
    raw_wo = monday_client.fetch_board_data("Work Orders")
    
    cleaner = DataCleaner()
    deals_df = cleaner.clean_deals_data(raw_deals)
    wo_df = cleaner.clean_work_orders_data(raw_wo)
    
    state.deals_df = deals_df
    state.work_orders_df = wo_df
    state.data_cleaner = cleaner
    state.bi_engine = BIEngine(deals_df, wo_df)
    state.last_fetch = pd.Timestamp.now()

class QueryRequest(BaseModel):
    query: str

@app.on_event("startup")
def startup_event():
    if monday_client.api_key:
         try:
             refresh_data()
         except Exception as e:
             print(f"Startup fetch failed: {e}")

@app.post("/api/chat")
def chat_endpoint(req: QueryRequest):
        
    if state.bi_engine is None:
        try:
            refresh_data()
        except Exception as e:
             return {"response": f"Failed to fetch data from Monday.com: {e}", "type": "error"}

    query = req.query
    intent = query_parser.parse_query(query)
    print("DEBUG INTENT:", intent)
    
    if "error" in intent:
        return {"response": "Error parsing query: " + intent["error"], "type": "error"}
        
    metric_type = intent.get("metric_type", "ambiguous")
    sector = intent.get("sector", "all")
    timeframe = intent.get("timeframe", "all")
    
    if metric_type == "ambiguous":
        return {"response": "Could you please clarify? I can answer about revenue, pipeline health, operations, or prepare a leadership update.", "type": "clarification"}
        
    if metric_type == "leadership_update":
        rg = ReportGenerator(state.bi_engine, state.data_cleaner)
        report = rg.generate_leadership_update(timeframe=timeframe, sector=sector)
        return {"response": report, "type": "report"}
        
    response_text = ""
    deals_kpis = state.bi_engine.deals_kpis(timeframe=timeframe, sector=sector)
    wo_kpis = state.bi_engine.work_orders_kpis(timeframe=timeframe, sector=sector)
    
    warnings = []
    dq = state.data_cleaner.get_data_quality_report()
    if dq['deals']['missing_close_dates'] > 0:
        warning_pct = dq['deals']['missing_close_dates'] / max(dq['deals']['total_records'], 1)
        if warning_pct > 0.1:
            warnings.append(f"⚠ {warning_pct:.0%} of deals are missing close dates. Timeframe filters might be inaccurate.")
            
    if metric_type in ["revenue", "sales"]:
        val = deals_kpis.get('closed_revenue', 0)
        response_text = f"The closed revenue is ${val:,.2f}."
    elif metric_type in ["pipeline", "pipeline_health"]:
        val = deals_kpis.get('open_pipeline_value', 0)
        w_val = deals_kpis.get('weighted_pipeline', 0)
        response_text = f"The open pipeline value is ${val:,.2f}, with a weighted value of ${w_val:,.2f}."
    elif metric_type == "win_rate":
        val = deals_kpis.get('win_rate', 0)
        response_text = f"The win rate is {val:.1%}."
    elif metric_type in ["active_projects", "operations", "operational_metrics"]:
        active = wo_kpis.get('active_projects', 0)
        delayed = wo_kpis.get('delayed_projects', 0)
        response_text = f"There are {active} active projects, with {delayed} currently delayed."
    elif metric_type == "cross_board_insights" or "overload" in query.lower():
        insight = state.bi_engine.cross_board_intelligence(timeframe=timeframe, sector=sector)
        response_text = f"Cross-board analysis: {insight.get('strategic_insight', '')}"
    elif metric_type == "general_health":
         rev = deals_kpis.get('closed_revenue', 0)
         active = wo_kpis.get('active_projects', 0)
         response_text = f"Overall health: Revenue is ${rev:,.2f} and we are handling {active} active projects."
    else:
        response_text = f"I pulled the metrics. Revenue: ${deals_kpis.get('closed_revenue', 0):,.2f}. Active projects: {wo_kpis.get('active_projects', 0)}."

    if warnings:
        response_text += "\n\n" + "\n".join(warnings)
        
    return {
        "response": response_text,
        "type": "text",
        "intent": intent,
        "raw_data": {"deals": deals_kpis, "work_orders": wo_kpis}
    }

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
