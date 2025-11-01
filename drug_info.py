import requests

class DrugInfoFetcher:
    def __init__(self):
        self.base_url = "https://rxnav.nlm.nih.gov/REST"
        self.timeout = 15

    def fetch_drug_info(self, drug_name: str) -> dict:
        try:
            # Step 1: Get RxCUI ID
            rxcui = self._get_rxcui(drug_name)
            if not rxcui:
                return {"error": "Drug not found in RxNav database"}

            # Step 2: Get properties
            props = self._get_drug_properties(rxcui)
            
            # Step 3: Get interactions
            interactions = self._get_drug_interactions(rxcui)

            return {
                "Drug Name": drug_name.title(),
                "Drug Class": self._get_property(props, "class"),
                "Mechanism of Action": self._get_property(props, "mechanism"),
                "Uses": self._get_drug_uses(drug_name),
                "Adverse Effects": self._get_adverse_effects(drug_name),
                "Drug-Drug Interactions": ", ".join(interactions[:5]) or "None found",
                "Drug-Food Interactions": "Avoid alcohol; may increase liver risk"
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"Network error while fetching drug info: {str(e)}"}
        except Exception as e:
            return {"error": f"Error processing drug information: {str(e)}"}

    def _get_rxcui(self, drug_name: str) -> str:
        """Get RxCUI ID for the drug."""
        url = f"{self.base_url}/rxcui.json"
        params = {"name": drug_name}
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("idGroup", {}).get("rxnormId", [None])[0]

    def _get_drug_properties(self, rxcui: str) -> list:
        """Get drug properties from RxNorm."""
        url = f"{self.base_url}/rxcui/{rxcui}/allProperties.json"
        params = {"prop": "all"}
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("propConceptGroup", {}).get("propConcept", [])

    def _get_drug_interactions(self, rxcui: str) -> list:
        """Get drug interactions from RxNav."""
        url = f"{self.base_url}/interaction/interaction.json"
        params = {"rxcui": rxcui}
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        
        interactions = []
        for group in data.get("interactionTypeGroup", []):
            for t in group.get("interactionType", []):
                for i in t.get("interactionPair", []):
                    if "minConceptItem" in i.get("interactionConcept", [{}])[1]:
                        interactions.append(i["interactionConcept"][1]["minConceptItem"].get("name"))
        return [i for i in interactions if i]

    def _get_property(self, props: list, prop_type: str) -> str:
        """Helper to get specific property from props list."""
        values = [p['propValue'] for p in props 
                 if prop_type in p.get('propCategory', '').lower()]
        return ", ".join(values) or "Not found"

    def _get_drug_uses(self, drug_name: str) -> str:
        """Get drug uses with fallback."""
        # This is a simplified version - you can expand this with more detailed logic
        common_uses = {
            "aspirin": "Pain relief, fever reduction, anti-inflammatory, blood thinner",
            "ibuprofen": "Pain relief, fever reduction, anti-inflammatory",
            "metformin": "Type 2 diabetes treatment",
            "atorvastatin": "High cholesterol treatment",
            "lisinopril": "High blood pressure treatment"
        }
        return common_uses.get(drug_name.lower(), "Information not available")

    def _get_adverse_effects(self, drug_name: str) -> str:
        """Get adverse effects with fallback."""
        # This is a simplified version - you can expand this with more detailed logic
        common_effects = {
            "aspirin": "Stomach pain, heartburn, nausea, vomiting, stomach ulcers, bleeding",
            "ibuprofen": "Stomach pain, heartburn, dizziness, headache, high blood pressure",
            "metformin": "Nausea, vomiting, diarrhea, stomach upset, metallic taste",
            "atorvastatin": "Muscle pain, diarrhea, upset stomach, liver problems",
            "lisinopril": "Dizziness, headache, cough, high potassium levels"
        }
        return common_effects.get(drug_name.lower(), "Information not available")
