import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import time
from typing import Dict, Any

st.set_page_config(
    page_title="AI Review Analysis System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    h1 {
        font-size: 3rem !important;
        color: #1f2937 !important;
        margin-bottom: 2rem !important;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .upload-section {
        border: 2px dashed #cbd5e0;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f7fafc;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

API_BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{API_BASE_URL}/api/v1/reviews/upload-excel"

def main():
    # Header
    st.markdown("# 🤖 AI Review Analysis System")
    st.markdown("### Upload Excel files with customer reviews for intelligent analysis")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📋 File Requirements")
        st.markdown("""
        **Required columns:**
        - `customer_name` or `name`
        - `customer_email` or `email`
        - `review` or `comment` or `feedback`
        
        **Supported formats:**
        - Excel (.xlsx, .xls)
        - CSV (.csv)
        
        **Max file size:** 10MB
        """)
        st.markdown("---")
        st.markdown("## ℹ️ About AI Review Analysis System")
    
        st.markdown("""
        ### 🎯 What It Does
        Automatically analyze customer reviews using AI to extract:
        - **Sentiment**: Positive, negative, or neutral emotions
        - **Categories**: Quality, service, pricing, delivery issues
        - **Urgency**: Priority levels for customer support
        
        ### 🔧 Technology
        - **AI**: Gemini Pro language model
        - **Backend**: FastAPI + MongoDB
        - **Frontend**: Streamlit
        """)
    
    upload_page()

def upload_page():
    """Upload and process Excel files page"""
    
    st.markdown("### 📁 Upload Your Excel File")
    
    uploaded_file = st.file_uploader(
        "Choose an Excel or CSV file",
        type=['xlsx', 'xls', 'csv'],
        help="Upload a file containing customer reviews for AI analysis"
    )
    
    if uploaded_file is not None:
        file_details = {
            "filename": uploaded_file.name,
            "filetype": uploaded_file.type,
            "filesize": uploaded_file.size
        }
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 Filename", file_details["filename"])
        with col2:
            st.metric("📊 File Type", file_details["filetype"])
        with col3:
            st.metric("💾 Size", f"{file_details['filesize']} bytes")
        
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.markdown("### 👀 File Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            st.markdown(f"**Total rows:** {len(df)}")
            
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        if st.button("🚀 Process Reviews with AI", type="primary", use_container_width=True):
            process_file(uploaded_file)

def process_file(uploaded_file):
    """Process the uploaded file with the API"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        
        status_text.text("🔄 Uploading file to AI analysis system...")
        progress_bar.progress(25)
        
        response = requests.post(UPLOAD_ENDPOINT, files=files, timeout=300)
        
        progress_bar.progress(75)
        status_text.text("🧠 AI is analyzing reviews...")
        
        if response.status_code == 200:
            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")
            
            result = response.json()
            display_results(result)
            
        else:
            st.error(f"❌ Error processing file: {response.status_code}")
                
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please try again with a smaller file.")
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to the AI service. Please ensure the backend is running.")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
    finally:
        progress_bar.empty()
        status_text.empty()

def display_results(result: Dict[str, Any]):
    """Display the processing results with beautiful visualizations"""
    
    st.markdown("## 🎉 Processing Results")
    
    results_data = result.get("results", {})
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Total Rows</h3>
            <h2>{results_data.get('total_rows', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        processed = results_data.get('processed', 0)
        st.markdown(f"""
        <div class="success-card">
            <h3>✅ Processed</h3>
            <h2>{processed}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        errors = len(results_data.get('errors', []))
        st.markdown(f"""
        <div class="warning-card">
            <h3>❌ Errors</h3>
            <h2>{errors}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        success_rate = (processed / results_data.get('total_rows', 1)) * 100
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 Success Rate</h3>
            <h2>{success_rate:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        emails_sent = results_data.get('emails_sent', 0)
        st.markdown(f"""
        <div class="metric-card">
            <h3>📧 Emails Sent</h3>
            <h2>{emails_sent}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    sentiment_summary = results_data.get('sentiment_summary', {})
    reviews_created = results_data.get('reviews_created', [])
    
    if sentiment_summary:
        st.markdown("### 😊 Sentiment & Urgency Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            labels = list(sentiment_summary.keys())
            values = list(sentiment_summary.values())
            colors = ['#10b981', '#ef4444', '#6b7280']  # green, red, gray
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=[l.capitalize() for l in labels],
                values=values,
                hole=0.4,
                marker_colors=colors
            )])
            fig_pie.update_layout(
                title="Sentiment Distribution",
                font=dict(size=14),
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            if reviews_created:
                urgency_levels = [r['analysis']['urgency_level'] for r in reviews_created]
                urgency_summary = pd.Series(urgency_levels).value_counts().reindex(['low', 'medium', 'high']).dropna()

                fig_bar = px.bar(
                    x=[l.capitalize() for l in urgency_summary.index],
                    y=urgency_summary.values,
                    color=[l.capitalize() for l in urgency_summary.index],
                    color_discrete_map={
                        'Low': '#10b981',    # Green
                        'Medium': '#f59e0b', # Amber
                        'High': '#ef4444'    # Red
                    },
                    title="Urgency Distribution"
                )
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
    
    if reviews_created:
        st.markdown("### 📝 Processed Reviews")
        
        display_df = pd.DataFrame({
            'Customer': [r['customer_name'] for r in reviews_created],
            'Email': [r['customer_email'] for r in reviews_created],
            'Sentiment': [r['analysis']['sentiment'].capitalize() for r in reviews_created],
            'Confidence': [f"{r['analysis']['sentiment_score']:.2f}" for r in reviews_created],
            'Urgency': [r['analysis']['urgency_level'].capitalize() for r in reviews_created],
            'Categories': [', '.join(r['analysis']['categories']) for r in reviews_created]
        })
        
        st.dataframe(display_df, use_container_width=True)
        
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"processed_reviews_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    if results_data.get('errors'):
        st.markdown("### ⚠️ Processing Errors")
        with st.expander(f"View {len(results_data['errors'])} errors"):
            for error in results_data['errors']:
                st.error(error)

if __name__ == "__main__":
    main() 