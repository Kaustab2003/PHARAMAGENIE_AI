# agents/clinical_trials_agent.py
import requests
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime, timedelta
import json
import random
import time
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class ClinicalTrialsAgent:
    # ClinicalTrials.gov API v2
    CLINICALTRIALS_API_V2 = "https://clinicaltrials.gov/api/v2/studies"
    
    # Fallback to website if API fails
    CLINICALTRIALS_WEB = "https://clinicaltrials.gov/ct2/results"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds between requests to avoid rate limiting

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _get_with_retry(self, url: str, params: Optional[dict] = None, max_retries: int = 3) -> Optional[dict]:
        """Make a GET request with retry logic and rate limiting."""
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed for URL: {url}")
                    return None
                # Exponential backoff with jitter
                time.sleep((2 ** attempt) + random.uniform(0, 1))

    def _format_date(self, date_str: Optional[str]) -> str:
        """Format date string to a more readable format."""
        if not date_str:
            return 'N/A'
        try:
            # Handle different date formats
            if 'T' in date_str:
                date_str = date_str.split('T')[0]
            
            # Try to parse the date
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y%m%d'):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%b %d, %Y')
                except ValueError:
                    continue
            return date_str or 'N/A'
        except Exception as e:
            logger.warning(f"Error formatting date '{date_str}': {str(e)}")
            return date_str or 'N/A'
            
    def _process_trial(self, trial_data: dict) -> Optional[dict]:
        """Process a single trial from ClinicalTrials.gov API response."""
        try:
            protocol_section = trial_data.get('protocolSection', {})
            identification_module = protocol_section.get('identificationModule', {})
            status_module = protocol_section.get('statusModule', {})
            design_module = protocol_section.get('designModule', {})
            
            # Get interventions
            interventions = []
            if 'interventions' in protocol_section:
                for intervention in protocol_section['interventions']:
                    name = intervention.get('name', '')
                    if name and name.lower() != 'not provided':
                        interventions.append(name)
            
            # Get conditions
            conditions = protocol_section.get('conditionsModule', {}).get('conditions', [])
            
            # Get locations
            locations = []
            if 'sites' in trial_data.get('hasResultsModule', {}):
                for site in trial_data['hasResultsModule']['sites']:
                    if 'name' in site:
                        locations.append(site['name'])
            
            # Get sponsors
            sponsors = []
            if 'sponsor' in protocol_section:
                sponsor = protocol_section['sponsor']
                if 'name' in sponsor and sponsor['name'].lower() != 'not provided':
                    sponsors.append(sponsor['name'])
            
            # Get phase
            phase = design_module.get('phases', ['N/A'])[0] if design_module.get('phases') else 'N/A'
            
            return {
                'title': identification_module.get('briefTitle') or identification_module.get('officialTitle', 'No title available'),
                'nct_id': identification_module.get('nctId', ''),
                'status': status_module.get('overallStatus', 'Status not available'),
                'phase': phase,
                'start_date': self._format_date(status_module.get('startDate')),
                'completion_date': self._format_date(status_module.get('completionDate')),
                'enrollment': status_module.get('enrollmentCount', 'N/A'),
                'url': f"https://clinicaltrials.gov/ct2/show/{identification_module.get('nctId', '')}",
                'interventions': ', '.join(interventions) or 'Not specified',
                'conditions': ', '.join(conditions) or 'Not specified',
                'sponsors': ', '.join(sponsors) or 'Not specified',
                'locations': ', '.join(locations[:3]) + ('...' if len(locations) > 3 else '') if locations else 'Not specified',
                'source': 'clinicaltrials.gov',
                'study_type': design_module.get('studyType', 'N/A'),
                'description': protocol_section.get('descriptionModule', {}).get('briefSummary', 'No description available')
            }
        except Exception as e:
            logger.error(f"Error processing trial data: {str(e)}\n{json.dumps(trial_data, indent=2)}")
            return None
            
    def _parse_clinicaltrials_card(self, card) -> Optional[dict]:
        """Parse a single trial card from ClinicalTrials.gov search results."""
        try:
            title_elem = card.find('a', {'class': 'link-underline'}) or card.find('a', href=lambda x: x and '/ct2/show/' in x)
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            nct_id = ''
            if 'href' in title_elem.attrs:
                nct_id = title_elem['href'].split('/')[-1].split('?')[0]
            
            # Extract status
            status_elem = card.find('span', {'class': 'study-status'}) or card.find('div', string=lambda x: x and 'status:' in x.lower())
            status = status_elem.get_text(strip=True).replace('Status:', '').strip() if status_elem else 'Status not available'
            
            # Extract condition
            condition_elem = (card.find('div', {'class': 'truncate'}) or 
                            card.find('div', string=lambda x: x and 'condition' in x.lower()) or
                            card.find('div', {'class': 'condition'}))
            condition = condition_elem.get_text(strip=True) if condition_elem else 'Not specified'
            
            # Extract phase
            phase = 'N/A'
            for label in card.find_all(['span', 'div'], {'class': lambda x: x and 'phase' in x.lower()}):
                phase_text = label.get_text(strip=True)
                if 'phase' in phase_text.lower():
                    phase = phase_text
                    break
            
            return {
                'title': title,
                'nct_id': nct_id,
                'status': status,
                'condition': condition,
                'phase': phase,
                'url': f"{self.CLINICALTRIALS_URL}/ct2/show/{nct_id}" if nct_id else '',
                'interventions': 'Not specified',
                'conditions': condition,
                'sponsors': 'Not specified',
                'location': 'Not specified',
                'source': 'clinicaltrials.gov',
                'registration_date': ''
            }
        except Exception as e:
            logger.error(f"Error parsing trial card: {str(e)}")
            return None

    def _search_clinicaltrials(self, drug_name: str, condition: str = "") -> Optional[Dict[str, Any]]:
        """Search for clinical trials using ClinicalTrials.gov API v2."""
        # Broader search expression
        search_expr = f'AREA[Intervention] "{drug_name}"'
        if condition:
            search_expr += f' AND AREA[Condition] "{condition}"'

        params = {
            'expr': search_expr,
            'fmt': 'json',
            'pageSize': '20',
            'sort': 'LastUpdatePostDate:desc'
        }
        
        try:
            logger.info(f"Searching ClinicalTrials.gov with params: {params}")
            data = self._get_with_retry(self.CLINICALTRIALS_API_V2, params=params)
            
            if data and data.get('studies'):
                processed = self._process_api_response(data)
                if processed and processed.get('trials'):
                    return processed
            
            logger.warning("No studies found with the initial search.")
            return None

        except Exception as e:
            logger.error(f"Error in ClinicalTrials.gov search: {str(e)}", exc_info=True)
            return None
    
    def _process_api_response(self, data: dict) -> Dict[str, Any]:
        """Process response from ClinicalTrials.gov API v2."""
        phase_ii = phase_iii = 0
        recent_trials = []
        insights = []
        
        for study in data.get('studies', [])[:10]:  # Limit to 10 most recent
            trial = self._process_trial(study)
            if not trial:
                continue
            
            # Count phases
            phase_lower = str(trial.get('phase', '')).lower()
            if any(phase in phase_lower for phase in ['phase 2', 'phase ii', 'phase2', 'phaseii']):
                phase_ii += 1
            if any(phase in phase_lower for phase in ['phase 3', 'phase iii', 'phase3', 'phaseiii']):
                phase_iii += 1
            
            recent_trials.append(trial)
            
            # Build insight
            insight_parts = []
            if trial.get('phase', 'N/A') != 'N/A':
                insight_parts.append(trial['phase'])
            if trial.get('status', 'N/A') != 'N/A':
                insight_parts.append(trial['status'])
            
            insight = trial['title']
            if insight_parts:
                insight += f" ({', '.join(insight_parts)})"
            insights.append(insight)
        
        return {
            'phase_ii': phase_ii,
            'phase_iii': phase_iii,
            'trials': recent_trials,
            'insights': insights[:5],  # Limit to 5 insights
            'source': 'clinicaltrials.gov',
            'total_count': data.get('totalCount', 0)
        }
    
    def get_clinical_trials(self, drug_name: str, condition: str = "") -> Dict[str, Any]:
        """
        Get clinical trials information from ClinicalTrials.gov.
        
        Args:
            drug_name: Name of the drug to search for
            condition: Optional condition/disease to filter by
            
        Returns:
            Dict containing clinical trials information or error message
        """
        try:
            logger.info(f"Searching for clinical trials for drug: {drug_name}, condition: {condition}")
            
            # Search ClinicalTrials.gov
            result = self._search_clinicaltrials(drug_name, condition)
            
            if not result or not result.get('trials'):
                # Try a more general search without condition
                if condition:
                    logger.info("No results with condition, trying broader search...")
                    result = self._search_clinicaltrials(drug_name, "")
                
                if not result or not result.get('trials'):
                    return {
                        "message": "No clinical trials found for the specified criteria.",
                        "suggestion": (
                            "Try checking the drug name spelling or try a different name. "
                            "You can also try a more general search term or check the ClinicalTrials.gov website directly."
                        ),
                        "status": "No trials found",
                        "phase_ii_trials": 0,
                        "phase_iii_trials": 0,
                        "recent_trials": [],
                        "key_insights": ["No clinical trial data available for this search."],
                        "source": "clinicaltrials.gov",
                        "search_url": f"https://clinicaltrials.gov/ct2/results?term={quote_plus(drug_name)}"
                    }
            
            return {
                "phase_ii_trials": result['phase_ii'],
                "phase_iii_trials": result['phase_iii'],
                "recent_trials": result['trials'],
                "key_insights": result['insights'],
                "total_studies": result.get('total_count', len(result.get('trials', []))),
                "status": f"Found {result.get('total_count', len(result.get('trials', [])))} studies",
                "source": "clinicaltrials.gov",
                "search_url": f"https://clinicaltrials.gov/ct2/results?term={quote_plus(drug_name)}"
            }
        except Exception as e:
            error_msg = f"An error occurred while fetching clinical trials: {str(e)}"
            logger.error(error_msg, exc_info=True)
            search_url = f"https://clinicaltrials.gov/ct2/results?term={quote_plus(drug_name)}"
            return {
                "error": error_msg,
                "status": "Error processing request",
                "suggestion": f"Please try again later or <a href='{search_url}' target='_blank'>search on ClinicalTrials.gov</a> directly.",
                "phase_ii_trials": 0,
                "phase_iii_trials": 0,
                "recent_trials": [],
                "key_insights": ["Error loading clinical trial data."],
                "source": "clinicaltrials.gov",
                "search_url": search_url
            }