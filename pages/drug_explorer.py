# pages/drug_explorer.py
"""
Comprehensive Drug Explorer Page
Combines drug information, molecular visualization, and interactive features
"""

import streamlit as st
from utils.drug_info_fetcher import DrugInfoFetcher
from utils.molecule_viz import MoleculeVisualizer
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Drug Explorer | PharmaGenie AI",
    page_icon="💊",
    layout="wide"
)

def create_property_gauge(value: float, title: str, max_value: float = 500):
    """Create a gauge chart for molecular properties."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_value*0.33], 'color': "lightgray"},
                {'range': [max_value*0.33, max_value*0.66], 'color': "gray"},
                {'range': [max_value*0.66, max_value], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value*0.8
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def display_drug_information(drug_info: dict):
    """Display comprehensive drug information in an organized layout."""
    
    st.markdown("---")
    
    # Header with drug name
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"📋 {drug_info['drug_name']}")
    with col2:
        if drug_info.get('rxcui'):
            st.metric("RxCUI", drug_info['rxcui'])
    
    # Main information tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "🔬 Molecular Info", 
        "⚠️ Safety", 
        "🔄 Interactions",
        "🧬 Structure"
    ])
    
    # Tab 1: Overview
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏷️ Classification")
            st.info(drug_info['drug_class'])
            
            st.subheader("⚙️ Mechanism of Action")
            st.write(drug_info['mechanism_of_action'])
            
        with col2:
            st.subheader("💊 Uses & Indications")
            st.write(drug_info['uses'])
            
            if drug_info['molecular_info'].get('synonyms'):
                with st.expander("📝 Common Names & Synonyms"):
                    for synonym in drug_info['molecular_info']['synonyms'][:10]:
                        st.write(f"• {synonym}")
    
    # Tab 2: Molecular Information
    with tab2:
        mol_info = drug_info['molecular_info']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Molecular Formula", mol_info.get('molecular_formula', 'N/A'))
        with col2:
            st.metric("Molecular Weight", f"{mol_info.get('molecular_weight', 'N/A')} g/mol")
        with col3:
            st.metric("IUPAC Name", "Available" if mol_info.get('iupac_name') != 'N/A' else 'N/A')
        
        if mol_info.get('iupac_name') and mol_info['iupac_name'] != 'N/A':
            with st.expander("🔬 IUPAC Name (Chemical Name)"):
                st.code(mol_info['iupac_name'], language=None)
        
        # Molecular weight visualization
        if mol_info.get('molecular_weight') and mol_info['molecular_weight'] != 'N/A':
            try:
                mw = float(mol_info['molecular_weight'])
                st.plotly_chart(
                    create_property_gauge(mw, "Molecular Weight (g/mol)", 1000),
                    use_container_width=True
                )
            except:
                pass
    
    # Tab 3: Safety Information
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚠️ Adverse Effects")
            if drug_info['adverse_effects']:
                for effect in drug_info['adverse_effects']:
                    st.warning(f"• {effect}")
            else:
                st.info("No specific adverse effects listed. Consult healthcare provider.")
        
        with col2:
            st.subheader("🍽️ Food Interactions")
            st.info(drug_info['food_interactions'])
            
            st.subheader("⚕️ Important Notes")
            st.write("""
            - Always consult a healthcare professional before use
            - Follow prescribed dosage instructions
            - Report any unusual side effects immediately
            - Keep out of reach of children
            """)
    
    # Tab 4: Drug Interactions
    with tab4:
        st.subheader("💊 Drug-Drug Interactions")
        
        interactions = drug_info['drug_interactions']
        if interactions and interactions[0]['drug'] != "No major interactions found":
            st.warning(f"⚠️ Found {len(interactions)} potential interactions")
            
            for i, interaction in enumerate(interactions, 1):
                with st.expander(f"{i}. {interaction['drug']}"):
                    if interaction.get('description'):
                        st.write(interaction['description'])
                    else:
                        st.write("Interaction details not available. Consult healthcare provider.")
        else:
            st.success("✅ No major drug interactions found in database")
            st.info("Always inform your healthcare provider about all medications you're taking.")
    
    # Tab 5: Molecular Structure
    with tab5:
        st.subheader("🧬 Molecular Structure Visualization")
        visualizer = MoleculeVisualizer()
        
        with st.spinner("Loading molecular structure..."):
            visualizer.show_molecule(drug_info['drug_name'])

def main():
    """Main function for the Drug Explorer page."""
    
    # Title and description
    st.title("💊 Comprehensive Drug Explorer")
    st.markdown("""
    Explore detailed drug information including classification, mechanism of action, 
    molecular structure, safety information, and interactions - all powered by free APIs.
    """)
    
    # Initialize services
    fetcher = DrugInfoFetcher()
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        drug_name = st.text_input(
            "🔍 Enter Drug Name:",
            placeholder="e.g., Aspirin, Ibuprofen, Metformin",
            help="Enter the generic or brand name of the drug"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        search_button = st.button("🔍 Search Drug", type="primary", use_container_width=True)
    
    # Quick examples
    st.markdown("**Quick Examples:**")
    example_cols = st.columns(6)
    examples = ["Aspirin", "Ibuprofen", "Paracetamol", "Metformin", "Omeprazole", "Amoxicillin"]
    
    for i, example in enumerate(examples):
        if example_cols[i].button(example, use_container_width=True):
            drug_name = example
            search_button = True
    
    # Process search
    if search_button or (drug_name and len(drug_name) > 2):
        if not drug_name:
            st.warning("⚠️ Please enter a drug name")
        else:
            with st.spinner(f"🔍 Searching for {drug_name}..."):
                drug_info = fetcher.get_comprehensive_drug_info(drug_name)
            
            if drug_info['status'] == 'error':
                st.error(f"❌ Error: {drug_info['error']}")
                st.info("💡 Try checking the spelling or use a different name")
            elif drug_info['status'] == 'partial':
                st.warning(f"⚠️ {drug_info['error']}")
                st.info("Showing available information from PubChem...")
                display_drug_information(drug_info)
            else:
                st.success("✅ Drug information retrieved successfully!")
                display_drug_information(drug_info)
                
                # Download report option
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("📥 Download PDF Report"):
                        st.info("PDF generation feature coming soon!")
                with col2:
                    if st.button("📧 Email Report"):
                        if 'current_analysis' not in st.session_state:
                            st.session_state.current_analysis = drug_info
                        st.session_state.active_page = "Email Reports"
                        st.experimental_rerun()
    
    # Information section
    with st.expander("ℹ️ About Drug Explorer"):
        st.markdown("""
        ### 🎯 Features
        - **Comprehensive Information**: Drug class, mechanism, uses, and more
        - **Molecular Visualization**: Interactive 2D and 3D molecular structures
        - **Safety Data**: Adverse effects and contraindications
        - **Interaction Checker**: Drug-drug and drug-food interactions
        - **Free Data Sources**: Powered by RxNav (NIH) and PubChem APIs
        
        ### 📚 Data Sources
        - **RxNav API**: Drug classification, interactions, and identifiers
        - **PubChem**: Molecular structures, properties, and descriptions
        
        ### ⚠️ Disclaimer
        This tool is for educational and informational purposes only. 
        Always consult qualified healthcare professionals for medical advice.
        
        ### 🔒 Privacy
        No personal data is collected or stored. All searches are anonymous.
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: gray;'>"
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"Data sources: RxNav (NIH) & PubChem"
        f"</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
