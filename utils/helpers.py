import os
from dotenv import load_dotenv
from pathlib import Path
import json
from typing import Dict, Any

# Load environment variables
load_dotenv()

def initialize_agents() -> bool:
    """Initialize all agents and verify required environment variables."""
    required_vars = [
        'OPENAI_API_KEY',
        'CLINICAL_TRIALS_API_KEY',
        'PATENT_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Please set them in the .env file."
        )
    
    # Create necessary directories
    Path("data/reports").mkdir(parents=True, exist_ok=True)
    Path("data/cache").mkdir(parents=True, exist_ok=True)
    
    return True

def save_report(report_data: Dict[str, Any], filename: str = None) -> str:
    """Save analysis report to a JSON file."""
    if not filename:
        drug_name = report_data.get('drug_name', 'report').lower().replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{drug_name}_{timestamp}.json"
    
    filepath = Path("data/reports") / filename
    
    with open(filepath, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    return str(filepath)

def load_report(filename: str) -> Dict[str, Any]:
    """Load a previously saved report."""
    filepath = Path("data/reports") / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Report not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def get_cached_data(key: str) -> Any:
    """Get cached data if available."""
    cache_file = Path(f"data/cache/{key}.json")
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)
    return None

def cache_data(key: str, data: Any) -> None:
    """Cache data for future use."""
    cache_file = Path(f"data/cache/{key}.json")
    with open(cache_file, 'w') as f:
        json.dump(data, f)
