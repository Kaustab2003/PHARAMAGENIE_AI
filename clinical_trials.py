import requests
from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import random

logger = logging.getLogger(__name__)

class ClinicalTrialsFetcher:
    def __init__(self):
        self.base_url = "https://clinicaltrials.gov/api/v2"
        self.timeout = 20
        self.max_retries = 3
        self.session = requests.Session()
        self._update_headers()
        
    def _update_headers(self):
        """Update request headers with random user agents"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
        ]
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def fetch_clinical_trials(self, drug_name: str, condition: str = "") -> Dict[str, Any]:
        """Fetch clinical trials for a given drug and optional condition."""
        if not drug_name.strip():
            return {"error": "Drug name cannot be empty"}

        search_strategies = self._get_search_strategies(drug_name, condition)
        
        for strategy in search_strategies:
            try:
                logger.info(f"Trying search strategy: {strategy}")
                data = self._make_api_request(strategy)
                
                if data and (items := data.get("trials")):
                    processed = self._process_trials(items)
                    if processed["trials"]:
                        return processed
                
                # Add delay between requests
                time.sleep(1)
                        
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed: {str(e)}")
                if "429" in str(e):  # Too Many Requests
                    time.sleep(5)  # Wait longer if rate limited
                continue
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                continue
                
        return {
            "message": f"No clinical trials found for {drug_name}.",
            "suggestion": "Try a different drug name or check the spelling."
        }

    def _get_search_strategies(self, drug_name: str, condition: str) -> List[Dict[str, str]]:
        """Generate multiple search strategies for better results."""
        strategies = []
        
        # Clean and prepare search terms
        drug_terms = [drug_name.strip()]
        
        # Add common variations
        if ' ' in drug_name:
            drug_terms.append(drug_name.split()[0])  # First word only
        
        # Generate search strategies for each term
        for term in set(drug_terms):
            # Basic search
            strategies.append({
                'query.term': term,
                'filter.overallStatus': ['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'COMPLETED'],
                'pageSize': 20,
                'sortField': 'NCTId',
                'sortOrder': 'DESC'
            })
            
            # Search in title
            strategies.append({
                'query.term': f'"{term}"',
                'query.locn': 'TITLE',
                'filter.overallStatus': ['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'COMPLETED'],
                'pageSize': 20,
                'sortField': 'NCTId',
                'sortOrder': 'DESC'
            })
            
            # Search in interventions
            strategies.append({
                'query.term': f'"{term}"',
                'query.locn': 'INTERVENTION',
                'filter.overallStatus': ['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'COMPLETED'],
                'pageSize': 20,
                'sortField': 'NCTId',
                'sortOrder': 'DESC'
            })
            
            # If condition is provided, add it to the search
            if condition.strip():
                strategies.append({
                    'query.term': f'"{term}" AND "{condition}"',
                    'filter.overallStatus': ['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'COMPLETED'],
                    'pageSize': 20,
                    'sortField': 'NCTId',
                    'sortOrder': 'DESC'
                })
        
        return strategies

    def _make_api_request(self, params: Dict) -> Optional[Dict]:
        """Make API request with retry logic and better error handling."""
        endpoint = f"{self.base_url}/studies"
        
        for attempt in range(self.max_retries):
            try:
                # Update headers for each attempt
                self._update_headers()
                
                # Add a small delay between retries
                if attempt > 0:
                    time.sleep(1 + attempt)  # Exponential backoff
                
                logger.info(f"Making request to {endpoint} with params: {params}")
                
                response = self.session.get(
                    endpoint,
                    params=params,
                    timeout=self.timeout
                )
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                    
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Resource not found: {e}")
                    return None
                elif e.response.status_code >= 500:
                    logger.error(f"Server error: {e}")
                    if attempt == self.max_retries - 1:
                        return None
                    continue
                else:
                    logger.error(f"HTTP error: {e}")
                    return None
                    
            except (requests.exceptions.RequestException, Exception) as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(1)  # Wait before retry

    def _process_trials(self, items: List[Dict]) -> Dict[str, Any]:
        """Process and format trial data from ClinicalTrials.gov API."""
        if not items:
            return {"trials": [], "total": 0, "phase_ii": 0, "phase_iii": 0}
            
        trials = []
        phase_ii = phase_iii = 0
        
        for item in items:
            try:
                # Extract basic info
                protocol_section = item.get('protocolSection', {})
                identification_module = protocol_section.get('identificationModule', {})
                status_module = protocol_section.get('statusModule', {})
                design_module = protocol_section.get('designModule', {})
                
                # Get phase information
                phases = design_module.get('phases', [])
                phase = self._get_trial_phase(phases[0] if phases else "")
                
                # Count phase II and III trials
                if "2" in phase:
                    phase_ii += 1
                elif "3" in phase:
                    phase_iii += 1
                
                # Get conditions
                conditions = ", ".join(protocol_section.get('conditionsModule', {}).get('conditions', [])) or "N/A"
                
                # Get interventions
                interventions = []
                for intervention in protocol_section.get('armsInterventionsModule', {}).get('interventions', []):
                    name = intervention.get('name', '')
                    intervention_type = intervention.get('type', '')
                    if name:
                        interventions.append(f"{name} ({intervention_type})" if intervention_type else name)
                
                trial = {
                    "Title": identification_module.get('briefTitle') or identification_module.get('officialTitle', 'N/A'),
                    "Status": status_module.get('overallStatus', 'Unknown').capitalize(),
                    "Phase": phase,
                    "Conditions": conditions,
                    "Interventions": ", ".join(interventions) or "N/A",
                    "Start Date": status_module.get('startDate', 'N/A'),
                    "Completion Date": status_module.get('completionDate', 'N/A'),
                    "NCT ID": identification_module.get('nctId', ''),
                    "URL": f"https://clinicaltrials.gov/ct2/show/{identification_module.get('nctId', '')}"
                }
                
                trials.append(trial)
                
            except Exception as e:
                logger.error(f"Error processing trial: {str(e)}\nTrial data: {item}", exc_info=True)
                continue

        return {
            "trials": trials,
            "total": len(trials),
            "phase_ii": phase_ii,
            "phase_iii": phase_iii
        }

    @staticmethod
    def _get_trial_phase(phase: str) -> str:
        """Format trial phase for display."""
        if not phase:
            return "N/A"
            
        phase = str(phase).upper()
        phase_map = {
            'PHASE1': 'Phase 1',
            'PHASE2': 'Phase 2',
            'PHASE3': 'Phase 3',
            'PHASE4': 'Phase 4',
            'EARLY_PHASE1': 'Early Phase 1',
            'PHASE1_PHASE2': 'Phase 1/Phase 2',
            'PHASE2_PHASE3': 'Phase 2/Phase 3',
            'NO_PHASE': 'N/A',
            '': 'N/A'
        }
        
        return phase_map.get(phase, phase.replace('_', ' ').title())

    @staticmethod
    def _format_date(date_str: Optional[str]) -> str:
        """Format date string to YYYY-MM-DD."""
        if not date_str:
            return "N/A"
            
        try:
            # Handle different date formats
            if 'T' in date_str:
                return date_str.split('T')[0]
            return str(date_str)[:10]
        except Exception:
            return str(date_str or 'N/A')
