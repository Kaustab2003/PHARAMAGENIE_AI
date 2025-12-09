# utils/drug_info_fetcher.py
"""
Drug Information Fetcher Module
Fetches comprehensive drug information from free APIs (RxNav and PubChem)
"""

import requests
import logging
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

class DrugInfoFetcher:
    """Fetches drug information from RxNav and PubChem APIs."""
    
    def __init__(self):
        """Initialize the DrugInfoFetcher with API base URLs and a session."""
        self.rxnav_base = "https://rxnav.nlm.nih.gov/REST"
        self.pubchem_base = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.fda_base = "https://api.fda.gov/drug"
        
        # Initialize session with custom user agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PharmaGenieAI/1.0 (Educational Project)'
        })
        
    @lru_cache(maxsize=100)
    def get_rxcui(self, drug_name: str) -> Optional[str]:
        """
        Get RxCUI (unique drug identifier) from RxNav.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            RxCUI string or None if not found
        """
        try:
            url = f"{self.rxnav_base}/rxcui.json"
            params = {'name': drug_name}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rxcui_list = data.get("idGroup", {}).get("rxnormId", [])
            
            if rxcui_list:
                return rxcui_list[0]
            return None
            
        except Exception as e:
            logger.error(f"Error fetching RxCUI for {drug_name}: {str(e)}")
            return None
    
    def get_drug_class(self, rxcui: str) -> str:
        """
        Get drug class/category from RxNav.
        
        Args:
            rxcui: RxNorm Concept Unique Identifier
            
        Returns:
            Drug class string
        """
        try:
            url = f"{self.rxnav_base}/rxclass/class/byRxcui.json"
            params = {
                'rxcui': rxcui,
                'relaSource': 'ATC'  # Anatomical Therapeutic Chemical Classification
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            class_list = data.get("rxclassDrugInfoList", {}).get("rxclassDrugInfo", [])
            
            if class_list:
                classes = [item.get("rxclassMinConceptItem", {}).get("className", "") 
                          for item in class_list]
                return ", ".join(filter(None, classes[:3]))  # Return top 3 classes
            
            return "Classification not available"
            
        except Exception as e:
            logger.error(f"Error fetching drug class for RxCUI {rxcui}: {str(e)}")
            return "Classification not available"
    
    def get_drug_interactions(self, drug_name: str) -> List[Dict[str, str]]:
        """
        Get drug-drug interactions from multiple sources.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            List of dictionaries containing interacting drug information
        """
        interactions: List[Dict[str, str]] = []
        
        # First get RxCUI
        try:
            rxcui = self.get_rxcui(drug_name)
            if not rxcui:
                return [{"drug": "Could not find drug in database", "description": ""}]
        except Exception as e:
            logger.error(f"Error getting RxCUI for {drug_name}: {str(e)}")
            return [{"drug": "Error fetching drug information", "description": ""}]
            
        # Try RxNav's interaction API first
        try:
            url = f"{self.rxnav_base}/interaction/interaction.json"
            params = {'rxcui': rxcui}
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                interaction_groups = data.get("interactionTypeGroup", [])
                
                for group in interaction_groups:
                    for interaction_type in group.get("interactionType", []):
                        for pair in interaction_type.get("interactionPair", []):
                            try:
                                drug = pair["interactionConcept"][1]["sourceConceptItem"]["name"]
                                desc = pair.get("description", "").strip()
                                if desc:
                                    interactions.append({
                                        "drug": drug,
                                        "description": desc
                                    })
                            except (KeyError, IndexError):
                                continue
        except Exception as e:
            logger.warning(f"Error fetching RxNav interactions for {drug_name}: {str(e)}")
            
        # If no interactions found in RxNav, try FDA API
        if not interactions:
            try:
                fda_url = f"{self.fda_base}/drug/label.json"
                params = {
                    'search': f'openfda.generic_name:"{drug_name}" OR openfda.brand_name:"{drug_name}"',
                    'limit': 1
                }
                response = self.session.get(fda_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        result = data['results'][0]
                        
                        if result.get('drug_interactions'):
                            for interaction in result['drug_interactions']:
                                interactions.append({
                                    "drug": "FDA Interaction Warning",
                                    "description": interaction.strip()
                                })
            except Exception as e:
                logger.warning(f"Error fetching FDA interactions for {drug_name}: {str(e)}")
        
        # If we have interactions, deduplicate and limit to top 10
        if interactions:
            unique_interactions: List[Dict[str, str]] = []
            seen = set()
            for item in interactions:
                if item["drug"] not in seen:
                    seen.add(item["drug"])
                    unique_interactions.append(item)
                if len(unique_interactions) >= 10:
                    break
            return unique_interactions
            
        # No interactions found from any source
        return [{"drug": "No known interactions", "description": ""}]
    
    def get_drug_properties(self, rxcui: str) -> Dict:
        """Get comprehensive drug properties from RxNav"""
        try:
            properties = {}
            
            # Get basic drug info including indications
            url = f"{self.rxnav_base}/rxcui/{rxcui}/allProperties.json"
            response = self.session.get(url, params={'prop': 'attributes'}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                properties.update(self._extract_basic_info(data))
            
            # Get additional indications from RxClass
            url = f"{self.rxnav_base}/rxclass/class/byRxcui.json"
            params = {'rxcui': rxcui}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                class_indications = self._extract_indications(data)
                if class_indications:
                    if 'indications' in properties:
                        properties['indications'] += "\n\n" + class_indications
                    else:
                        properties['indications'] = class_indications
            
            # Get NDC properties for dosage
            url = f"{self.rxnav_base}/ndcproperties.json"
            params = {'id': rxcui}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                ndc_data = response.json()
                properties['dosage'] = self._extract_dosage(ndc_data)
                
            return properties
            
        except Exception as e:
            logger.error(f"Error fetching drug properties for RxCUI {rxcui}: {str(e)}")
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching drug properties for RxCUI {rxcui}: {str(e)}")
            return {}
            
    def _extract_basic_info(self, data: Dict) -> Dict:
        """Extract basic drug information from RxNav allProperties endpoint"""
        info = {}
        try:
            properties = data.get("propConceptGroup", {}).get("propConcept", [])
            
            # Collect all indications and uses
            indications = []
            mechanism = []
            
            for prop in properties:
                prop_name = prop.get("propName", "").lower()
                prop_value = prop.get("propValue", "")
                
                if any(word in prop_name for word in ["indication", "use", "treat"]):
                    indications.append(f"- {prop_value}")
                elif any(word in prop_name for word in ["mechanism", "action", "activity"]):
                    mechanism.append(f"- {prop_value}")
                    
            if indications:
                info["indications"] = "\n".join(indications)
            if mechanism:
                info["mechanism"] = "\n".join(mechanism)
                
            return info
            
        except Exception as e:
            logger.error(f"Error extracting basic info: {str(e)}")
            return {}
            
    def _extract_indications(self, data: Dict) -> str:
        """Extract indications from RxClass data"""
        try:
            indications = []
            
            # Extract from rxclassDrugInfoList
            drug_info_list = data.get("rxclassDrugInfoList", {}).get("rxclassDrugInfo", [])
            for item in drug_info_list:
                class_info = item.get("rxclassMinConceptItem", {})
                if class_info.get("classType") == "INDICATION":
                    indications.append(f"- {class_info.get('className', '')}")
                    
            # Extract from rxclassMinConceptList as backup
            if not indications:
                class_info = data.get("rxclassMinConceptList", {}).get("rxclassMinConcept", [])
                for item in class_info:
                    if item.get("classType") == "INDICATION":
                        indications.append(f"- {item.get('className', '')}")
                        
            return "\n".join(indications) if indications else ""
        except Exception:
            return ""
            
    def _extract_dosage(self, data: Dict) -> str:
        """Extract dosage information from NDC properties"""
        try:
            props = data.get("ndcPropertyList", {}).get("ndcProperty", [])
            dosage_info = []
            for prop in props:
                if "dosage" in prop.get("propertyName", "").lower():
                    dosage_info.append(f"{prop['propertyName']}: {prop['propertyValue']}")
            return "\n".join(dosage_info) if dosage_info else "Dosage information not available"
        except Exception:
            return "Dosage information not available"
            
    def get_adverse_effects(self, drug_name: str) -> List[str]:
        """
        Get adverse effects from RxNav and FDA sources.
        
        Args:
            drug_name: Name of the drug to get adverse effects for
            
        Returns:
            List of adverse effects as strings
        """
        try:
            # First get RxCUI if not already provided
            rxcui = self.get_rxcui(drug_name)
            if not rxcui:
                return ["Could not find drug in database"]
            
            # Try RxNav's MED-RT API for adverse effects
            url = f"{self.rxnav_base}/rxclass/class/byRxcui.json"
            params = {'rxcui': rxcui, 'relaSource': 'MEDRT', 'relas': 'has_PE'}
            response = self.session.get(url, params=params, timeout=10)
            
            effects: List[str] = []
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("rxclassDrugInfoList", {}).get("rxclassDrugInfo", []):
                    effect = item.get("rxclassMinConceptItem", {}).get("className", "")
                    if effect and effect not in effects:
                        effects.append(effect)
            
            # If no effects found in RxNav, try FDA API
            if not effects:
                try:
                    fda_url = f"{self.fda_base}/label.json"
                    params = {
                        'search': f'openfda.generic_name:"{drug_name}" OR openfda.brand_name:"{drug_name}"',
                        'limit': 1
                    }
                    response = self.session.get(fda_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            if result.get('adverse_reactions'):
                                effects.extend(result['adverse_reactions'])
                except Exception as e:
                    logger.warning(f"Error fetching FDA adverse effects for {drug_name}: {str(e)}")
            
            return effects if effects else ["No major adverse effects reported"]
            
        except Exception as e:
            logger.error(f"Error fetching adverse effects for {drug_name}: {str(e)}")
            return ["Adverse effects information not available"]
            
    def get_drug_uses(self, drug_name: str) -> str:
        """
        Get drug uses and indications from multiple sources.
        
        Args:
            drug_name: Name of the drug to get uses for
            
        Returns:
            String containing drug uses and indications
        """
        try:
            # Try FDA API first
            fda_url = f"{self.fda_base}/label.json"
            params = {
                'search': f'openfda.generic_name:"{drug_name}" OR openfda.brand_name:"{drug_name}"',
                'limit': 1
            }
            response = self.session.get(fda_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    uses = []
                    result = data['results'][0]
                    
                    # Get indications
                    if result.get('indications_and_usage'):
                        uses.extend([f"- {use.strip()}" for use in result['indications_and_usage']])
                        
                    # Get purpose/use
                    if result.get('purpose'):
                        uses.extend([f"- {purpose.strip()}" for purpose in result['purpose']])
                        
                    if uses:
                        return "\n".join(uses)
            
            # Fallback to RxNav
            rxcui = self.get_rxcui(drug_name)
            if rxcui:
                url = f"{self.rxnav_base}/rxclass/class/byRxcui.json"
                params = {'rxcui': rxcui}
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    uses = []
                    for item in data.get('rxclassDrugInfoList', {}).get('rxclassDrugInfo', []):
                        class_info = item.get('rxclassMinConceptItem', {})
                        if class_info.get('classType') == 'INDICATION':
                            uses.append(f"- {class_info.get('className', '')}")
                    if uses:
                        return "\n".join(uses)
            
            return "No indication information available"
            
        except Exception as e:
            logger.error(f"Error fetching drug uses for {drug_name}: {str(e)}")
            return "Error fetching indication information"

    def get_drug_details(self, drug_name: str) -> Dict:
        """
        Get comprehensive drug information from multiple sources.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            Dictionary containing comprehensive drug information
        """
        details = {
            'name': drug_name,
            'indications': self._get_drug_uses(drug_name),
            'dosage': 'Information not available',
            'adverse_effects': 'Information not available',
            'mechanism': 'Information not available',
            'safety_info': 'Information not available',
            'interactions': 'Information not available',
            'smiles': None
        }
        
        try:
            # Get RxCUI
            rxcui = self.get_rxcui(drug_name)
            if rxcui:
                # Get drug properties
                properties = self.get_drug_properties(rxcui)
                details.update(properties)
                
                # Get drug class
                details['classification'] = self.get_drug_class(rxcui)
                
                # Get adverse effects
                effects = self.get_adverse_effects(rxcui)
                if effects and effects[0] != "Adverse effects information not available":
                    details['adverse_effects'] = "\n".join(f"- {effect}" for effect in effects)
                
                # Get interactions
                interactions = self.get_drug_interactions(drug_name)
                if interactions:
                    # Format interactions, filtering out empty descriptions
                    interaction_texts = []
                    for inter in interactions:
                        drug = inter.get('drug', '')
                        desc = inter.get('description', '').strip()
                        if desc:
                            interaction_texts.append(f"- {drug}:\n  {desc}")
                        else:
                            interaction_texts.append(f"- {drug}")
                    details['interactions'] = "\n".join(interaction_texts)
            
            # Get safety information
            safety_info = []
            if details.get('adverse_effects') and details['adverse_effects'] != 'Information not available':
                safety_info.append(f"Adverse Effects:\n{details['adverse_effects']}")
            if details.get('classification'):
                safety_info.append(f"Drug Class:\n{details['classification']}")
            if safety_info:
                details['safety_info'] = "\n\n".join(safety_info)
            else:
                details['safety_info'] = "No detailed safety information available in database"
            
            # Get PubChem information
            pubchem_info = self.get_pubchem_info(drug_name)
            if pubchem_info:
                details['mechanism'] = pubchem_info.get('description', 'Mechanism of action not available')
                mol_info = []
                if pubchem_info.get('molecular_formula'):
                    mol_info.append(f"Molecular Formula: {pubchem_info['molecular_formula']}")
                if pubchem_info.get('molecular_weight'):
                    mol_info.append(f"Molecular Weight: {pubchem_info['molecular_weight']}")
                if pubchem_info.get('iupac_name'):
                    mol_info.append(f"IUPAC Name: {pubchem_info['iupac_name']}")
                details['molecular_info'] = "\n".join(mol_info)
                
                # Get SMILES for visualization
                smiles = self.get_smiles(drug_name)
                if smiles:
                    details['smiles'] = smiles
            
            # Use AI to fill in missing information
            details = self._enhance_with_ai(details, drug_name)
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching comprehensive info for {drug_name}: {str(e)}")
            return details
    
    def _enhance_with_ai(self, details: Dict, drug_name: str) -> Dict:
        """Use AI to fill in missing drug information, with fallback to static database."""
        
        # Static knowledge base for common drugs
        drug_knowledge = {
            'metformin': {
                'dosage': 'Initial: 500 mg twice daily or 850 mg once daily with meals. Maximum: 2,550 mg/day in divided doses. Extended-release: 500-2,000 mg once daily with evening meal.',
                'mechanism': 'Decreases hepatic glucose production, decreases intestinal absorption of glucose, and improves insulin sensitivity by increasing peripheral glucose uptake and utilization.',
                'smiles': 'CN(C)C(=N)NC(=N)N'
            },
            'aspirin': {
                'dosage': 'Pain/fever: 325-650 mg every 4-6 hours. Cardiovascular protection: 75-325 mg once daily. Maximum: 4,000 mg/day for pain.',
                'mechanism': 'Inhibits cyclooxygenase (COX) enzymes, reducing prostaglandin synthesis. Irreversibly acetylates COX-1 and COX-2, preventing platelet aggregation and reducing inflammation, pain, and fever.',
                'smiles': 'CC(=O)Oc1ccccc1C(=O)O'
            },
            'ibuprofen': {
                'dosage': 'Adults: 200-400 mg every 4-6 hours as needed. Maximum: 3,200 mg/day (prescription strength) or 1,200 mg/day (OTC).',
                'mechanism': 'Nonsteroidal anti-inflammatory drug (NSAID) that inhibits COX-1 and COX-2 enzymes, reducing prostaglandin synthesis and providing anti-inflammatory, analgesic, and antipyretic effects.',
                'smiles': 'CC(C)Cc1ccc(cc1)C(C)C(=O)O'
            },
            'lisinopril': {
                'dosage': 'Hypertension: Initial 10 mg once daily, usual range 20-40 mg/day. Heart failure: Initial 5 mg once daily, target 20-40 mg/day.',
                'mechanism': 'ACE inhibitor that prevents conversion of angiotensin I to angiotensin II, reducing vasoconstriction and aldosterone secretion, thereby lowering blood pressure and reducing cardiac workload.',
                'smiles': 'NCCCC[C@H](N[C@@H](CCc1ccccc1)C(=O)O)C(=O)N1CCC[C@H]1C(=O)O'
            },
            'atorvastatin': {
                'dosage': 'Initial: 10-20 mg once daily. Usual range: 10-80 mg once daily. Can be taken at any time without regard to meals.',
                'mechanism': 'HMG-CoA reductase inhibitor (statin) that competitively inhibits the rate-limiting enzyme in cholesterol biosynthesis, reducing LDL cholesterol and total cholesterol levels.',
                'smiles': 'CC(C)c1c(c(c(n1CC[C@H](C[C@H](CC(=O)O)O)O)c2ccc(cc2)F)c3ccccc3)C(=O)Nc4ccccc4'
            },
            'omeprazole': {
                'dosage': 'GERD: 20 mg once daily for 4-8 weeks. H. pylori: 20 mg twice daily (with antibiotics). Best taken before meals.',
                'mechanism': 'Proton pump inhibitor that suppresses gastric acid secretion by irreversibly blocking the H+/K+-ATPase enzyme system in gastric parietal cells.',
                'smiles': 'COc1ccc2c(c1)[nH]c(n2)S(=O)Cc3ncc(c(c3C)OC)C'
            }
        }
        
        drug_lower = drug_name.lower()
        
        # Check static knowledge base first
        if drug_lower in drug_knowledge:
            knowledge = drug_knowledge[drug_lower]
            if details.get('dosage') == 'Information not available' or details.get('dosage') == 'Dosage information not available':
                details['dosage'] = knowledge.get('dosage', details['dosage'])
            if details.get('mechanism') in ['Information not available', 'Mechanism of action not available', 'Description not available']:
                details['mechanism'] = knowledge.get('mechanism', details['mechanism'])
            if not details.get('smiles') or details['smiles'] == 'Not available':
                details['smiles'] = knowledge.get('smiles', details.get('smiles'))
            return details
        
        # Try AI enhancement for drugs not in static database
        try:
            from utils.api_client import get_api_client
            
            missing_fields = []
            if details.get('dosage') in ['Information not available', 'Dosage information not available']:
                missing_fields.append('dosage')
            if details.get('mechanism') in ['Information not available', 'Mechanism of action not available', 'Description not available']:
                missing_fields.append('mechanism')
            if not details.get('smiles'):
                missing_fields.append('structure')
            
            if not missing_fields:
                return details
            
            # Get AI-powered information
            api_client = get_api_client()
            
            prompt = f"""Provide concise information for the drug "{drug_name}":
"""
            
            if 'dosage' in missing_fields:
                prompt += "\n1. DOSAGE: Typical adult dosage (2-3 sentences)"
            if 'mechanism' in missing_fields:
                prompt += "\n2. MECHANISM OF ACTION: How the drug works (2-3 sentences)"
            if 'structure' in missing_fields:
                prompt += "\n3. SMILES: SMILES notation for molecular structure (just the SMILES string)"
            
            prompt += "\n\nFormat your response as:\nDOSAGE: [info]\nMECHANISM: [info]\nSMILES: [notation]"
            
            response = api_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a pharmaceutical database assistant. Provide accurate, concise drug information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            if content:
                # Parse response
                lines = content.strip().split('\n')
                for line in lines:
                    if line.startswith('DOSAGE:') and 'dosage' in missing_fields:
                        details['dosage'] = line.replace('DOSAGE:', '').strip()
                    elif line.startswith('MECHANISM:') and 'mechanism' in missing_fields:
                        details['mechanism'] = line.replace('MECHANISM:', '').strip()
                    elif line.startswith('SMILES:') and 'structure' in missing_fields:
                        smiles = line.replace('SMILES:', '').strip()
                        if smiles and smiles != 'Not available':
                            details['smiles'] = smiles
            
            return details
            
        except Exception as e:
            logger.error(f"Error enhancing with AI: {str(e)}")
            return details

    def get_smiles(self, drug_name: str) -> Optional[str]:
        """
        Get SMILES notation for a drug from PubChem.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            SMILES string or None if not found
        """
        try:
            # Get CID first
            url = f"{self.pubchem_base}/compound/name/{drug_name}/cids/JSON"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            cid = data.get("IdentifierList", {}).get("CID", [None])[0]
            
            if not cid:
                return None
                
            # Get SMILES using CID
            url = f"{self.pubchem_base}/compound/cid/{cid}/property/CanonicalSMILES/JSON"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            properties = data.get("PropertyTable", {}).get("Properties", [{}])[0]
            
            return properties.get("CanonicalSMILES")
            
        except Exception as e:
            logger.error(f"Error fetching SMILES for {drug_name}: {str(e)}")
            return None
            
    def get_pubchem_info(self, drug_name: str) -> Dict:
        """
        Get drug information from PubChem.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            Dictionary with drug information
        """
        info = {
            "description": "Description not available",
            "molecular_formula": "N/A",
            "molecular_weight": "N/A",
            "iupac_name": "N/A",
            "synonyms": []
        }
        
        try:
            # Get CID (Compound ID)
            url = f"{self.pubchem_base}/compound/name/{drug_name}/cids/JSON"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            cid = data.get("IdentifierList", {}).get("CID", [None])[0]
            
            if not cid:
                return info
            
            # Get compound properties
            url = f"{self.pubchem_base}/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IUPACName/JSON"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            properties = data.get("PropertyTable", {}).get("Properties", [{}])[0]
            
            info["molecular_formula"] = properties.get("MolecularFormula", "N/A")
            info["molecular_weight"] = properties.get("MolecularWeight", "N/A")
            info["iupac_name"] = properties.get("IUPACName", "N/A")
            
            # Get description
            url = f"{self.pubchem_base}/compound/cid/{cid}/description/JSON"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                descriptions = data.get("InformationList", {}).get("Information", [])
                if descriptions:
                    info["description"] = descriptions[0].get("Description", "Description not available")
            
            # Get synonyms
            url = f"{self.pubchem_base}/compound/cid/{cid}/synonyms/JSON"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                synonyms = data.get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
                info["synonyms"] = synonyms[:10]  # Limit to 10 synonyms
            
        except Exception as e:
            logger.error(f"Error fetching PubChem info for {drug_name}: {str(e)}")
        
        return info

    def _get_drug_uses(self, drug_name: str) -> str:
        """Return common uses for a small set of well-known drugs as a fallback."""
        common_uses = {
            "aspirin": "Pain relief, fever reduction, anti-inflammatory, and prevention of blood clots",
            "ibuprofen": "Pain relief, fever reduction, anti-inflammatory",
            "paracetamol": "Pain relief and fever reduction",
            "acetaminophen": "Pain relief and fever reduction",
            "metformin": "Treatment of type 2 diabetes (improves insulin sensitivity)",
            "atorvastatin": "Treatment of high cholesterol to reduce cardiovascular risk",
            "omeprazole": "Reduction of gastric acid production for GERD and peptic ulcers",
            "amoxicillin": "Treatment of bacterial infections (various indications)",
            "lisinopril": "Treatment of high blood pressure and heart failure",
            "caffeine": "Stimulant; sometimes used in headache preparations"
        }

        return common_uses.get(drug_name.strip().lower(), "Information not available")
    
    def get_mechanism_of_action(self, drug_name: str, drug_class: str) -> str:
        """
        Get mechanism of action (using common knowledge base).
        
        Args:
            drug_name: Name of the drug
            drug_class: Drug classification
            
        Returns:
            Mechanism of action description
        """
        # Common mechanisms for well-known drugs
        mechanisms = {
            "aspirin": "Irreversibly inhibits cyclooxygenase (COX) enzymes, reducing prostaglandin synthesis and platelet aggregation",
            "ibuprofen": "Reversibly inhibits COX-1 and COX-2 enzymes, reducing prostaglandin synthesis and inflammation",
            "paracetamol": "Inhibits prostaglandin synthesis in the CNS, affecting pain and fever centers",
            "acetaminophen": "Inhibits prostaglandin synthesis in the CNS, affecting pain and fever centers",
            "metformin": "Decreases hepatic glucose production, decreases intestinal glucose absorption, and improves insulin sensitivity",
            "atorvastatin": "Inhibits HMG-CoA reductase, the rate-limiting enzyme in cholesterol synthesis",
            "lisinopril": "Inhibits angiotensin-converting enzyme (ACE), reducing angiotensin II formation and lowering blood pressure",
            "omeprazole": "Irreversibly inhibits the H+/K+ ATPase enzyme (proton pump) in gastric parietal cells",
            "amoxicillin": "Inhibits bacterial cell wall synthesis by binding to penicillin-binding proteins",
            "metoprolol": "Selectively blocks beta-1 adrenergic receptors in the heart, reducing heart rate and contractility"
        }
        
        drug_lower = drug_name.lower()
        if drug_lower in mechanisms:
            return mechanisms[drug_lower]
        
        # Generic mechanism based on drug class
        if "analgesic" in drug_class.lower():
            return "Reduces pain perception through various mechanisms affecting pain pathways"
        elif "antibiotic" in drug_class.lower():
            return "Inhibits bacterial growth or kills bacteria through various mechanisms"
        elif "antihypertensive" in drug_class.lower():
            return "Lowers blood pressure through various mechanisms affecting cardiovascular system"
        else:
            return "Mechanism of action varies based on drug class and target"
    
    def get_adverse_effects(self, drug_class: str) -> List[str]:
        """
        Get common adverse effects based on drug class.
        
        Args:
            drug_class: Drug classification
            
        Returns:
            List of common adverse effects
        """
        # Common adverse effects by drug class
        effects_map = {
            "analgesic": ["Nausea", "Gastric irritation", "Dizziness", "Liver toxicity (overdose)"],
            "nsaid": ["Gastric ulceration", "Bleeding", "Renal impairment", "Cardiovascular events"],
            "antibiotic": ["Diarrhea", "Nausea", "Allergic reactions", "Antibiotic resistance"],
            "antihypertensive": ["Dizziness", "Fatigue", "Headache", "Electrolyte imbalance"],
            "statin": ["Muscle pain", "Liver enzyme elevation", "Digestive problems", "Memory issues"],
            "antidiabetic": ["Hypoglycemia", "Gastrointestinal upset", "Weight changes", "Lactic acidosis (rare)"]
        }
        
        drug_class_lower = drug_class.lower()
        for key, effects in effects_map.items():
            if key in drug_class_lower:
                return effects
        
        return ["Common: Nausea, headache, dizziness", "Consult healthcare provider for complete list"]
    
    def get_comprehensive_drug_info(self, drug_name: str) -> Dict:
        """
        Get comprehensive drug information from all sources.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            Dictionary with complete drug information
        """
        result = {
            "drug_name": drug_name.title(),
            "status": "success",
            "rxcui": None,
            "drug_class": "Not available",
            "mechanism_of_action": "Not available",
            "uses": "Not available",
            "adverse_effects": [],
            "drug_interactions": [],
            "food_interactions": "Avoid alcohol unless specifically advised by healthcare provider",
            "molecular_info": {},
            "error": None
        }
        
        try:
            # Get RxCUI
            rxcui = self.get_rxcui(drug_name)
            if not rxcui:
                result["status"] = "partial"
                result["error"] = "Drug not found in RxNav database"
                # Still try PubChem
            else:
                result["rxcui"] = rxcui
                
                # Get drug class
                drug_class = self.get_drug_class(rxcui)
                result["drug_class"] = drug_class
                
                # Get interactions
                interactions = self.get_drug_interactions(rxcui)
                result["drug_interactions"] = interactions
                
                # Get adverse effects
                result["adverse_effects"] = self.get_adverse_effects(drug_class)
            
            # Get PubChem information
            pubchem_info = self.get_pubchem_info(drug_name)
            result["molecular_info"] = pubchem_info
            # Use PubChem description when available; otherwise fall back to
            # a small built-in mapping of common uses for popular drugs.
            pubchem_description = (pubchem_info.get("description") or "").strip()
            if pubchem_description and pubchem_description.lower() != "description not available":
                result["uses"] = pubchem_description
            else:
                result["uses"] = self._get_drug_uses(drug_name)
            
            # Get mechanism of action
            result["mechanism_of_action"] = self.get_mechanism_of_action(
                drug_name, 
                result["drug_class"]
            )
            
        except Exception as e:
            logger.error(f"Error in get_comprehensive_drug_info: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)
        
        return result


# Convenience function for easy import
def get_drug_info(drug_name: str) -> Dict:
    """
    Convenience function to get drug information.
    
    Args:
        drug_name: Name of the drug
        
    Returns:
        Dictionary with drug information
    """
    fetcher = DrugInfoFetcher()
    return fetcher.get_comprehensive_drug_info(drug_name)
