# AI Customer Feedback Management System

An intelligent system that automatically classifies customer reviews and sends personalized follow-up emails to customers with negative experiences.

## 🚀 Features

- **AI-Powered Review Classification**: Uses Gemini AI and LangGraph to analyze sentiment and categorize reviews
- **Automated Email Responses**: Sends personalized emails to customers with negative reviews
- **Real-time Dashboard**: React-based interface to monitor reviews and email campaigns
- **Multi-step AI Agent**: Uses LangGraph for complex decision-making workflows
- **Analytics & Insights**: Track customer satisfaction trends and response rates

## 🏗️ Architecture

```
├── backend/           # Python FastAPI server
│   ├── app/
│   │   ├── agents/    # LangGraph AI agents
│   │   ├── models/    # Database models
│   │   ├── services/  # Business logic
│   │   └── api/       # API endpoints
├── frontend/          # React application
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
└── shared/           # Shared utilities and types
```

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- LangGraph (AI agent framework)
- Gemini AI (Language model)
- PostgreSQL (Database)
- SMTP (Email service)

**Frontend:**
- React 18
- TypeScript
- Tailwind CSS
- React Query
- Chart.js (Analytics)

## 🚀 Quick Start

### Prerequisites
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Backend Setup
```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
cp env.example .env  # Configure your environment variables
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 📧 Email Templates

The system includes customizable email templates for different scenarios:
- Service issues
- Food quality concerns
- General dissatisfaction
- Follow-up emails

## 🤖 AI Agent Workflow

1. **Review Ingestion**: Receive customer review
2. **Sentiment Analysis**: Classify as positive/negative/neutral
3. **Issue Categorization**: Identify specific problems (food, service, etc.)
4. **Urgency Assessment**: Determine priority level
5. **Email Generation**: Create personalized response
6. **Send & Track**: Deliver email and monitor engagement

## 🔧 Environment Variables

```env
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key
LANGCHAIN_API_KEY=your_langchain_api_key

# Database
DATABASE_URL=postgresql://user:password@localhost/feedback_db

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=your_secret_key
```

## 📊 Dashboard Features

- Review classification statistics
- Email campaign performance
- Customer satisfaction trends
- Response rate analytics
- Manual review override capabilities

## 🔮 Future Enhancements

- Multi-language support
- Integration with review platforms (Google, Yelp, etc.)
- A/B testing for email templates
- Advanced analytics and reporting
- Mobile app for business owners 