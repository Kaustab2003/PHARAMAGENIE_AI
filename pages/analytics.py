# pages/analytics.py
"""Analytics Dashboard module for drug comparison and statistics visualization"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Optional
import sys
import os
from pathlib import Path

# Add parent directory to path to import from utils
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from utils.drug_info_fetcher import DrugInfoFetcher
from utils.molecule_viz import MoleculeVisualizer

__all__ = ['AnalyticsDashboard']

class AnalyticsDashboard:
    """Analytics Dashboard for drug comparison and statistics visualization."""
    
    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initialize the Analytics Dashboard.
        
        Args:
            data: Optional DataFrame containing drug analysis data.
                 If not provided, sample data will be generated.
        """
        # Initialize dashboard data
        self.data = data if data is not None else self._generate_sample_data()
        
        # Initialize drug information fetcher and molecule visualizer
        try:
            self.drug_fetcher = DrugInfoFetcher()
            self.mol_viz = MoleculeVisualizer()
        except Exception as e:
            st.error(f"Error initializing components: {str(e)}")
            raise
        
    def compare_drugs(self, drug1: str, drug2: str):
        """Compare two drugs and display their information side by side"""
        
        # Create columns for side-by-side comparison
        col1, col2 = st.columns(2)
        
        # Fetch detailed information for both drugs
        info1 = self.drug_fetcher.get_drug_details(drug1)
        info2 = self.drug_fetcher.get_drug_details(drug2)
        
        if not info1 or not info2:
            st.error("Could not fetch information for one or both drugs")
            return
            
        # Compare uses and indications
        st.subheader("💊 Uses and Indications")
        uses1 = info1.get('indications', 'Not available')
        uses2 = info2.get('indications', 'Not available')
        cols = st.columns(2)
        with cols[0]:
            st.write(f"**{drug1}**")
            st.write(uses1)
        with cols[1]:
            st.write(f"**{drug2}**")
            st.write(uses2)
            
        # Compare dosage information
        st.subheader("💉 Dosage Information")
        dose1 = info1.get('dosage', 'Not available')
        dose2 = info2.get('dosage', 'Not available')
        cols = st.columns(2)
        with cols[0]:
            st.write(f"**{drug1}**")
            st.write(dose1)
        with cols[1]:
            st.write(f"**{drug2}**")
            st.write(dose2)
            
        # Compare adverse effects
        st.subheader("⚠️ Adverse Effects")
        effects1 = info1.get('adverse_effects', 'Not available')
        effects2 = info2.get('adverse_effects', 'Not available')
        cols = st.columns(2)
        with cols[0]:
            st.write(f"**{drug1}**")
            st.write(effects1)
        with cols[1]:
            st.write(f"**{drug2}**")
            st.write(effects2)
            
        # Compare mechanism of action
        st.subheader("🔬 Mechanism of Action")
        mech1 = info1.get('mechanism', 'Not available')
        mech2 = info2.get('mechanism', 'Not available')
        cols = st.columns(2)
        with cols[0]:
            st.write(f"**{drug1}**")
            st.write(mech1)
        with cols[1]:
            st.write(f"**{drug2}**")
            st.write(mech2)
            
        # Compare molecular structure
        st.subheader("🧬 Molecular Structure")
        cols = st.columns(2)
        with cols[0]:
            st.write(f"**{drug1}**")
            smiles1 = info1.get('smiles')
            if smiles1:
                mol_img1 = self.mol_viz.generate_molecule_image(smiles1)
                st.image(mol_img1)
            else:
                st.write("Structure not available")
        with cols[1]:
            st.write(f"**{drug2}**")
            smiles2 = info2.get('smiles')
            if smiles2:
                mol_img2 = self.mol_viz.generate_molecule_image(smiles2)
                st.image(mol_img2)
            else:
                st.write("Structure not available")
                
        # Compare safety information
        st.subheader("🛡️ Safety Information")
        safety1 = info1.get('safety_info', 'Not available')
        safety2 = info2.get('safety_info', 'Not available')
        cols = st.columns(2)
        with cols[0]:
            st.write(f"**{drug1}**")
            st.write(safety1)
        with cols[1]:
            st.write(f"**{drug2}**")
            st.write(safety2)

    def _generate_sample_data(self) -> pd.DataFrame:
        """Generate sample data for demonstration"""
        np.random.seed(42)
        dates = [datetime.now() - timedelta(days=x) for x in range(30)]
        drugs = ['Metformin', 'Aspirin', 'Ibuprofen', 'Atorvastatin', 'Sertraline']
        areas = ['Oncology', 'Cardiology', 'Neurology', 'Endocrinology', 'Psychiatry']
        
        data = []
        for date in dates:
            for drug in drugs:
                area = np.random.choice(areas)
                score = np.random.normal(70, 15)
                score = max(0, min(100, score))  # Clamp between 0-100
                
                data.append({
                    'date': date.date(),
                    'drug': drug,
                    'therapeutic_area': area,
                    'score': round(score, 2),
                    'success': 1 if score > 70 else 0
                })
                
        return pd.DataFrame(data)
    
    def show_overview(self):
        st.title("📈 Analytics Dashboard")
        
        # Manual drug input section
        st.subheader("🔍 Drug Comparison")
        col1, col2 = st.columns(2)
        
        with col1:
            drug1 = st.text_input("Enter first drug name", "Metformin")
        with col2:
            drug2 = st.text_input("Enter second drug name", "Aspirin")
            
        if st.button("Compare Drugs"):
            if drug1 and drug2:
                self.compare_drugs(drug1, drug2)
            else:
                st.warning("Please enter both drug names")
        
        st.divider()
        
        # Statistics Overview
        st.subheader("📊 Statistics Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Analyses", len(self.data))
        with col2:
            st.metric("Success Rate", f"{self.data['success'].mean()*100:.1f}%")
        with col3:
            st.metric("Unique Drugs", self.data['drug'].nunique())
        
        # Date range selector
        min_date = self.data['date'].min()
        max_date = self.data['date'].max()
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            filtered_data = self.data[
                (self.data['date'] >= date_range[0]) & 
                (self.data['date'] <= date_range[1])
            ]
        else:
            filtered_data = self.data
        
        # Time series of scores
        st.subheader("Score Trends Over Time")
        fig = px.line(
            filtered_data,
            x='date',
            y='score',
            color='drug',
            title="Scores Over Time",
            labels={'date': 'Date', 'score': 'Score', 'drug': 'Drug'}
        )
        # Use container width and Plotly config instead of deprecated keyword args
        st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
        
        # Success rate by therapeutic area
        st.subheader("Success Rate by Therapeutic Area")
        success_rates = filtered_data.groupby('therapeutic_area')['success'].mean().reset_index()
        fig = px.bar(
            success_rates,
            x='therapeutic_area',
            y='success',
            title="Success Rate by Therapeutic Area",
            labels={'therapeutic_area': 'Therapeutic Area', 'success': 'Success Rate'}
        )
        # Use container width and Plotly config instead of deprecated keyword args
        st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
        
        # Heatmap of drug vs therapeutic area
        st.subheader("Drug Performance Heatmap")
        heatmap_data = filtered_data.pivot_table(
            index='drug',
            columns='therapeutic_area',
            values='score',
            aggfunc='mean'
        )
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Therapeutic Area", y="Drug", color="Score"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            aspect="auto"
        )
        fig.update_xaxes(side="bottom")
        # Use container width and Plotly config instead of deprecated keyword args
        st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
        
        # Raw data
        if st.checkbox("Show raw data"):
            st.subheader("Raw Data")
            st.dataframe(filtered_data)

# Example usage in a Streamlit app
if __name__ == "__main__":
    dashboard = AnalyticsDashboard()
    dashboard.show_overview()