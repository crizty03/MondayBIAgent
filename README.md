# Monday.com Business Intelligence Agent

An AI-powered BI Agent that provides founder-level insights from Monday.com Boards. It uses Google Gemini 2.5 Flash to parse natural language queries and translates them into actionable business intelligence across Sales and Operations.

## 🚀 Key Features
*   **Executive Leadership Updates**: Instantly generates reports on Revenue, Pipeline, and Operations.
*   **Natural Language Interaction**: Ask questions like "How is the Aviation pipeline?" or "Are we overloaded in Mining?"
*   **Cross-Board Intelligence**: Automatically links Deals and Work Orders to detect execution risks.
*   **Data Reliability Layer**: Sanitizes messy CRM data and flags quality warnings.

## 🏗 Architecture
*   **Frontend**: Streamlit (Dashboard & Chat)
*   **Backend**: FastAPI (Python)
*   **Intelligence**: Google Gemini (Prompt Engineering + Intent Parsing)
*   **Data**: Pandas (Analytics Engine)
*   **Integration**: GraphQL (Monday.com API)

## 📋 Prerequisites
1.  **Monday.com API Key**: Generate in `Administration > API` in Monday.com.
2.  **Google Gemini API Key**: Obtain from Google AI Studio.
3.  **Board IDs**: You will need the IDs of your "Deals" and "Work Orders" boards.

## 🛠 Setup & Local Deployment
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set environment variables:
    ```powershell
    $env:MONDAY_API_KEY="your_key"
    $env:GEMINI_API_KEY="your_key"
    ```
4.  Run the backend:
    ```bash
    python main.py
    ```
5.  Run the frontend:
    ```bash
    streamlit run app.py
    ```

## 🌐 Deployment to Render.com
This project is configured for one-click deployment to Render.
1.  Connect your GitHub repository to Render.
2.  Select **Web Service**.
3.  Use the following settings:
    *   **Runtime**: Python
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4.  Add your API keys to the **Environment Variables** section.

## 💬 Sample Queries
*   "Give me a leadership update."
*   "What is our total closed revenue in the Railways sector?"
*   "How is the pipeline looking for this quarter?"
*   "Are there any projects currently delayed?"
