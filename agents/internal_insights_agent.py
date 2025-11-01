# agents/internal_insights_agent.py
import random
from datetime import datetime, timedelta
from typing import Dict, List

class InternalInsightsAgent:
    """Simulates an agent that connects to internal R&D and strategic databases."""

    def __init__(self):
        # In-memory 'database' to simulate internal knowledge
        self._internal_db = {}

    def _get_or_create_drug_profile(self, drug_name: str) -> Dict:
        """Creates a consistent, simulated internal profile for a drug if one doesn't exist."""
        drug_key = drug_name.lower()
        if drug_key in self._internal_db:
            return self._internal_db[drug_key]

        # Use a hash for deterministic randomness
        seed = sum(ord(c) for c in drug_key)
        random.seed(seed)

        # --- Simulate Previous Research ---
        num_projects = random.randint(0, 4)
        projects = []
        for i in range(num_projects):
            year = random.randint(2018, 2023)
            status = random.choice(["Completed", "On-Hold", "Pitched", "In-Progress"])
            team = random.choice(["Oncology", "Cardiology", "Neurology", "Immunology"])
            summary = f"Project in {team} exploring {drug_name} for a novel indication. Status: {status}."
            projects.append({
                "title": f"{team} Research Project #{random.randint(100,999)}",
                "date": f"{year}-Q{random.randint(1,4)}",
                "status": status,
                "summary": summary
            })

        # --- Simulate Strategic Fit ---
        fit_score = random.randint(30, 95)  # Score out of 100
        if fit_score > 75:
            level = "High"
            rationale = f"Strongly aligns with our current focus on the {random.choice(['oncology', 'rare diseases', 'immunology'])} pipeline."
        elif fit_score > 50:
            level = "Medium"
            rationale = f"Potential alignment with future strategic interests, but not a current top priority."
        else:
            level = "Low"
            rationale = f"Does not align with our primary therapeutic areas. Represents a diversification opportunity."
        
        strategic_fit = {
            "level": level,
            "score": fit_score,
            "rationale": rationale
        }

        profile = {
            "previous_research": sorted(projects, key=lambda x: x['date'], reverse=True),
            "strategic_fit": strategic_fit,
            "key_insights": [
                f"Internal expertise in the {random.choice(['pharmacokinetics', 'formulation', 'toxicology'])} of {drug_name} is considered {random.choice(['strong', 'moderate', 'nascent'])}.",
                f"A total of {num_projects} internal projects related to {drug_name} have been identified.",
                f"Strategic fit score of {fit_score}/100 suggests a {level.lower()} priority for further investment."
            ]
        }
        
        self._internal_db[drug_key] = profile
        return profile

    def get_internal_insights(self, drug_name: str) -> Dict:
        """Retrieves simulated internal insights for a given drug."""
        return self._get_or_create_drug_profile(drug_name)