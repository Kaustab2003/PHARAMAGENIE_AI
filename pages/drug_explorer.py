# pages/drug_explorer.py
"""
Comprehensive Drug Explorer Page
Combines drug information, molecular visualization, and interactive features
"""

import streamlit as st
from utils.drug_info_fetcher import DrugInfoFetcher
from utils.molecule_viz import MoleculeVisualizer
from agents.report_generator import ReportGenerator
import plotly.graph_objects as go
from datetime import datetime
import base64

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
        
        # Check for error states
        if interactions and interactions[0]['drug'] in ["Could not find drug in database", "Error fetching drug information"]:
            st.error("❌ " + interactions[0]['drug'])
            st.info("💡 This might be due to the drug name spelling or the drug not being in the RxNav database. Try using the generic name or a common brand name.")
        elif not interactions or interactions[0]['drug'] == "No major interactions found":
            st.success("✅ No major drug interactions found in database")
            if interactions and interactions[0].get('description'):
                st.info(interactions[0]['description'])
            else:
                st.info("Always inform your healthcare provider about all medications you're taking.")
        else:
            st.warning(f"⚠️ Found {len(interactions)} potential interactions")
            
            for i, interaction in enumerate(interactions, 1):
                severity_icon = "🔴" if "severe" in interaction.get('description', '').lower() else "🟡"
                with st.expander(f"{severity_icon} {i}. {interaction['drug']}"):
                    if interaction.get('description'):
                        st.write(interaction['description'])
                    else:
                        st.write("Interaction details not available. Consult healthcare provider.")
    
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
    
    # Check for saved search query from voice assistant
    if 'drug_search_query' in st.session_state and st.session_state.get('drug_search_query'):
        st.info(f"🎤 Voice Assistant suggested: **{st.session_state['drug_search_query']}**")
        default_drug = st.session_state['drug_search_query']
    else:
        default_drug = ""
    
    # Initialize services
    fetcher = DrugInfoFetcher()
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        drug_name = st.text_input(
            "🔍 Enter Drug Name:",
            value=default_drug,
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
                
                # Store drug info in session state for reports
                st.session_state['current_drug_info'] = drug_info
                
                # PDF Download Option
                st.markdown("---")
                st.subheader("📄 Export Options")
                
                if st.button("📥 Download PDF Report", type="primary", use_container_width=False):
                    with st.spinner("Generating PDF report..."):
                        try:
                            # Prepare data for PDF
                            pdf_data = {
                                'drug_name': drug_info['drug_name'],
                                'therapeutic_area': drug_info['drug_class'],
                                'report_type': 'Drug Information Report',
                                'overview': {
                                    'Drug Name': drug_info['drug_name'],
                                    'RxCUI': drug_info.get('rxcui', 'N/A'),
                                    'Classification': drug_info['drug_class'],
                                    'Mechanism': drug_info['mechanism_of_action'],
                                    'Uses': drug_info['uses']
                                },
                                'molecular_info': drug_info['molecular_info'],
                                'safety': {
                                    'Adverse Effects': ', '.join(drug_info.get('adverse_effects', [])[:10]),
                                    'Food Interactions': drug_info.get('food_interactions', 'N/A')
                                },
                                'interactions': drug_info.get('drug_interactions', [])
                            }
                            
                            # Generate PDF
                            generator = ReportGenerator()
                            pdf_bytes = generator.generate_pdf(pdf_data)
                            
                            # Create download button
                            b64 = base64.b64encode(pdf_bytes).decode()
                            filename = f"{drug_info['drug_name'].replace(' ', '_')}_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
                            
                            href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Click here if download doesn\'t start automatically</a>'
                            
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=False
                            )
                            st.success("✅ PDF generated successfully!")
                            
                        except Exception as e:
                            st.error(f"❌ Error generating PDF: {str(e)}")
                            st.info("💡 Please try again or contact support if the issue persists.")
    
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

def render_drug_explorer_page():
    """Wrapper function for rendering the drug explorer page."""
    main()

if __name__ == "__main__":
    main()
