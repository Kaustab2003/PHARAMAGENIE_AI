import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Optional

# Import the TradeAgent
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.trade_agent import TradeAgent

class TradeDashboard:
    """Dashboard for visualizing international trade data."""
    
    def __init__(self):
        self.trade_agent = TradeAgent()
        self.country_codes = self.trade_agent.get_country_codes()
        self.indicators = self.trade_agent.get_common_indicators()
        self._setup_page_config()
    
    def _setup_page_config(self):
        """Configure the Streamlit page settings."""
        st.set_page_config(
            page_title="Global Trade Dashboard",
            page_icon="🌍",
            layout="wide"
        )
        
        # Custom CSS for better styling
        st.markdown("""
        <style>
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .stMetricValue {
                font-size: 1.2rem !important;
            }
            .stMetricLabel {
                font-size: 0.9rem !important;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def show_dashboard(self):
        """Display the main dashboard interface."""
        st.title("🌍 Global Trade Analysis Dashboard")
        
        # Sidebar filters
        st.sidebar.header("Filters")
        
        # Country selection
        selected_country = st.sidebar.selectbox(
            "Select Country",
            options=list(self.country_codes.items()),
            format_func=lambda x: x[1],  # Show full country name
            index=0,
            key="trade_country_selector"
        )
        country_code = selected_country[0]
        
        # Indicator selection
        selected_indicator = st.sidebar.selectbox(
            "Select Trade Indicator",
            options=list(self.indicators.items()),
            format_func=lambda x: x[1],  # Show full description
            index=0,
            key="trade_indicator_selector"
        )
        indicator_code = selected_indicator[0]
        
        # Year range
        current_year = datetime.now().year
        start_year, end_year = st.sidebar.slider(
            "Select Year Range",
            min_value=1990,
            max_value=current_year,
            value=(current_year - 10, current_year - 1),
            key="trade_year_range_slider"
        )
        
        # Show selected parameters
        with st.sidebar.expander("🔍 Selected Parameters", expanded=False):
            st.write(f"**Country:** {selected_country[1]} ({country_code})")
            st.write(f"**Indicator:** {selected_indicator[1][:50]}...")
            st.write(f"**Years:** {start_year} - {end_year}")
        
        # Fetch data
        with st.spinner(f"Loading trade data for {selected_country[1]}..."):
            df = self.trade_agent.get_trade_data(
                country_code=country_code,
                indicator=indicator_code,
                start_year=start_year,
                end_year=end_year
            )
        
        # Display data or error message
        if df.empty:
            st.error(f"⚠️ No data available for **{selected_country[1]}** ({country_code})")
            st.info("""
            **Possible reasons:**
            - The selected country may not have data for this indicator
            - The year range may not have available data
            - The World Bank API may be temporarily unavailable
            
            **Try:**
            - Selecting a different country (USA, China, Germany, etc.)
            - Adjusting the year range
            - Choosing a different trade indicator
            """)
        else:
            # Display metrics
            self._display_metrics(df, country_code, indicator_code)
            
            # Display charts
            self._display_trend_chart(df, selected_country[1], selected_indicator[1])
            
            # Show trade balance if available
            if indicator_code in ['NE.EXP.GNFS.CD', 'NE.IMP.GNFS.CD']:
                self._show_trade_balance(country_code, start_year, end_year)
            
            # Show data table
            with st.expander("View Raw Data"):
                st.dataframe(
                    df[['year', 'value']].rename(columns={
                        'year': 'Year',
                        'value': selected_indicator[1].split('(')[0].strip()
                    }),
                    use_container_width=True
                )
    
    def _display_metrics(self, df: pd.DataFrame, country_code: str, indicator_code: str):
        """Display key metrics."""
        if df.empty:
            return
            
        # Get the most recent year with data
        latest_data = df[df['year'] == df['year'].max()].iloc[0]
        
        # Format value based on magnitude
        value = latest_data['value']
        if value >= 1e12:  # Trillions
            formatted_value = f"${value/1e12:.2f}T"
        elif value >= 1e9:  # Billions
            formatted_value = f"${value/1e9:.2f}B"
        elif value >= 1e6:  # Millions
            formatted_value = f"${value/1e6:.2f}M"
        else:
            formatted_value = f"${value:,.2f}"
        
        # Calculate percentage change from previous year
        if len(df) > 1:
            prev_year = df[df['year'] == df['year'].nlargest(2).iloc[-1]].iloc[0]
            pct_change = ((latest_data['value'] - prev_year['value']) / prev_year['value']) * 100
        else:
            pct_change = 0
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Latest Value",
                formatted_value,
                f"{pct_change:+.1f}% from previous year"
            )
        with col2:
            st.metric(
                "Year",
                int(latest_data['year'])
            )
        with col3:
            st.metric(
                "Data Points",
                len(df)
            )
        with col4:
            st.metric(
                "Time Range",
                f"{df['year'].min()} - {df['year'].max()}"
            )
    
    def _display_trend_chart(self, df: pd.DataFrame, country_name: str, indicator_name: str):
        """Display the main trend chart."""
        st.subheader(f"{indicator_name} - {country_name}")
        
        # Determine appropriate y-axis format
        max_value = df['value'].max()
        if max_value >= 1e12:  # Trillions
            yaxis_tickformat = '$.2sT'
            hover_format = '$,.2f'
            yaxis_title = 'Value (Trillions USD)'
        elif max_value >= 1e9:  # Billions
            yaxis_tickformat = '$.2sB'
            hover_format = '$,.2f'
            yaxis_title = 'Value (Billions USD)'
        elif max_value >= 1e6:  # Millions
            yaxis_tickformat = '$.2sM'
            hover_format = '$,.2f'
            yaxis_title = 'Value (Millions USD)'
        else:
            yaxis_tickformat = '$,.0f'
            hover_format = '$,.0f'
            yaxis_title = 'Value (USD)'
        
        # Create the figure
        fig = px.line(
            df,
            x='year',
            y='value',
            title=f"{indicator_name} - {country_name} ({df['year'].min()} - {df['year'].max()})",
            labels={'year': 'Year', 'value': yaxis_title},
            markers=True
        )
        
        # Update layout for better visualization
        fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(
                tickformat=yaxis_tickformat,
                title=yaxis_title
            ),
            hovermode='x unified',
            template='plotly_white'
        )
        
        # Update hover template
        fig.update_traces(
            hovertemplate=f'<b>Year</b>: %{{x}}<br>' +
                         f'<b>Value</b>: {hover_format}' + '<extra></extra>'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_trade_balance(self, country_code: str, start_year: int, end_year: int):
        """Display trade balance information."""
        with st.spinner("Calculating trade balance..."):
            trade_balance = self.trade_agent.get_trade_balance(
                country_code=country_code,
                start_year=start_year,
                end_year=end_year
            )
        
        if not trade_balance.empty:
            st.subheader("Trade Balance")
            
            # Calculate metrics
            latest_balance = trade_balance.iloc[-1]
            balance_status = "Surplus" if latest_balance['trade_balance'] >= 0 else "Deficit"
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Trade Balance",
                    f"${latest_balance['trade_balance']/1e9:,.2f}B",
                    balance_status
                )
            with col2:
                st.metric(
                    "Exports",
                    f"${latest_balance['value_exports']/1e9:,.2f}B"
                )
            with col3:
                st.metric(
                    "Imports",
                    f"${latest_balance['value_imports']/1e9:,.2f}B"
                )
            
            # Plot trade balance over time
            fig = go.Figure()
            
            # Add exports and imports
            fig.add_trace(go.Scatter(
                x=trade_balance['year'],
                y=trade_balance['value_exports'],
                name='Exports',
                line=dict(color='#2ecc71', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=trade_balance['year'],
                y=trade_balance['value_imports'],
                name='Imports',
                line=dict(color='#e74c3c', width=2)
            ))
            
            # Add trade balance area
            fig.add_trace(go.Scatter(
                x=trade_balance['year'].tolist() + trade_balance['year'].tolist()[::-1],
                y=trade_balance['value_exports'].tolist() + trade_balance['value_imports'].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(46, 204, 113, 0.2)',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Update layout
            fig.update_layout(
                title='Exports vs Imports Over Time',
                xaxis_title='Year',
                yaxis_title='Value (USD)',
                hovermode='x unified',
                template='plotly_white',
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Main function to run the dashboard
if __name__ == "__main__":
    dashboard = TradeDashboard()
    dashboard.show_dashboard()
