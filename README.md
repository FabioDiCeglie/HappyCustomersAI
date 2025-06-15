# HappyCustomersAI

An intelligent system that automatically classifies customer reviews and sends personalized follow-up emails to customers with negative experiences.

This project uses AI to analyze customer feedback from Excel or CSV files. It identifies the sentiment, category, and urgency of each review, and for negative reviews, it automatically drafts and sends a personalized email response.

## 🚀 Core Features

This system processes customer reviews from Excel/CSV files, using AI to analyze sentiment, categorize issues, and assess urgency. For negative feedback with medium or high urgency, it automatically drafts and sends personalized emails. The interactive dashboard allows for file uploads, progress monitoring, and viewing detailed analytics, with an option to download the results.

## 🤖 AI Agent Workflow

The workflow begins when a user uploads a review file. Each review is analyzed by an AI agent to determine sentiment, category, and urgency. Based on this analysis, for negative reviews with medium or high urgency, a personalized email is generated and sent. The aggregated results are then presented on the dashboard.

## 📊 Dashboard Features

The dashboard provides a simple interface to upload files, preview data, and track the analysis in real-time. It features visualizations for sentiment and urgency, along with key metrics. A detailed table of the processed reviews is also available and can be downloaded as a CSV file.

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

## ☁️ Deployment

The application is designed to be deployed with a containerized backend on **Google Cloud Run** and a frontend on **Streamlit Community Cloud**.

### Backend

The backend is deployed as a Docker container on Google Cloud Run. For detailed instructions on how to build and deploy the backend, including manual and automated workflows, see the deployment guide:

[**➡️ Backend Deployment Guide (`backend/DEPLOYMENT.md`)**](./backend/DEPLOYMENT.md)

### Frontend

The Streamlit application is deployed directly from the GitHub repository to the Streamlit Community Cloud.

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
GOOGLE_API_KEY=your_gemini_api_key

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```
