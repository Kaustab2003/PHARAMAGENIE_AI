# agents/patent_agent.py
import random
from datetime import datetime, timedelta
from typing import Dict, List

class PatentLandscapeAgent:
    def get_patent_analysis(self, drug_name: str) -> Dict:
        """
        Generates a dynamic, simulated patent analysis for a given drug.
        In a real-world scenario, this would query patent databases like USPTO, Espacenet, or Google Patents.
        """
        # Use a hash of the drug name for deterministic randomness
        seed = sum(ord(c) for c in drug_name.lower())
        random.seed(seed)

        # --- Generate Patent Data ---
        active_patents_count = random.randint(2, 15)
        patent_timeline = []
        filing_years = sorted([random.randint(2005, 2022) for _ in range(active_patents_count)], reverse=True)
        
        next_expiry_date = None

        for i, year in enumerate(filing_years):
            filing_date = datetime(year, random.randint(1, 12), random.randint(1, 28))
            # Patents typically last 20 years from filing
            expiry_date = filing_date + timedelta(days=20*365)
            
            status = "Active"
            if expiry_date < datetime.now():
                status = "Expired"
            
            patent_timeline.append({
                "patent_number": f"US{random.randint(7, 11)}{random.randint(100, 999)}{random.randint(100, 999)}B{random.randint(1,2)}",
                "filing_date": filing_date.strftime('%Y-%m-%d'),
                "expiry_date": expiry_date.strftime('%Y-%m-%d'),
                "status": status,
                "title": f"Composition and method for {drug_name} formulation" if i % 2 == 0 else f"Method of treating disease using {drug_name}"
            })

            if status == "Active":
                if next_expiry_date is None or expiry_date < next_expiry_date:
                    next_expiry_date = expiry_date

        # --- Determine Freedom to Operate (FTO) ---
        active_core_patents = len([p for p in patent_timeline if p['status'] == 'Active' and 'composition' in p['title'].lower()])
        if active_core_patents == 0:
            fto = "High"
        elif active_core_patents <= 2 and (next_expiry_date and (next_expiry_date.year - datetime.now().year) < 3):
            fto = "Moderate"
        else:
            fto = "Low"

        # --- Generate Key Insights ---
        insights = []
        if next_expiry_date:
            insights.append(f"Key composition patent expires in {next_expiry_date.year}, opening opportunities for generics.")
        
        if fto == "Low":
            insights.append("Low freedom to operate suggests high litigation risk for new market entrants.")
        elif fto == "Moderate":
            insights.append("Moderate FTO indicates potential for strategic partnerships or licensing.")
        else:
            insights.append("High FTO suggests a favorable environment for new product development.")

        formulation_patents = len([p for p in patent_timeline if 'formulation' in p['title'].lower()])
        if formulation_patents > active_patents_count / 2:
            insights.append("A significant number of patents relate to formulation, indicating a mature product lifecycle.")
        else:
            insights.append("Focus on method-of-use patents suggests exploration of new therapeutic areas.")

        return {
            "active_patents": len([p for p in patent_timeline if p['status'] == 'Active']),
            "freedom_to_operate": fto,
            "next_expiry": next_expiry_date.year if next_expiry_date else 'N/A',
            "patent_timeline": patent_timeline,
            "key_insights": insights
        }