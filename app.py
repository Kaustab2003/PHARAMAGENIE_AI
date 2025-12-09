# app.py
import streamlit as st
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import plotly.express as px
import asyncio
import uuid
import webbrowser
import logging
from typing import Dict, Any, List, Optional
from functools import wraps, lru_cache
import hashlib
import base64
import time
from cryptography.fernet import Fernet
from ratelimit import limits, sleep_and_retry

# Import custom modules
from api.websocket import manager, send_progress_update
from features.comparison import DrugComparison
from features.batch_processor import BatchProcessor
from pages.analytics import AnalyticsDashboard
from utils.email_service import EmailService
from utils.molecule_viz import MoleculeVisualizer
from agents.insights_agent import InsightsAgent

# Import agent modules
from agents.fda_agent import FDAAgent
from agents.trade_agent import TradeAgent
from agents.patent_agent import PatentLandscapeAgent
from agents.clinical_trials_agent import ClinicalTrialsAgent
from agents.web_intel_agent import WebIntelligenceAgent
from agents.internal_insights_agent import InternalInsightsAgent

# Constants
CALLS = 10  # Max API calls
PERIOD = 60  # per 60 seconds

# =============================================
# Core Utility Functions
# =============================================

def setup_logging():
    """Configure application logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging configured successfully")

def validate_environment():
    """Validate required environment variables."""
    required_vars = [
        "OPENAI_API_KEY",
        "SMTP_SERVER",
        "SMTP_PORT",
        "SENDER_EMAIL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logging.error(error_msg)
        raise EnvironmentError(error_msg)

def encrypt_data(data: str, key: str) -> str:
    """Encrypt sensitive data."""
    try:
        f = Fernet(base64.urlsafe_b64encode(key.encode() + b'=' * (32 - len(key))))
        return f.encrypt(data.encode()).decode()
    except Exception as e:
        logging.error(f"Encryption error: {str(e)}")
        raise

def decrypt_data(encrypted_data: str, key: str) -> str:
    """Decrypt sensitive data."""
    try:
        f = Fernet(base64.urlsafe_b64encode(key.encode() + b'=' * (32 - len(key))))
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logging.error(f"Decryption error: {str(e)}")
        raise

@lru_cache(maxsize=100)
def get_analysis_cache_key(drug_name: str, therapeutic_area: str) -> str:
    """Generate a cache key for analysis results."""
    key_str = f"{drug_name.lower()}_{therapeutic_area.lower()}"
    return hashlib.md5(key_str.encode()).hexdigest()

def validate_drug_name(drug_name: str) -> bool:
    """Validate drug name format."""
    if not drug_name or not drug_name.strip():
        return False
    # Add more validation rules as needed
    return True

@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def call_external_api(endpoint: str, params: dict):
    """Rate-limited API call."""
    logging.info(f"Calling API: {endpoint}")
    # Implementation here
    pass

def timeit(func):
    """Decorator to measure function execution time."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"Function {func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper

# =============================================
# Application State and Configuration
# =============================================

class AppState:
    def __init__(self):
        self.fda_agent = FDAAgent()
        self.trade_agent = TradeAgent()
        self.patent_agent = PatentLandscapeAgent()
        self.clinical_trials_agent = ClinicalTrialsAgent()
        self.web_intel_agent = WebIntelligenceAgent()
        self.internal_insights_agent = InternalInsightsAgent()

# Initialize services
setup_logging()
email_service = EmailService()
molecule_viz = MoleculeVisualizer()
batch_processor = BatchProcessor(max_workers=4)
insights_agent = InsightsAgent()

# Load environment variables
load_dotenv()
validate_environment()

# =============================================
# UI Components
# =============================================

def get_websocket_js():
    """Generate WebSocket JavaScript code."""
    return f"""
    <script>
    const client_id = "{st.session_state.client_id}";
    let socket;
    
    function connectWebSocket() {{
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname + ':8000';
        socket = new WebSocket(${{protocol}}//${{host}}/ws/${{client_id}});
        
        socket.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            updateUI(data);
        }};
        
        socket.onclose = function() {{
            console.log('WebSocket disconnected. Reconnecting...');
            setTimeout(connectWebSocket, 3000);
        }};
    }}
    
    function updateUI(data) {{
        // Update progress bar
        const progressBar = document.getElementById('progress-bar');
        if (progressBar) {{
            progressBar.style.width = data.progress + '%';
            progressBar.textContent = data.progress + '%';
        }}
        
        // Update status text
        const statusText = document.getElementById('status-text');
        if (statusText) {{
            statusText.textContent = data.message;
        }}
    }}
    
    window.addEventListener('load', function() {{
        connectWebSocket();
    }});
    </script>
    <style>
    .progress {{
        height: 20px;
        margin-bottom: 20px;
        overflow: hidden;
        background-color: #f5f5f5;
        border-radius: 4px;
        box-shadow: inset 0 1px 2px rgba(0,0,0,.1);
    }}
    .progress-bar {{
        float: left;
        width: 0;
        height: 100%;
        font-size: 12px;
        line-height: 20px;
        color: #fff;
        text-align: center;
        background-color: #4CAF50;
        transition: width .6s ease;
    }}
    .alert {{
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid transparent;
        border-radius: 4px;
    }}
    .alert-info {{
        color: #31708f;
        background-color: #d9edf7;
        border-color: #bce8f1;
    }}
    .alert-success {{
        color: #3c763d;
        background-color: #dff0d8;
        border-color: #d6e9c6;
    }}
    .alert-warning {{
        color: #8a6d3b;
        background-color: #fcf8e3;
        border-color: #faebcc;
    }}
    .alert-error {{
        color: #a94442;
        background-color: #f2dede;
        border-color: #ebccd1;
    }}
    </style>
    """

def display_welcome():
    """Display welcome message and instructions."""
    st.title("🧪 Welcome to PharmaGenie AI")
    st.markdown("### Your AI-Powered Drug Repurposing Assistant")
    
    with st.expander("📚 How It Works", expanded=True):
        st.markdown("""
        1. *Enter a drug name* you're interested in
        2. *Select a therapeutic area* (optional)
        3. Click *Analyze* to generate insights
        4. View detailed reports and export results
        """)
    
    with st.expander("💡 Example Queries", expanded=False):
        st.markdown("""
        - "Metformin in oncology"
        - "Aspirin for cardiovascular prevention"
        - "Ibuprofen in Alzheimer's disease"
        """)

async def update_progress(stage: str, progress: int, total_stages: int = 5):
    """Update progress with detailed stage information."""
    progress_percent = int((progress / total_stages) * 100)
    await send_progress_update(
        st.session_state.client_id,
        progress_percent,
        "Analysis in Progress",
        f"Stage {progress}/{total_stages}: {stage}"
    )


def collect_user_feedback(analysis_id: str):
    """Collect user feedback for analysis."""
    with st.expander("📝 Provide Feedback", expanded=False):
        rating = st.slider("Rate this analysis (1-5)", 1, 5, 3)
        comments = st.text_area("Your feedback (optional)")
        if st.button("Submit Feedback"):
            try:
                # Save feedback to database or file
                save_feedback(analysis_id, rating, comments)
                st.success("Thank you for your feedback!")
            except Exception as e:
                st.error("Failed to save feedback. Please try again.")
                logging.error(f"Feedback error: {str(e)}")

def save_feedback(analysis_id: str, rating: int, comments: str):
    """Save user feedback to a file."""
    feedback_dir = Path("data/feedback")
    feedback_dir.mkdir(parents=True, exist_ok=True)
    
    feedback = {
        "analysis_id": analysis_id,
        "rating": rating,
        "comments": comments,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(feedback_dir / f"feedback_{analysis_id}.json", "w") as f:
        json.dump(feedback, f, indent=2)

# =============================================
# Core Application Logic
# =============================================

@timeit
async def analyze_drug(drug_name: str, therapeutic_area: str) -> dict:
    """Analyze drug with all available agents."""
    try:
        if not validate_drug_name(drug_name):
            raise ValueError("Invalid drug name")
            
        cache_key = get_analysis_cache_key(drug_name, therapeutic_area)
        
        # Check cache first
        if cache_key in st.session_state:
            logging.info(f"Returning cached result for {drug_name}")
            return st.session_state[cache_key]
            
        await update_progress("Starting analysis", 1, 5)
        
        # Collect data from all agents in parallel
        tasks = [
            asyncio.create_task(
                asyncio.to_thread(
                    st.session_state.app_state.fda_agent.get_drug_adverse_events,
                    drug_name,
                    limit=10
                )
            ),
            asyncio.create_task(
                asyncio.to_thread(
                    st.session_state.app_state.trade_agent.get_trade_data_by_drug,
                    drug_name
                )
            ),
            asyncio.create_task(
                asyncio.to_thread(
                    st.session_state.app_state.patent_agent.get_patent_analysis, 
                    drug_name
                )
            ),
            asyncio.create_task(
                asyncio.to_thread(
                    st.session_state.app_state.clinical_trials_agent.get_clinical_trials,
                    drug_name,
                    therapeutic_area
                )
            ),
            asyncio.create_task(
                asyncio.to_thread(
                    st.session_state.app_state.web_intel_agent.search_evidence,
                    f"{drug_name} {therapeutic_area}"
                )
            ),
            asyncio.create_task(
                asyncio.to_thread(
                    st.session_state.app_state.internal_insights_agent.get_internal_insights,
                    drug_name
                )
            )
        ]
        
        # Wait for all tasks to complete
        await update_progress("Gathering data from all sources", 2, 5)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results with proper error handling
        def process_result(result, default=None):
            if isinstance(result, Exception):
                logging.error(f"Error in task: {str(result)}")
                return default or {}
            return result if result is not None else {}
        
        # Process FDA adverse events data
        fda_data = process_result(results[0], pd.DataFrame())
        
        # Convert DataFrame to dict for JSON serialization if needed
        if hasattr(fda_data, 'to_dict'):
            fda_data = fda_data.to_dict(orient='records')
        
        # Process trade data
        trade_data = process_result(results[1], {})
        
        # Process other results
        patent_analysis = process_result(results[2])
        clinical_trials = process_result(results[3])
        web_intel = process_result(results[4])
        internal_insights = process_result(results[5])
        
        # Generate final analysis with consistent structure
        await update_progress("Analyzing results", 3, 5)
        analysis = {
            "drug_name": drug_name,
            "therapeutic_area": therapeutic_area or 'General',
            "timestamp": datetime.now().isoformat(),
            "adverse_events": fda_data,
            "trade_data": trade_data,
            "patent_analysis": patent_analysis or {
                'active_patents': 0,
                'freedom_to_operate': 'N/A',
                'key_insights': ['No patent data available']
            },
            "clinical_trials": clinical_trials or {
                'phase_ii_trials': 0,
                'phase_iii_trials': 0,
                'key_insights': ['No clinical trials data available']
            },
            "web_intelligence": web_intel or {
                'sources': [],
                'findings': ['No web intelligence data available']
            },
            "internal_insights": internal_insights or {
                'previous_research': [],
                'strategic_fit': 'N/A',
                'key_insights': ['No internal insights available']
            }
        }
        
        await update_progress("Finalizing analysis", 4, 5)
        st.session_state[cache_key] = {
            "status": "success",
            "analysis": analysis
        }
        
        await update_progress("Analysis complete", 5, 5)
        return st.session_state[cache_key]
        
    except Exception as e:
        error_msg = f"Analysis error: {str(e)}"
        logging.error(f"Error in analyze_drug: {error_msg}", exc_info=True)
        await send_progress_update(
            st.session_state.client_id,
            0,
            "Error",
            error_msg
        )
        return {
            "status": "error",
            "message": error_msg
        }

async def show_comprehensive_report(analysis_data: dict):
    """Display comprehensive analysis report with dynamic data and visualizations."""
    st.title(f"📊 Comprehensive Analysis for {analysis_data.get('drug_name', '').title()}")
    st.caption(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # --- Market Analysis ---
    with st.expander("📈 Market Analysis", expanded=True):
        trade_data = analysis_data.get('trade_data', {})
        if not trade_data or 'error' in trade_data:
            st.warning("Market analysis data could not be retrieved.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Market Size", trade_data.get('market_size', 'N/A'))
            col2.metric("CAGR", trade_data.get('cagr', 'N/A'))
            col3.metric("Market Trend", trade_data.get('market_trend', 'N/A'))

            if trade_data.get('market_share'):
                st.subheader("Market Share by Region")
                df = pd.DataFrame(trade_data['market_share'])
                fig = px.pie(df, values='share', names='name', title='Regional Market Share', hole=0.3)
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Key Insights")
            for insight in trade_data.get('key_insights', ["No insights available."]):
                st.markdown(f"- {insight}")
            st.caption(f"Source: {trade_data.get('source', 'N/A')} | Last Updated: {trade_data.get('last_updated', 'N/A')}")

    # --- Patent Landscape ---
    with st.expander("📜 Patent Landscape", expanded=True):
        patents = analysis_data.get('patent_analysis', {})
        if not patents or 'error' in patents:
            st.warning("Patent landscape data could not be retrieved.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Active Patents", patents.get('active_patents', 0))
            col2.metric("Next Expiry Year", str(patents.get('next_expiry', 'N/A')))
            col3.metric("Freedom to Operate", patents.get('freedom_to_operate', 'N/A'))

            if patents.get('patent_timeline'):
                st.subheader("Patent Expiry Timeline")
                df = pd.DataFrame(patents['patent_timeline'])
                df['expiry_date'] = pd.to_datetime(df['expiry_date'])
                fig = px.timeline(df, x_start="filing_date", x_end="expiry_date", y="patent_number", color="status",
                                title="Patent Status Over Time", color_discrete_map={"Active": "#2ecc71", "Expired": "#e74c3c"})
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Key Insights")
            for insight in patents.get('key_insights', ["No insights available."]):
                st.markdown(f"- {insight}")

    # --- Clinical Trials ---
    with st.expander("🔬 Clinical Trials", expanded=True):
        trials = analysis_data.get('clinical_trials', {})
        if not trials or 'error' in trials:
            st.warning(trials.get("message", "Clinical trials data could not be retrieved."))
            if 'suggestion' in trials:
                st.info(trials['suggestion'], icon="💡")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Studies Found", trials.get('total_studies', 0))
            col2.metric("Phase II Trials", trials.get('phase_ii_trials', 0))
            col3.metric("Phase III Trials", trials.get('phase_iii_trials', 0))

            st.subheader("Recent Clinical Trials")
            if trials.get('recent_trials'):
                for trial in trials['recent_trials']:
                    with st.container(border=True):
                        st.markdown(f"{trial.get('title', 'No Title')}")
                        c1, c2 = st.columns([3,1])
                        c1.caption(f"*Conditions:* {trial.get('conditions', 'N/A')} | *Interventions:* {trial.get('interventions', 'N/A')}")
                        c2.link_button("View on ClinicalTrials.gov", trial.get('url', '#'), use_container_width=True)
                        
                        sc1, sc2, sc3, sc4 = st.columns(4)
                        sc1.metric("Status", trial.get('status', 'N/A'))
                        sc2.metric("Phase", trial.get('phase', 'N/A'))
                        sc3.metric("Enrollment", str(trial.get('enrollment', 'N/A')))
                        sc4.metric("Start Date", trial.get('start_date', 'N/A'))
            else:
                st.info("No recent trials were found based on the search criteria.")

            st.subheader("Key Insights")
            for insight in trials.get('key_insights', ["No insights available."]):
                st.markdown(f"- {insight}")

    # --- Web Intelligence ---
    with st.expander("🌐 Web Intelligence", expanded=True):
        web_intel = analysis_data.get('web_intelligence', {})
        if not web_intel or 'error' in web_intel:
            st.warning("Web intelligence data could not be retrieved.")
        else:
            st.subheader("Latest Research from PubMed")
            if web_intel.get('findings'):
                for finding in web_intel['findings']:
                    st.markdown(f"- {finding}")
            else:
                st.info("No recent publications found on PubMed.")

            st.subheader("Recent News from Google")
            if web_intel.get('news'):
                for item in web_intel['news']:
                    st.markdown(f"[{item['title']}]({item['url']})")
                    st.caption(f"Source: {item['source']} | Published: {item['date']}")
                    st.markdown(f"> {item['snippet']}", unsafe_allow_html=True)
            else:
                st.info("No recent news articles found.")

    # --- Internal Insights ---
    with st.expander("🏢 Internal Insights", expanded=True):
        internal = analysis_data.get('internal_insights', {})
        if not internal or 'error' in internal:
            st.warning("Internal insights could not be retrieved.")
        else:
            st.subheader("Strategic Fit Analysis")
            fit = internal.get('strategic_fit', {})
            if fit:
                level = fit.get('level', 'N/A')
                score = fit.get('score', 0)
                st.progress(score, text=f"Strategic Fit Score: {score}/100 ({level})")
                st.markdown(f"> {fit.get('rationale', 'No rationale provided.')}")

            st.subheader("Related Internal Research")
            if internal.get('previous_research'):
                for project in internal['previous_research']:
                    with st.container(border=True):
                        st.markdown(f"{project['title']}** ({project['date']})")
                        st.caption(f"Status: {project['status']}")
                        st.write(project['summary'])
            else:
                st.info("No prior internal research found for this drug.")
            st.subheader("Key Insights")
            for insight in internal.get('key_insights', ["No insights available."]):
                st.markdown(f"- {insight}")


# =============================================
# Main Application
# =============================================

async def main_app():
    """Main application logic."""
    # Initialize app state
    if 'app_state' not in st.session_state:
        st.session_state.app_state = AppState()
    
    if 'client_id' not in st.session_state:
        st.session_state.client_id = str(uuid.uuid4())
    
    if 'recent_analyses' not in st.session_state:
        st.session_state.recent_analyses = []

    page = st.sidebar.radio(
        "Navigation",
        [
            "Analysis",
            "💊 Drug Explorer",
            "🚀 Advanced AI Features",
            "🔗 Drug Interactions",
            "Analytics",
            "Email Reports"
        ]
    )
    
    # Progress bar in sidebar
    with st.sidebar:
        st.markdown("### Analysis Progress")
        progress_bar = st.progress(0, text="Waiting to start...")
        
        # Recent analyses
        if st.session_state.recent_analyses:
            st.subheader("📋 Recent Analyses")
            for analysis in st.session_state.recent_analyses[-5:]:
                if st.button(f"{analysis.get('drug_name', 'Unknown')} - {analysis.get('therapeutic_area', '')}"):
                    st.session_state.current_analysis = analysis
    
    # Page routing
    if page == "Analysis":
        await handle_analysis_page()
    elif page == "💊 Drug Explorer":
        from pages.drug_explorer import render_drug_explorer_page
        render_drug_explorer_page()
    elif page == "🚀 Advanced AI Features":
        from pages.advanced_features import render_advanced_features_page
        render_advanced_features_page()
    elif page == "🔗 Drug Interactions":
        from pages.interaction_network import render_interaction_network_page
        render_interaction_network_page()
    elif page == "Batch Processing":
        show_batch_processing()
    elif page == "Molecule Visualizer":
        show_molecule_visualizer()
    elif page == "Comprehensive Report":
        if hasattr(st.session_state, 'current_analysis'):
            await show_comprehensive_report(st.session_state.current_analysis)
        else:
            st.warning("Please run an analysis first to view the comprehensive report.")
    elif page == "Analytics":
        show_analytics_dashboard()
    elif page == "Email Reports":
        show_email_reports()

async def handle_analysis_page():
    """Handle the analysis page by separating form submission from result display."""
    display_welcome()
    
    # Check for saved search query from voice assistant
    default_drug = ""
    if 'drug_search_query' in st.session_state and st.session_state.get('drug_search_query'):
        st.info(f"🎤 Voice Assistant suggested: **{st.session_state['drug_search_query']}**")
        default_drug = st.session_state['drug_search_query']

    with st.form("drug_analysis_form"):
        drug_name = st.text_input("Drug Name", value=default_drug, placeholder="Enter drug name")
        therapeutic_area = st.text_input(
            "Therapeutic Area (optional)",
            placeholder="e.g., Oncology"
        )
        submitted = st.form_submit_button("🚀 Start Analysis")

        if submitted:
            if not drug_name:
                st.error("Please enter a drug name")
            else:
                with st.spinner("Analyzing..."):
                    result = await analyze_drug(drug_name, therapeutic_area)
                    if result["status"] == "success":
                        analysis = result["analysis"]
                        analysis['analysis_id'] = str(uuid.uuid4())
                        st.session_state.current_analysis = analysis
                        st.session_state.recent_analyses.append(analysis)
                    else:
                        st.error(f"❌ Analysis failed: {result.get('message', 'Unknown error')}")
                        st.session_state.current_analysis = None

    # Display the report and feedback form outside of the main analysis form
    if 'current_analysis' in st.session_state and st.session_state.current_analysis:
        await show_comprehensive_report(st.session_state.current_analysis)
        collect_user_feedback(st.session_state.current_analysis['analysis_id'])

def show_batch_processing():
    """Display batch processing interface."""
    st.title("📊 Batch Processing")
    st.warning("Batch processing feature is under development.")
    # Implementation here

def show_molecule_visualizer():
    """Display molecule visualization."""
    st.title("🔬 Molecule Visualizer")
    st.warning("Molecule visualization feature is under development.")
    # Implementation here

def show_analytics_dashboard():
    """Display analytics dashboard.

    This now instantiates the AnalyticsDashboard from pages.analytics
    so the improved multi-drug comparison UI and charts are shown.
    """
    try:
        dashboard = AnalyticsDashboard()
        dashboard.show_overview()
    except Exception as e:
        st.error("Failed to load Analytics Dashboard")
        st.exception(e)

def test_email_connection():
    """Test the email connection and display results."""
    with st.spinner("Testing email connection..."):
        success, message = email_service.test_connection()
        if success:
            st.success(f"✅ {message}")
            
            # Test sending a real email
            st.info("Sending a test email...")
            test_success, test_msg = email_service.send_email(
                to_email=email_service.sender_email,  # Send to self
                subject="Test Email from PharmaGenie AI",
                body="""
                <h2>Test Email</h2>
                <p>This is a test email from PharmaGenie AI.</p>
                <p>If you received this, your email configuration is working correctly!</p>
                <p>Current time: {}</p>
                """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                cc=None,
                bcc=None
            )
            
            if test_success:
                st.success(f"✅ Test email sent successfully to {email_service.sender_email}")
                st.balloons()
            else:
                st.error(f"❌ Failed to send test email: {test_msg}")
        else:
            st.error(f"❌ {message}")
            
            # Provide troubleshooting steps
            with st.expander("🔧 Troubleshooting Steps", expanded=True):
                st.markdown("""
                ### ⚠️ Gmail Authentication Error
                
                **The most common issue is using your regular Gmail password instead of an App Password.**
                
                ### ✅ How to Fix:
                
                1. **Generate Gmail App Password:**
                   - Go to: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
                   - Enable 2-Factor Authentication first (if not enabled)
                   - Select "Mail" and "Windows Computer"
                   - Click "Generate"
                   - Copy the 16-character password (remove spaces)
                   
                2. **Update your .env file:**
                   - Open `.env` in your project folder
                   - Update `SENDER_PASSWORD` with the App Password
                   - Save and restart the app
                   
                3. **Check your credentials:**
                   - Verify SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, and SENDER_PASSWORD in your .env file
                   - Make sure there are no extra spaces in the values
                
                ### 📖 Full Guide
                See `EMAIL_TROUBLESHOOTING.md` for detailed instructions
                   
                3. **Firewall/Antivirus:**
                   - Temporarily disable any firewall or antivirus that might block the connection
                   
                4. **Try different ports:**
                   - Common ports: 587 (TLS), 465 (SSL), or 25 (not recommended)
                """)

def show_email_reports():
    """Display email reports interface with configuration options."""
    st.title("📧 Email Reports")
    
    # Check if email configuration is set up
    if not all([os.getenv("SMTP_SERVER"), os.getenv("SENDER_EMAIL"), os.getenv("SENDER_PASSWORD")]):
        st.error("⚠️ Email service is not properly configured. Please set up SMTP settings in your environment variables.")
        st.info("""
        Required environment variables:
        - `SMTP_SERVER`: Your SMTP server (e.g., smtp.gmail.com)
        - `SMTP_PORT`: SMTP port (e.g., 587 for TLS)
        - `SENDER_EMAIL`: Your email address
        - `SENDER_PASSWORD`: Your email password or app password
        """)
        return

    # Test connection button
    if st.button("🔌 Test Email Connection"):
        test_email_connection()
    
    st.markdown("---")
    
    # Email configuration form
    with st.form("email_config_form"):
        st.subheader("Email Configuration")
        
        # Recipient email
        recipient_email = st.text_input("Recipient Email", 
                                     placeholder="Enter recipient email address",
                                     help="The email address that will receive the report")
        
        # Report type selection
        report_type = st.selectbox(
            "Report Format",
            ["PDF", "JSON"],
            index=0,
            help="Select the format of the report"
        )
        
        # Schedule options
        schedule = st.selectbox(
            "Schedule",
            ["Send Now", "Daily", "Weekly", "Monthly"],
            index=0,
            help="When to send the report"
        )
        
        # Include analysis data option
        include_data = st.checkbox(
            "Include raw analysis data",
            value=False,
            help="Include the complete analysis data in the email"
        )
        
        # Submit button
        submitted = st.form_submit_button("Send Report")
        
        if submitted:
            if not recipient_email:
                st.error("Please enter a recipient email address")
            else:
                with st.spinner("Sending report..."):
                    # Get the current analysis if available
                    analysis_data = st.session_state.get('current_analysis', {})
                    if not analysis_data:
                        st.warning("No current analysis found. Using sample data.")
                        analysis_data = {
                            "drug_name": "Sample Drug",
                            "score": "85%",
                            "indication": "Sample indication",
                            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                    
                    # Send the email
                    success = email_service.send_analysis_report(
                        to_email=recipient_email,
                        analysis_data=analysis_data,
                        format_type=report_type.lower()
                    )
                    
                    if success:
                        st.success(f"✅ Report sent successfully to {recipient_email}")
                    else:
                        st.error("❌ Failed to send email. Please check your email configuration.")
    
    # Add a section for scheduled reports
    st.markdown("---")
    st.subheader("Scheduled Reports")
    
    # Placeholder for scheduled reports list
    if 'scheduled_reports' not in st.session_state:
        st.session_state.scheduled_reports = []
    
    if st.session_state.scheduled_reports:
        for report in st.session_state.scheduled_reports:
            with st.expander(f"Report to {report['email']} ({report['schedule']})"):
                st.write(f"Format: {report['format']}")
                st.write(f"Last sent: {report.get('last_sent', 'Never')}")
                if st.button(f"Delete {report['email']}", key=f"del_{report['email']}"):
                    st.session_state.scheduled_reports = [r for r in st.session_state.scheduled_reports if r['email'] != report['email']]
                    st.experimental_rerun()
    else:
        st.info("No scheduled reports. Configure a report above.")
    
    # Add documentation/help section
    with st.expander("Need help?"):
        st.markdown("""
        ### Email Reports Guide
        
        **Sending Reports**
        - Enter the recipient's email address
        - Select the report format (PDF or JSON)
        - Choose when to send the report
        - Click "Send Report"
        
        **Troubleshooting**
        - Make sure your email settings are correct in the environment variables
        - Check your spam folder if you don't receive the email
        - For Gmail, you may need to use an App Password if 2FA is enabled
        
        **Scheduled Reports**
        - Scheduled reports will be sent automatically at the specified interval
        - You can manage scheduled reports in the section below
        """)

def main():
    """Main entry point for the application."""
    try:
        logging.info("Starting PharmaGenie AI application")
        asyncio.run(main_app())
    except TypeError as e:
        if "unhashable type: 'set'" in str(e):
            st.error("A data processing error occurred. This is often due to an agent returning an unexpected data structure. Please check the agent implementations.")
            st.exception(e)
        else:
            st.error("A critical error occurred. Please check the logs for details.")
            st.exception(e)
    except Exception as e:
        error_msg = f"Application error: {str(e)}"
        logging.error(error_msg, exc_info=True)
        st.error("A critical error occurred. Please check the logs for details.")
        st.exception(e)
    finally:
        logging.info("Application shutdown")

if __name__ == "__main__":
    main()