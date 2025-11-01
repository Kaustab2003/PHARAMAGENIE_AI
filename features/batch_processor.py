# features/batch_processor.py
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import asyncio
from tqdm import tqdm
import io

class BatchProcessor:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        
    async def process_csv(self, file: bytes, callback=None) -> pd.DataFrame:
        """Process a CSV file with drug data"""
        # Read CSV
        try:
            df = pd.read_csv(io.BytesIO(file))
            required_columns = ['drug_name']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"CSV must contain columns: {required_columns}")
                
            # Process in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(
                        executor, 
                        self._process_single_drug, 
                        row.to_dict()
                    )
                    for _, row in df.iterrows()
                ]
                
                results = []
                for future in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
                    result = await future
                    if callback:
                        await callback(result)
                    results.append(result)
                    
            return pd.DataFrame(results)
            
        except Exception as e:
            raise Exception(f"Error processing batch: {str(e)}")
    
    def _process_single_drug(self, drug_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single drug (simplified example)"""
        # In a real app, this would call your analysis functions
        return {
            'drug_name': drug_data.get('drug_name', 'Unknown'),
            'score': np.random.randint(0, 100),
            'status': 'completed',
            'details': {'message': 'Analysis complete'}
        }
    
    def generate_comparison_matrix(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Generate a comparison matrix from analysis results"""
        if not results:
            return pd.DataFrame()
            
        df = pd.DataFrame(results)
        # Add more sophisticated comparison logic here
        return df
    
    def export_to_excel(self, results: List[Dict[str, Any]]) -> bytes:
        """Export results to Excel format"""
        df = self.generate_comparison_matrix(results)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Analysis Results')
            
            # Add charts if needed
            if not df.empty:
                workbook = writer.book
                worksheet = writer.sheets['Analysis Results']
                
                # Example: Add a bar chart
                chart = workbook.add_chart({'type': 'column'})
                chart.add_series({
                    'values': '=Analysis Results!$B$2:$B$'+str(len(df)+1),
                    'categories': '=Analysis Results!$A$2:$A$'+str(len(df)+1),
                    'name': 'Scores'
                })
                chart.set_title({'name': 'Drug Comparison'})
                worksheet.insert_chart('D2', chart)
        
        return output.getvalue()
        