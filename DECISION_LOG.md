# Monday.com Business Intelligence Agent — Decision Log

## 1. Key Assumptions
*   **Messy Business Data**: Assumed board data contains missing values, specifically close dates and revenue numbers. Fallback logic is implemented to report these as quality warnings.
*   **Inconsistent Status Labels**: Statuses like "Closed Won", "Sent to Client", and "Done" vary. Normalization uses regex (e.g., `closed|won`) for flexible matching.
*   **Founder Context**: Assumed that "How are things?" or "Leadership update" implies a cross-board summary of revenue, pipeline, and operations.

## 2. Architecture Decisions
*   **Modular Layered Design**: Separated concerns into `monday_client` (API), `data_cleaner` (Reliability), `bi_engine` (Analytics), and `query_parser` (Intelligence).
*   **Streamlit Frontend**: Chosen for rapid, Python-native dashboarding with native support for chat and data visualization.
*   **FastAPI Backend**: Provides a robust, scalable REST API for handling complex analytical queries synchronously.
*   **Gemini 2.5 Flash**: Integrated via `google-genai` for high-performance, low-latency intent parsing and structured JSON output.

## 3. Data Cleaning & KPIs
*   **Status Normalization**: Automated conversion of arbitrary board statuses to standard "Open/Closed" states for KPI calculation.
*   **Date Fallback**: Missing close dates are flagged rather than guessed to maintain data integrity in the pipeline report.
*   **Cross-Board Intelligence**: Joins deal pipeline with work order status to detect "Operational Overload" (e.g., high pipeline concentration with delayed execution).

## 4. Trade-offs
*   **Read-Only Integration**: Prioritizing data safety and simplicity. The agent does not modify Monday.com data.
*   **In-Memory Processing**: Uses Pandas for analytics. Suitable for portfolios of up to ~10,000 records; enterprise-scale would require a database caching layer.

## 5. Future roadmap
*   **Trend Analysis**: Moving average calculations for revenue growth over time.
*   **Auto-Detection**: Dynamically detecting board schemas rather than using static column mappings.
*   **Authentication**: Secure user login for multi-tenant deployment.
