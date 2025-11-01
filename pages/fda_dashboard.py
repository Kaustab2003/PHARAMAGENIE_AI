import streamlit as st
import pandas as pd
import plotly.express as px
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FDADashboard:
    """Dashboard for displaying FDA drug safety data."""
    
    def __init__(self, fda_agent):
        self.fda_agent = fda_agent
        
    def show_dashboard(self, drug_name: str):
        """Display the FDA safety dashboard for a specific drug."""
        st.header(f"📊 FDA Safety Dashboard: {drug_name}")
        
        # Add filters
        st.sidebar.header("Filters")
        time_frame = st.sidebar.selectbox(
            "Time Frame",
            ["1m", "3m", "6m", "1y", "2y", "5y", "All"],
            index=3
        )
        
        # Fetch data
        with st.spinner("Fetching FDA data..."):
            adverse_events = self.fda_agent.get_drug_adverse_events(
                drug_name=drug_name,
                limit=100,
                time_frame=time_frame if time_frame != "All" else None
            )
            
            label_info = self.fda_agent.get_drug_label(drug_name)
            enforcement = self.fda_agent.get_drug_enforcement_reports(
                drug_name=drug_name,
                limit=10
            )
        
        # Display metrics
        self._display_metrics(adverse_events, enforcement)
        
        # Display charts
        if not adverse_events.empty:
            self._display_adverse_events_chart(adverse_events)
            self._display_reactions_chart(adverse_events)
            
        # Display label information
        self._display_label_info(label_info)
        
        # Display enforcement reports
        if not enforcement.empty:
            self._display_enforcement_reports(enforcement)
    
    def _display_metrics(self, adverse_events: pd.DataFrame, enforcement: pd.DataFrame):
        """Display key metrics."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Adverse Events", len(adverse_events) if not adverse_events.empty else 0)
        with col2:
            if not adverse_events.empty and 'serious' in adverse_events.columns:
                serious = adverse_events['serious'].sum()
                total = len(adverse_events)
                st.metric(
                    "Serious Events",
                    f"{serious} ({serious/total*100:.1f}%)" if total > 0 else "0"
                )
            else:
                st.metric("Serious Events", "N/A")
        with col3:
            if not adverse_events.empty and 'reactions' in adverse_events.columns:
                st.metric("Unique Reactions", adverse_events['reactions'].nunique())
            else:
                st.metric("Unique Reactions", 0)
        with col4:
            st.metric("Enforcement Actions", len(enforcement) if enforcement is not None and not enforcement.empty else 0)
    
    def _display_adverse_events_chart(self, adverse_events: pd.DataFrame):
        """Display adverse events over time."""
        st.subheader("Adverse Events Over Time")
        
        if adverse_events.empty or 'date_received' not in adverse_events.columns:
            st.warning("No date information available for the selected time period.")
            return
            
        try:
            # Make a copy to avoid SettingWithCopyWarning
            df = adverse_events.copy()
            
            # Convert date column to datetime with better error handling
            df['date_received'] = pd.to_datetime(
                df['date_received'], 
                errors='coerce',
                format='%Y%m%d'  # Expected format from FDA API
            )
            
            # Filter out any invalid or NA dates
            df = df[df['date_received'].notna()]
            
            if df.empty:
                st.warning("No valid date information available for the selected time period.")
                return
                
            # Group by month and count events
            df = df.set_index('date_received')
            events_by_month = df.resample('M').size()
            
            if len(events_by_month) == 0:
                st.warning("No data available for the selected time period.")
                return
            
            # Create the plot
            fig = px.area(
                events_by_month,
                title=f"Monthly Adverse Event Reports (Last {len(events_by_month)} Months)",
                labels={'value': 'Number of Reports', 'date_received': 'Date'},
                template='plotly_white'
            )
            
            # Improve the layout
            fig.update_layout(
                showlegend=False,
                xaxis_title="Date",
                yaxis_title="Number of Reports",
                hovermode="x"
            )
            
            # Add range slider
            fig.update_xaxes(
                rangeslider_visible=True,
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all")
                    ])
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            error_msg = f"Error generating events chart: {str(e)}"
            st.error(error_msg)
            logger.error(error_msg, exc_info=True)
    
    def _display_reactions_chart(self, adverse_events: pd.DataFrame):
        """Display most common adverse reactions with improved error handling and data processing."""
        st.subheader("Most Common Adverse Reactions")
        
        if adverse_events.empty:
            st.warning("No adverse event data available.")
            return
            
        if 'reactions' not in adverse_events.columns:
            st.warning("No reaction data available in the dataset.")
            return
        
        try:
            # Initialize list to store all reactions
            all_reactions = []
            
            # Safely process reactions
            for reaction_str in adverse_events['reactions'].dropna():
                if isinstance(reaction_str, str):
                    # Handle different possible delimiters and clean up the text
                    reactions = [
                        r.strip().title()  # Title case for consistency
                        for r in str(reaction_str).replace(';', ',').split(',')
                        if r and r.strip()  # Skip empty strings
                    ]
                    all_reactions.extend(reactions)
            
            if not all_reactions:
                st.info("No reaction data available for the selected time period.")
                return
                
            # Get top 10 reactions
            reaction_counts = pd.Series(all_reactions).value_counts().head(10)
            
            if reaction_counts.empty:
                st.info("No reaction data to display after processing.")
                return
                
            # Create a more informative bar chart
            fig = px.bar(
                reaction_counts,
                orientation='h',
                title="Top 10 Reported Adverse Reactions",
                labels={'value': 'Number of Reports', 'index': 'Reaction'},
                template='plotly_white',
                color=reaction_counts.values,
                color_continuous_scale='Blues'
            )
            
            # Improve the layout
            fig.update_layout(
                showlegend=False,
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title="Number of Reports",
                yaxis_title="Reaction",
                hovermode='closest',
                margin=dict(l=150)  # Add margin for long reaction names
            )
            
            # Add data labels
            fig.update_traces(
                texttemplate='%{x:.0f}',
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add a small note about data source
            st.caption("Source: FDA Adverse Event Reporting System (FAERS)")
            
        except Exception as e:
            error_msg = f"Error generating reactions chart: {str(e)}"
            st.error(error_msg)
            logger.error(error_msg, exc_info=True)
    
    def _display_label_info(self, label_info: Dict):
        """Display drug label information."""
        with st.expander("ℹ️ Drug Label Information", expanded=False):
            if not label_info or 'error' in label_info:
                error_msg = label_info.get('error', 'No label information available')
                st.warning(f"Could not retrieve label information: {error_msg}")
                return
                
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Generic Name", label_info.get('generic_name', 'N/A'))
                st.metric("Manufacturer", label_info.get('manufacturer', 'N/A'))
            with col2:
                st.metric("Purpose", label_info.get('purpose', 'N/A')[:50] + '...' 
                         if label_info.get('purpose') else 'N/A')
            
            if 'warnings' in label_info and label_info['warnings'] != 'N/A':
                with st.expander("View Warnings"):
                    st.write(label_info['warnings'])
    
    def _display_enforcement_reports(self, enforcement: pd.DataFrame):
        """Display FDA enforcement reports."""
        st.subheader("Recent FDA Enforcement Actions")
        
        st.dataframe(
            enforcement[[
                'recall_number', 
                'reason_for_recall', 
                'status', 
                'recall_initiation_date'
            ]],
            column_config={
                "recall_number": "Recall #",
                "reason_for_recall": "Reason",
                "status": "Status",
                "recall_initiation_date": "Date Initiated"
            },
            use_container_width=True,
            hide_index=True
        )

# Example usage
if __name__ == "__main__":
    from agents.fda_agent import FDAAgent
    
    st.set_page_config(
        page_title="FDA Safety Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    # Create a search box for drug name
    drug_name = st.text_input("Enter a drug name:", "ibuprofen")
    
    if drug_name:
        fda_agent = FDAAgent()
        dashboard = FDADashboard(fda_agent)
        dashboard.show_dashboard(drug_name)
