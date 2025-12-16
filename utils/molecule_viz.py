# utils/molecule_viz.py
"""Module for handling molecular visualization using RDKit"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import io
import time
import random
from typing import (
    TYPE_CHECKING, Any, Optional, Union, Dict, Tuple, TypeVar, 
    List, Callable, cast
)
from pathlib import Path
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote_plus

# Type variable for RDKit molecule and related types
T = TypeVar('T')
MoleculeType = TypeVar('MoleculeType')
PropertyType = Union[float, int, str]

if TYPE_CHECKING:
    from rdkit import Chem
    from rdkit.Chem import (
        Draw, AllChem, rdDepictor, Descriptors, Lipinski,
        rdchem, rdDepictor
    )
    RDKit_AVAILABLE = True
    RDKitMol = rdchem.Mol
else:
    try:
        from rdkit import Chem
        from rdkit.Chem import (
            Draw, AllChem, rdDepictor, Descriptors, Lipinski
        )
        RDKit_AVAILABLE = True
        RDKitMol = Chem.rdchem.Mol
    except Exception as e:
        # If RDKit is missing, don't crash but show warning
        RDKit_AVAILABLE = False
        Chem = cast(Any, None)
        Draw = cast(Any, None)
        AllChem = cast(Any, None)
        rdDepictor = cast(Any, None)
        Descriptors = cast(Any, None)
        Lipinski = cast(Any, None)
        RDKitMol = cast(Any, None)
        st.warning(
            f"RDKit import failed: {e}\n"
            "If running on Streamlit Cloud, add required system packages (see README)."
        )
import py3Dmol
import streamlit.components.v1 as components
import requests
from typing import Optional, Tuple, Dict, Any
import io
import time
import random
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote_plus
from functools import lru_cache


@st.cache_data(ttl=60 * 60 * 24)
def fetch_smiles_from_pubchem(drug_name: str) -> Optional[str]:
    """Simple cached fetch of CanonicalSMILES from PubChem by name.

    Returns the SMILES string or None on failure.
    """
    if not drug_name:
        return None

    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote_plus(drug_name)}/property/CanonicalSMILES/JSON"
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'PharmaGenieAI/1.0',
            'Accept': 'application/json'
        })
        if resp.status_code == 200:
            j = resp.json()
            props = j.get('PropertyTable', {}).get('Properties', [])
            if props and 'CanonicalSMILES' in props[0]:
                return props[0]['CanonicalSMILES']
    except Exception:
        return None

    return None

class MoleculeVisualizer:
    def __init__(self):
        self.pubchem_urls = [
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound",
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"  # Can add more mirrors here
        ]
        self.current_url_index = 0
        self.session = self._create_session()
        # simple in-memory cache for this visualizer instance (avoids repeat work
        # during a single page interaction)
        self._local_smiles_cache: Dict[str, str] = {}
        
    def _ensure_rdkit(self) -> bool:
        """Return True if RDKit is available, otherwise show an error and return False."""
        if not RDKit_AVAILABLE:
            st.error(
                "RDKit is not installed or required system libraries are missing (e.g. libXrender).\n"
                "On Streamlit Cloud add the required system packages listed in `packages.txt` at the repo root: libxrender1, libxext6, libx11-6, libsm6, libice6, libgl1-mesa-glx, etc."
            )
            return False
        return True
    
    def generate_molecule_image(
        self, 
        smiles: str, 
        size: tuple[int, int] = (300, 300)
    ) -> Optional[Image.Image]:
        """
        Generate a 2D image of a molecule from its SMILES string.
        
        Args:
            smiles: SMILES notation of the molecule
            size: Tuple of (width, height) for the image
            
        Returns:
            PIL Image object or None if generation fails
        """
        if not self._ensure_rdkit():
            return None
            
        try:
            if not smiles:
                return None
                
            # Convert SMILES to RDKit molecule
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                st.warning(f"Could not parse SMILES: {smiles}")
                return None
                
            # Generate 2D coordinates if they don't exist
            if not mol.GetNumConformers():
                rdDepictor.Compute2DCoords(mol)
                
            # Draw the molecule
            return Draw.MolToImage(mol, size=size)
            
        except Exception as e:
            st.error(f"Error generating molecule image: {str(e)}")
            return None
        
    def _create_session(self):
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session
        
    def _switch_url(self):
        """Switch to the next available PubChem URL."""
        self.current_url_index = (self.current_url_index + 1) % len(self.pubchem_urls)
        time.sleep(1)  # Add a small delay when switching URLs
        
    def _make_pubchem_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Make a request to PubChem with retry logic."""
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries):
            base_url = self.pubchem_urls[self.current_url_index]
            url = f"{base_url}/{endpoint}"
            
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=10,
                    headers={
                        'User-Agent': 'PharmaGenieAI/1.0 (https://pharmagenie.example.com; contact@example.com)',
                        'Accept': 'application/json'
                    }
                )
                
                if response.status_code == 200:
                    return response.json(), None
                elif response.status_code == 429:  # Too Many Requests
                    retry_after = int(response.headers.get('Retry-After', 5))
                    time.sleep(retry_after + random.uniform(0, 1))
                    self._switch_url()
                    continue
                else:
                    self._switch_url()
                    
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                self._switch_url()
                time.sleep(1)  # Add a small delay before retrying
                
        return None, last_error or "Unknown error occurred"
        
    def get_molecule_from_pubchem(self, drug_name: str) -> Optional[Chem.rdchem.Mol]:
        """
        Fetch molecule data from PubChem by name with multiple fallback strategies.
        
        Args:
            drug_name: Name of the drug to search for
            
        Returns:
            RDKit Mol object if successful, None otherwise
        """
        if not self._ensure_rdkit():
            return None

        if not drug_name or not drug_name.strip():
            st.warning("Please enter a valid drug name.")
            return None
            
        drug_name = drug_name.strip()
        
        # First, try a cached PubChem lookup (fast on subsequent reruns)
        smiles = fetch_smiles_from_pubchem(drug_name)
        if smiles:
            try:
                mol = Chem.MolFromSmiles(smiles)
                if mol:
                    # cache for this instance as well
                    try:
                        self._local_smiles_cache[drug_name] = Chem.MolToSmiles(mol)
                    except Exception:
                        pass
                    return mol
            except Exception:
                pass

        # Fallback: simple local synonyms (keeps logic minimal)
        lower_name = drug_name.strip().lower()
        common_names = {
            'aspirin': 'CC(=O)OC1=CC=CC=C1C(=O)O',
            'ibuprofen': 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O',
            'paracetamol': 'CC(=O)NC1=CC=C(C=C1)O',
            'metformin': 'CN(C)CCN=C(N)N',
            'atorvastatin': 'CC(C)C(C(=O)O)CC1=CC=C(C=C1)C2=C(C(=C(N2C(=O)C3=CC=CC=C3C4=CC=CC=C4)C)CC5=CC=CC=C5)C'
        }
        if lower_name in common_names:
            try:
                return Chem.MolFromSmiles(common_names[lower_name])
            except Exception:
                return None

        st.warning(f"Could not find molecular data for '{drug_name}'.")
        return None
        
    def _try_exact_name_match(self, drug_name: str) -> Optional[Chem.rdchem.Mol]:
        """Try to get molecule by exact name match."""
        if not self._ensure_rdkit():
            return None

        try:
            # URL-encode names to avoid spaces or special char problems
            endpoint = f"name/{quote_plus(drug_name)}/property/CanonicalSMILES/JSON"
            data, error = self._make_pubchem_request(endpoint)
            
            if data and 'PropertyTable' in data and data['PropertyTable'].get('Properties'):
                for prop in data['PropertyTable']['Properties']:
                    if 'CanonicalSMILES' in prop:
                        mol = Chem.MolFromSmiles(prop['CanonicalSMILES'])
                        if mol is not None:
                            return mol
        except Exception as e:
            st.warning(f"Error in exact name search: {str(e)}")
        return None
        
    def _try_text_search(self, drug_name: str) -> Optional[Chem.rdchem.Mol]:
        """Try a more flexible text search."""
        if not self._ensure_rdkit():
            return None

        try:
            # First get CIDs for the name
            endpoint = f"name/{quote_plus(drug_name)}/cids/JSON"
            data, error = self._make_pubchem_request(endpoint)
            
            if data and 'IdentifierList' in data and data['IdentifierList'].get('CID'):
                # Try to get SMILES for the first CID
                cid = data['IdentifierList']['CID'][0]
                return self._get_mol_by_cid(cid)
        except Exception as e:
            st.warning(f"Error in text search: {str(e)}")
        return None
        
    def _try_smiles_lookup(self, drug_name: str) -> Optional[Chem.rdchem.Mol]:
        """Try to get molecule by common name lookup."""
        if not self._ensure_rdkit():
            return None

        try:
            # Try with common synonyms
            common_names = {
                'aspirin': 'CC(=O)OC1=CC=CC=C1C(=O)O',
                'ibuprofen': 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O',
                'paracetamol': 'CC(=O)NC1=CC=C(C=C1)O',
                'metformin': 'CN(C)CCN=C(N)N',
                'atorvastatin': 'CC(C)C(C(=O)O)CC1=CC=C(C=C1)C2=C(C(=C(N2C(=O)C3=CC=CC=C3C4=CC=CC=C4)C)CC5=CC=CC=C5)C'
            }
            
            lower_name = drug_name.lower()
            if lower_name in common_names:
                return Chem.MolFromSmiles(common_names[lower_name])
                
        except Exception as e:
            st.warning(f"Error in SMILES lookup: {str(e)}")
        return None
        
    def _get_mol_by_cid(self, cid: str) -> Optional[Chem.rdchem.Mol]:
        """Get molecule by PubChem CID."""
        if not self._ensure_rdkit():
            return None

        try:
            endpoint = f"cid/{quote_plus(str(cid))}/property/CanonicalSMILES/JSON"
            data, error = self._make_pubchem_request(endpoint)
            
            if data and 'PropertyTable' in data and data['PropertyTable'].get('Properties'):
                for prop in data['PropertyTable']['Properties']:
                    if 'CanonicalSMILES' in prop:
                        return Chem.MolFromSmiles(prop['CanonicalSMILES'])
        except Exception as e:
            st.warning(f"Error getting molecule by CID: {str(e)}")
        return None
    
    def draw_2d_molecule(
        self,
        mol: Union[RDKitMol, Any],
        size: tuple[int, int] = (400, 300)
    ) -> Optional[Image.Image]:
        """
        Generate a 2D image of the molecule with improved rendering.
        
        Args:
            mol: RDKit molecule object
            size: Tuple of (width, height) for the output image
            
        Returns:
            PIL Image object or None if rendering fails
        """
        if not self._ensure_rdkit():
            return None

        if mol is None:
            return None
            
        try:
            # Generate 2D coordinates if they don't exist
            if not mol.GetNumConformers():
                rdDepictor.Compute2DCoords(mol)
                
            # Generate the image with improved parameters
            img = Draw.MolToImage(
                mol,
                size=size,
                kekulize=True,
                wedgeBonds=True,
                imageType='png',
                fitImage=True,
                highlightAtoms=[],
                highlightBonds=[],
                highlightColor=(0.5, 0.5, 1.0),
                highlightBondWidthMultiplier=10
            )
            return img
            
        except Exception as e:
            st.warning(f"Error generating 2D image: {str(e)}")
            return None
    
    def draw_3d_molecule(self, mol: Chem.rdchem.Mol, width: int = 400, height: int = 300):
        """
        Generate an interactive 3D visualization with improved rendering.
        
        Args:
            mol: RDKit molecule object
            width: Width of the view in pixels
            height: Height of the view in pixels
            
        Returns:
            HTML string with embedded 3Dmol viewer or None if rendering fails
        """
        if not self._ensure_rdkit():
            return None

        if mol is None:
            return None

        try:
            # Make a quick 3D conformer (single embed) and produce an SDF block
            mol3 = Chem.AddHs(mol)
            embed_res = AllChem.EmbedMolecule(mol3, randomSeed=42)
            if embed_res != 0:
                return None
            try:
                AllChem.MMFFOptimizeMolecule(mol3, maxIters=120)
            except Exception:
                pass

            sdf = Chem.MolToMolBlock(mol3)

            # Build a minimal HTML page that uses 3Dmol.js to render the SDF
            # Use a JS template and insert the SDF safely (escaped newlines)
            data_js = sdf.replace('\n', '\\n')
            html = f'''<html>
  <head>
    <meta charset="utf-8" />
    <script src="https://3dmol.csb.pitt.edu/build/3Dmol-min.js"></script>
  </head>
  <body>
    <div id="viewer" style="width:{width}px; height:{height}px; position: relative;"></div>
    <script>
      (function() {{
        var element = document.getElementById('viewer');
        var config = {{backgroundColor: '0xffffff'}};
        var viewer = $3Dmol.createViewer(element, config);
        var data = `{data_js}`;
        try {{
          viewer.addModel(data, 'sdf');
          viewer.setStyle({{}}, {{stick:{{}}}});
          viewer.zoomTo();
          viewer.render();
        }} catch(e) {{
          document.body.innerHTML = '<p>Error rendering 3D view</p>';
        }}
      }})();
    </script>
  </body>
</html>'''
            return html
        except Exception as e:
            st.warning(f"Error generating 3D visualization: {str(e)}")
            return None
    
    def show_molecule(self, drug_name: str):
        """
        Display molecule in both 2D and 3D with enhanced visualization and information.
        
        Args:
            drug_name: Name of the drug to display
        """
        if not self._ensure_rdkit():
            return

        with st.spinner(f"Searching for {drug_name}..."):
            mol = self.get_molecule_from_pubchem(drug_name)
            
        if mol is None:
            st.error(f"Could not find molecular data for '{drug_name}'.\n\n"
                    "Please try one of these common drugs or enter a SMILES string directly:\n"
                    "- Aspirin\n- Ibuprofen\n- Paracetamol\n- Metformin\n- Atorvastatin")
            return
            
            # Display basic molecule info
        try:
            if not RDKit_AVAILABLE:
                st.error("RDKit is required for molecular property calculations")
                return
                
            # Use getattr to safely access potentially missing attributes
            descriptors = {
                'Molecular Weight': lambda m: getattr(Descriptors, 'ExactMolWt')(m),
                'LogP': lambda m: getattr(Descriptors, 'MolLogP')(m),
                'H-Bond Donors': lambda m: getattr(Lipinski, 'NumHDonors')(m),
                'H-Bond Acceptors': lambda m: getattr(Lipinski, 'NumHAcceptors')(m),
                'Rotatable Bonds': lambda m: getattr(Lipinski, 'NumRotatableBonds')(m)
            }
            
            properties = {}
            for name, calc in descriptors.items():
                try:
                    value = calc(mol)
                    properties[name] = round(value, 2) if isinstance(value, float) else value
                except Exception as e:
                    st.warning(f"Could not calculate {name}: {str(e)}")
                    properties[name] = "N/A"
            
            # Display properties in columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Molecular Weight", 
                         f"{properties['Molecular Weight']} g/mol" 
                         if properties['Molecular Weight'] != "N/A" 
                         else "N/A")
                st.metric("LogP", 
                         f"{properties['LogP']}" if properties['LogP'] != "N/A" else "N/A")
            with col2:
                st.metric("H-Bond Donors", properties['H-Bond Donors'])
                st.metric("H-Bond Acceptors", properties['H-Bond Acceptors'])
            with col3:
                st.metric("Rotatable Bonds", properties['Rotatable Bonds'])
                st.metric("Heavy Atoms", mol.GetNumHeavyAtoms())
                
        except Exception as e:
            st.warning(f"Could not calculate all molecular properties: {str(e)}")
        
        # Display 2D and 3D visualizations in tabs
        # NOTE: 3D generation can be slow. Make it optional so the page can
        # render 2D quickly and only compute the 3D view on demand.
        show_3d = st.checkbox(
            "Generate 3D structure (slower)",
            value=False,
            help="Enable to compute and view interactive 3D structure — may take several seconds"
        )

        tab1, tab2 = st.tabs(["2D Structure", "3D Structure"])

        with tab1:
            st.subheader("2D Structure")
            img = self.draw_2d_molecule(mol, size=(600, 400))
            if img:
                # Use use_container_width to avoid deprecated width string
                st.image(img, use_container_width=True)
            else:
                st.warning("Could not generate 2D visualization")

        with tab2:
            st.subheader("3D Structure")
            st.info("Click and drag to rotate, scroll to zoom, right-click to pan")

            # Initialize session state for 3D generation
            session_key = f"show_3d_{drug_name}"
            if session_key not in st.session_state:
                st.session_state[session_key] = show_3d
            
            # If the user enabled 3D generation via checkbox, update session state
            if show_3d:
                st.session_state[session_key] = True
            
            # Check if user clicked the generate button
            gen_clicked = st.button("Generate 3D structure", key=f"gen3d_{drug_name}")
            if gen_clicked:
                st.session_state[session_key] = True
            
            # Display 3D structure if enabled or button was clicked
            if st.session_state[session_key]:
                with st.spinner("Generating 3D structure..."):
                    html = self.draw_3d_molecule(mol, width=600, height=400)
                if html:
                    components.html(html, height=420)
                else:
                    st.warning("Could not generate 3D visualization")
            else:
                st.write("Click 'Generate 3D structure' button or enable the checkbox above to view the 3D molecular structure (this may take several seconds).")
        
        # Add download button
        self._add_download_button(mol, drug_name)
    
    def _add_download_button(self, mol: Chem.rdchem.Mol, drug_name: str):
        """Add a download button for the molecule."""
        if not self._ensure_rdkit():
            return

        try:
            # Generate SDF file
            sdf = Chem.MolToMolBlock(mol)
            
            # Create a clean filename
            clean_name = "".join(c if c.isalnum() else "_" for c in drug_name)
            
            # Add download button
            st.download_button(
                label="Download Structure (SDF)",
                data=sdf,
                file_name=f"{clean_name}.sdf",
                mime="chemical/x-mdl-sdfile",
                help="Download the molecular structure in SDF format"
            )
        except Exception as e:
            st.warning(f"Could not generate download link: {str(e)}")