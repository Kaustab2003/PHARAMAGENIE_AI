# pages/molecule_visualizer.py
import streamlit as st
from utils.molecule_viz import MoleculeVisualizer

# Set page configuration
st.set_page_config(
    page_title="Molecule Visualizer | PharmaGenie AI",
    page_icon="🔬",
    layout="wide"
)

def main():
    """Main function to run the Molecule Visualizer page."""
    st.title("🔬 Molecule Visualizer")
    st.markdown("""
    Visualize molecular structures in 2D and 3D. Enter a drug name or SMILES string to get started.
    """)
    
    # Initialize the visualizer
    visualizer = MoleculeVisualizer()
    
    # Add a search box
    drug_name = st.text_input(
        "Enter a drug name (e.g., Aspirin, Ibuprofen) or SMILES string:",
        placeholder="e.g., Aspirin, Ibuprofen, or CC(=O)OC1=CC=CC=C1C(=O)O"
    )
    
    # Add some example buttons
    st.markdown("**Try these examples:**")
    cols = st.columns(5)
    examples = ["Aspirin", "Ibuprofen", "Paracetamol", "Metformin", "Caffeine"]
    
    for i, example in enumerate(examples):
        if cols[i].button(example):
            drug_name = example
    
    # Add a search button
    search_clicked = st.button("Visualize Molecule")
    
    # Process the search
    if search_clicked and drug_name:
        with st.spinner("Searching for molecule..."):
            visualizer.show_molecule(drug_name)
    elif search_clicked and not drug_name:
        st.warning("Please enter a drug name or SMILES string.")
    
    # Add some helpful information in an expander
    with st.expander("ℹ️ About the Molecule Visualizer"):
        st.markdown("""
        ### How to Use
        - Enter a drug name (e.g., "Aspirin") or a SMILES string in the search box
        - Click "Visualize Molecule" or press Enter
        - View the 2D and 3D representations of the molecule
        - Download the structure in SDF format if needed
        
        ### Features
        - **2D Structure**: Clean 2D representation with atom numbering
        - **3D Structure**: Interactive 3D visualization (rotate, zoom, pan)
        - **Molecular Properties**: Key properties like molecular weight, LogP, etc.
        - **Download**: Save the molecular structure in SDF format
        
        ### Tips
        - For best results, use standard drug names
        - Try the example buttons for quick access to common drugs
        - The visualizer uses PubChem as the primary data source
        """)

if __name__ == "__main__":
    main()
