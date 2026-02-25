import os
import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MondayClient:
    def __init__(self):
        self.api_key = os.environ.get("MONDAY_API_KEY")
        if not self.api_key:
            logger.warning("MONDAY_API_KEY environment variable not set. API calls will fail.")
        self.headers = {
            "Authorization": self.api_key or "",
            "API-Version": "2023-10", 
            "Content-Type": "application/json"
        }
        self.url = "https://api.monday.com/v2"
        self.boards = {} # Cache for board names to IDs

    def execute_query(self, query, variables=None, retries=3, backoff_factor=1.5):
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        for attempt in range(retries):
            try:
                response = requests.post(self.url, json=payload, headers=self.headers, timeout=15)
                # Check rate limits
                if response.status_code == 429:
                    logger.warning("Monday API rate limit hit. Retrying...")
                    time.sleep(backoff_factor ** attempt)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    logger.error(f"GraphQL Errors: {data['errors']}")
                    return None
                    
                return data.get("data")

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt < retries - 1:
                    sleep_time = backoff_factor ** attempt
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error("Max retries reached. Monday API call failed.")
                    return None
        return None

    def get_boards(self):
        query = """
        query {
            boards (limit: 50) {
                id
                name
            }
        }
        """
        data = self.execute_query(query)
        if data and data.get("boards"):
            self.boards = {b["name"]: b["id"] for b in data["boards"]}
            return self.boards
        return {}

    def fetch_board_data(self, board_name):
        # Allow case-insensitive search
        if not self.boards:
            self.get_boards()
            
        board_id = None
        search_terms = [board_name.lower(), board_name.lower().rstrip('s'), board_name.lower().split()[0]]
        
        for name, bids in self.boards.items():
            name_lower = name.lower()
            if any(term in name_lower for term in search_terms):
                board_id = bids
                break
                
        if not board_id:
            logger.error(f"Board '{board_name}' not found.")
            return None

        # Fetch board items and column values dynamically
        query = """
        query ($boardId: [ID!]) {
            boards (ids: $boardId) {
                name
                items_page (limit: 500) {
                    items {
                        id
                        name
                        column_values {
                            id
                            text
                            type
                            value
                            column {
                                title
                            }
                        }
                    }
                }
            }
        }
        """
        variables = {"boardId": str(board_id)}
        data = self.execute_query(query, variables=variables)
        
        if data and data.get("boards") and len(data["boards"]) > 0:
            return data["boards"][0]["items_page"]["items"]
        return []
        
    def validate_connection(self):
        """Validate connection by fetching boards."""
        if not self.api_key:
            return False, "API key not set."
        boards = self.get_boards()
        if boards is not None:
             return True, "Connected successfully."
        return False, "Failed to connect to Monday.com API."
