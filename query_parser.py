import os
import json
import logging
from google import genai
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class QueryIntent(BaseModel):
    metric_type: str = Field(description='"revenue", "pipeline", "active_projects", "win_rate", "leadership_update", "cross_board_insights", "general_health", "ambiguous", etc.')
    sector: str = Field(description='The specific sector mentioned, or "all" if none.', default="all")
    timeframe: str = Field(description='The specific timeframe mentioned ("this_month", "this_quarter", "this_year", "all")', default="all")

class QueryParser:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY not set. Query parsing will fail.")

    def parse_query(self, query: str):
        if not self.client:
            return self._fallback_parse(query)
            
        system_prompt = """
        You are an AI assistant for a business intelligence system for founders.
        Extract the intent of the user's query into a structured JSON object.
        
        Rules:
        - If ambiguous like "How are things?", return "ambiguous".
        - If asking for a report/update, return "leadership_update".
        - For `sector`, extract the exact capitalization if it mentions Aviation, Construction, Dsp, Manufacturing, Mining, Powerline, Railways, Renewables, Security And Surveillance, or Tender. Otherwise, return "all".
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"User Query: {query}",
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=QueryIntent
                )
            )
            
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Failed to parse query via Gemini: {e}")
            logger.info("Falling back to keyword parsing due to Gemini failure.")
            return self._fallback_parse(query)
            
    def _fallback_parse(self, query: str):
        """Simple keyword matching fallback."""
        q = query.lower()
        intent = {"metric_type": "ambiguous", "sector": "all", "timeframe": "all"}
        
        if "update" in q or "leadership" in q or "report" in q:
            intent["metric_type"] = "leadership_update"
        elif "revenue" in q or "sales" in q:
            intent["metric_type"] = "revenue"
        elif "pipeline" in q:
            intent["metric_type"] = "pipeline"
        elif "win rate" in q or "win" in q:
             intent["metric_type"] = "win_rate"
        elif "active" in q or "project" in q or "operation" in q:
            intent["metric_type"] = "active_projects"
        elif "overload" in q or "cross" in q or "capacity" in q:
             intent["metric_type"] = "cross_board_insights"
        elif "health" in q or "how are" in q:
            intent["metric_type"] = "general_health"

        sectors = ["Aviation", "Construction", "Dsp", "Manufacturing", "Mining", "Powerline", "Railways", "Renewables", "Security And Surveillance", "Tender"]
        for s in sectors:
            if s.lower() in q:
                intent["sector"] = s
                break
            
        return intent
