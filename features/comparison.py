# features/comparison.py
from typing import List, Dict, Any
import pandas as pd
import plotly.express as px
import streamlit as st

class DrugComparison:
    def __init__(self):
        self.drugs = []
        
    def add_drug(self, drug_data: Dict[str, Any]):
        self.drugs.append(drug_data)
        
    def get_comparison_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.drugs)
    
    def plot_comparison(self, metric: str) -> None:
        if not self.drugs:
            st.warning("No drugs to compare")
            return
            
        df = self.get_comparison_dataframe()
        fig = px.bar(
            df,
            x='name',
            y=metric,
            title=f"Comparison by {metric}",
            color='name',
            labels={'name': 'Drug', metric: metric.replace('_', ' ').title()}
        )
        st.plotly_chart(fig, use_container_width=True)
        
    def generate_insights(self) -> str:
        if len(self.drugs) < 2:
            return "Add at least two drugs to generate insights"
            
        # Simple comparison logic - can be enhanced with AI
        best_drug = max(self.drugs, key=lambda x: x.get('score', 0))
        return f"Based on the analysis, {best_drug['name']} shows the highest potential with a score of {best_drug['score']}."