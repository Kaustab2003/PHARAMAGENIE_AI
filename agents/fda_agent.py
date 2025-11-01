import os
import requests
import pandas as pd
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta

class FDAAgent:
    """Agent for interacting with the OpenFDA API to fetch drug-related data."""
    
    def __init__(self):
        self.base_url = "https://api.fda.gov/drug/event.json"
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _make_api_request(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Make an API request to the OpenFDA API with retry logic.
        
        Args:
            url: The URL to make the request to
            max_retries: Maximum number of retry attempts
            
        Returns:
            The JSON response as a dictionary, or None if the request fails after retries
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Making API request to: {url}")
                response = requests.get(
                    url,
                    timeout=10,
                    headers={
                        'User-Agent': 'PharmaGenieAI/1.0 (contact@pharmagenie.example.com)',
                        'Accept': 'application/json'
                    }
                )
                
                # Check for rate limiting (429 Too Many Requests)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    self.logger.warning(f"Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                    
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(f"API request attempt {attempt + 1} failed: {str(e)}")
                
                # Exponential backoff
                time.sleep(min(2 ** attempt, 10))  # Cap at 10 seconds
        
        # If we get here, all retries failed
        self.logger.error(f"API request failed after {max_retries} attempts: {str(last_exception)}")
        return None
    
    def get_drug_adverse_events(
        self, 
        drug_name: Optional[str] = None,
        limit: int = 10,
        time_frame: str = '1y'
    ) -> pd.DataFrame:
        """
        Fetch drug adverse events from OpenFDA.
        
        Args:
            drug_name: Optional drug name to filter by
            limit: Maximum number of results to return (1-100)
            time_frame: Time frame for the search (e.g., '1y' for 1 year, '6m' for 6 months)
            
        Returns:
            DataFrame containing drug adverse event data
        """
        try:
            # Build the base URL
            base_url = "https://api.fda.gov/drug/event.json"
            
            # Build the search query
            search_terms = []
            
            # Add time filter if specified
            if time_frame:
                end_date = datetime.now()
                if time_frame.endswith('y'):
                    years = int(time_frame[:-1])
                    start_date = end_date - timedelta(days=365 * years)
                elif time_frame.endswith('m'):
                    months = int(time_frame[:-1])
                    start_date = end_date - timedelta(days=30 * months)
                else:
                    start_date = end_date - timedelta(days=365)  # Default to 1 year
                
                search_terms.append(f'receivedate:[{start_date.strftime("%Y%m%d")}+TO+{end_date.strftime("%Y%m%d")}]')
            
            # Add drug name filter if provided
            if drug_name:
                search_terms.append(f'patient.drug.medicinalproduct:"{drug_name}"')
            
            # Build the complete search query
            search_query = '+AND+'.join(search_terms) if search_terms else ''
            
            # Build the URL with parameters
            url = f"{base_url}?search={search_query}&limit={min(max(1, limit), 100)}&count=patient.reaction.reactionmeddrapt.exact"
            
            # Make the request
            data = self._make_api_request(url)
            
            if not data or 'results' not in data:
                return pd.DataFrame()
            
            # Process and return the data
            records = []
            for result in data.get('results', []):
                # Get the primary suspect drug (usually the first one)
                drugs = result.get('patient', {}).get('drug', [{}])
                primary_drug = drugs[0] if drugs else {}
                
                # Get reactions
                reactions = result.get('patient', {}).get('reaction', [])
                reaction_terms = [r.get('reactionmeddrapt', '') for r in reactions if r.get('reactionmeddrapt')]
                
                # Get outcomes
                outcomes = result.get('patient', {}).get('reactionoutcome', [])
                
                record = {
                    'date_received': result.get('receivedate', 'Unknown'),
                    'drug_name': primary_drug.get('medicinalproduct', drug_name or 'Unknown'),
                    'reactions': ', '.join(reaction_terms) if reaction_terms else 'Not reported',
                    'serious': 1 if result.get('serious') == '1' else 0,
                    'outcomes': ', '.join(outcomes) if outcomes else 'Not reported',
                    'report_id': result.get('safetyreportid', 'Unknown')
                }
                records.append(record)
            
            return pd.DataFrame(records)
            
        except Exception as e:
            self.logger.error(f"Error fetching adverse events for {drug_name}: {str(e)}", exc_info=True)
            return pd.DataFrame()
    
    def get_drug_enforcement_reports(self, drug_name: str, limit: int = 10) -> pd.DataFrame:
        """
        Fetch drug enforcement reports from OpenFDA.
        
        Args:
            drug_name: Name of the drug to search for
            limit: Maximum number of results to return (1-100)
            
        Returns:
            DataFrame containing drug enforcement reports
        """
        try:
            # Build the URL with parameters
            url = f"https://api.fda.gov/drug/enforcement.json?search=product_description:\"{drug_name}\"&limit={min(max(1, limit), 100)}"
            
            # Make the request
            data = self._make_api_request(url)
            
            if not data or 'results' not in data:
                return pd.DataFrame()
            
            # Process and return the data
            records = []
            for result in data.get('results', []):
                record = {
                    'recall_number': result.get('recall_number', 'Not available'),
                    'reason_for_recall': result.get('reason_for_recall', 'Not specified'),
                    'status': result.get('status', 'Not specified'),
                    'distribution_pattern': result.get('distribution_pattern', 'Not specified'),
                    'product_description': result.get('product_description', 'Not specified'),
                    'recall_initiation_date': result.get('recall_initiation_date', 'Not specified'),
                    'classification': result.get('classification', 'Not specified'),
                    'recalling_firm': result.get('recalling_firm', 'Not specified'),
                    'report_date': result.get('report_date', 'Not specified')
                }
                records.append(record)
            
            return pd.DataFrame(records)
            
        except Exception as e:
            self.logger.error(f"Error fetching enforcement reports for {drug_name}: {str(e)}", exc_info=True)
            return pd.DataFrame()
    
    def get_drug_label(self, drug_name: str) -> Dict[str, str]:
        """
        Fetch drug label information from OpenFDA API.
        
        Args:
            drug_name: Name of the drug to search for
            
        Returns:
            Dictionary containing drug label information
        """
        try:
            # First try searching by brand name
            search_url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:\"{drug_name}\"&limit=1"
            data = self._make_api_request(search_url)
            
            # If no results, try searching by generic name
            if not data or 'results' not in data or not data['results']:
                search_url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:\"{drug_name}\"&limit=1"
                data = self._make_api_request(search_url)
            
            # If still no results, try a broader search
            if not data or 'results' not in data or not data['results']:
                search_url = f"https://api.fda.gov/drug/label.json?search=\"{drug_name}\"&limit=1"
                data = self._make_api_request(search_url)
            
            if not data or 'results' not in data or not data['results']:
                return {"error": f"No label information found for {drug_name}. The drug may not be in the FDA database or may be marketed under a different name."}
            
            result = data['results'][0]
            openfda = result.get('openfda', {})
            
            return {
                'drug_name': drug_name,
                'generic_name': ', '.join(openfda.get('generic_name', ['N/A'])),
                'brand_name': ', '.join(openfda.get('brand_name', [drug_name])),
                'manufacturer': ', '.join(openfda.get('manufacturer_name', ['N/A'])),
                'purpose': result.get('purpose', ['N/A'])[0] if isinstance(result.get('purpose'), list) else 'N/A',
                'warnings': result.get('warnings', ['N/A'])[0] if isinstance(result.get('warnings'), list) else 'N/A',
                'indications_and_usage': result.get('indications_and_usage', ['N/A'])[0] if isinstance(result.get('indications_and_usage'), list) else 'N/A',
                'dosage_and_administration': result.get('dosage_and_administration', ['N/A'])[0] if isinstance(result.get('dosage_and_administration'), list) else 'N/A'
            }
        except Exception as e:
            self.logger.error(f"Error fetching drug label for {drug_name}: {str(e)}", exc_info=True)
            return {"error": f"Error retrieving label information: {str(e)}"}
        
    def get_drug_info(self, drug_name: str) -> Dict:
        """
        Get comprehensive drug information including adverse events, enforcement reports, and label info.
        
        Args:
            drug_name: Name of the drug to search for
            
        Returns:
            Dictionary containing comprehensive drug information
        """
        try:
            # Get label information first to verify the drug exists
            label_info = self.get_drug_label(drug_name)
            
            # If we can't find the drug, return early with an error
            if 'error' in label_info:
                return {
                    'status': 'error',
                    'message': label_info['error'],
                    'drug_name': drug_name,
                    'adverse_events': [],
                    'enforcement_reports': [],
                    'label_info': {},
                    'warnings': []
                }
            
            # Get adverse events
            adverse_events = self.get_drug_adverse_events(drug_name, limit=50)
            
            # Get enforcement reports
            enforcement_reports = self.get_drug_enforcement_reports(drug_name, limit=10)
            
            # Prepare the response
            return {
                'status': 'success',
                'drug_name': drug_name,
                'adverse_events': adverse_events.to_dict('records') if not adverse_events.empty else [],
                'enforcement_reports': enforcement_reports.to_dict('records') if not enforcement_reports.empty else [],
                'label_info': label_info,
                'warnings': [label_info['warnings']] if 'warnings' in label_info and label_info['warnings'] != 'N/A' else [],
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting drug info for {drug_name}: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to retrieve information for {drug_name}: {str(e)}',
                'drug_name': drug_name,
                'adverse_events': [],
                'enforcement_reports': [],
                'label_info': {},
                'warnings': []
            }
