# AI Customer Feedback Management System

An intelligent system that automatically classifies customer reviews and sends personalized follow-up emails to customers with negative experiences.

This project uses AI to analyze customer feedback from Excel or CSV files. It identifies the sentiment, category, and urgency of each review, and for negative reviews, it automatically drafts and sends a personalized email response.

## 🚀 Core Features

-   **Batch Processing**: Upload Excel or CSV files containing customer reviews for efficient processing.
-   **AI-Powered Analysis**: Utilizes Gemini Pro to perform:
    -   **Sentiment Analysis**: Classifies reviews as positive, negative, or neutral.
    -   **Issue Categorization**: Identifies specific issues like food quality, service, or pricing.
    -   **Urgency Assessment**: Determines the priority for responding to a review.
-   **Automated Email Responses**: For reviews classified as negative with high or medium urgency, the system automatically generates and sends a personalized and context-aware email to the customer.
-   **Interactive Dashboard**: A Streamlit-based web interface to upload files, monitor the analysis process, and view results.
-   **Detailed Analytics**: The dashboard provides visualizations of sentiment distribution, urgency levels, and key processing metrics.
-   **Downloadable Results**: Export the processed review data to a CSV file for further analysis.

## 🤖 AI Agent Workflow

1.  **File Ingestion**: User uploads an Excel or CSV file with customer reviews through the Streamlit dashboard.
2.  **Data Parsing**: The system parses the file, validating its structure and required columns (`customer_name`, `customer_email`, `review`).
3.  **Review Processing**: Each review is processed individually by the backend.
4.  **AI Analysis**: The LangGraph agent, powered by Gemini Pro, analyzes the review for sentiment, category, and urgency.
5.  **Decision Making**: Based on the analysis (e.g., negative sentiment), the agent decides whether to send an email.
6.  **Email Generation**: A personalized email is drafted using a template and the specifics of the customer's feedback.
7.  **Email Dispatch**: The email is sent to the customer via SMTP.
8.  **Result Aggregation**: The results of the analysis and actions taken are sent back to the frontend.

## 📊 Dashboard Features

The Streamlit dashboard provides a comprehensive view of the customer feedback analysis:

-   **File Uploader**: A simple drag-and-drop interface to upload review files.
-   **File Preview**: Displays the first few rows of the uploaded file to ensure it's correctly parsed.
-   **Real-time Progress**: Shows the status of the analysis, including a progress bar.
-   **Key Metrics**: Displays total reviews, number of processed reviews, errors, success rate, and number of emails sent.
-   **Sentiment Distribution**: A pie chart showing the breakdown of positive, negative, and neutral reviews.
-   **Urgency Distribution**: A bar chart illustrating the distribution of low, medium, and high-urgency reviews.
-   **Processed Reviews Table**: A detailed table of the processed reviews, including customer name, email, sentiment, confidence score, urgency, and categories.
-   **Download Results**: A button to download the full results as a CSV file.

## 🏗️ Architecture

```
├── backend/           # Python FastAPI server
│   ├── app/
│   │   ├── agents/    # LangGraph AI agents
│   │   ├── models/    # MongoDB document models
│   │   ├── services/  # Business logic
│   │   ├── api/       # API endpoints
│   │   ├── controllers/ # Request handlers
│   │   ├── routes/      # API routing
│   │   └── core/        # Core components (settings, etc.)
├── frontend/          # Streamlit application
│   └── app.py         # The main Streamlit app file
```

## 🛠️ Tech Stack

**Backend:**

-   FastAPI
-   MongoDB with Beanie and Motor
-   LangGraph for AI agent orchestration
-   Gemini Pro for language understanding
-   SMTP for sending emails

**Frontend:**

-   Streamlit
-   Pandas for data manipulation
-   Plotly for data visualization

## 🚀 Quick Start

### Prerequisites

-   Python 3.11+
-   Node.js and npm (if you were to use a javascript frontend)
-   MongoDB instance running

### Setup

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
cp env.example .env  # Configure your environment variables
uvicorn app.main:app --reload
```

Run backend
```bash
cd backend
uvicorn app.main:app --reload
```

Run frontend
```bash
cd frontend
streamlit run app.py
```

## 🔧 Environment Variables

To run the application, you'll need to set up the following environment variables in a `.env` file in the `backend` directory.

```env
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key
LANGCHAIN_API_KEY=your_langchain_api_key

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=email_support_ai

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=your_secret_key
```