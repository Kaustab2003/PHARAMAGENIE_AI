"""
Quick script to update all API calls to use unified client
Run this to complete the API migration
"""

import re
import os
from pathlib import Path

def update_file(filepath):
    """Update a single file to use unified API client."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Replace OpenAI client initialization patterns
    content = re.sub(
        r'from openai import OpenAI\s+client = OpenAI\(api_key=self\.api_key\)',
        'client = self.api_client.get_client()',
        content
    )
    
    # Replace model="gpt-4" with dynamic model
    content = re.sub(
        r'model="gpt-4"',
        'model=self.api_client.get_model()',
        content
    )
    
    # Replace self.api_key checks
    content = re.sub(
        r'if not self\.api_key:',
        'if not self.api_client:',
        content
    )
    
    content = re.sub(
        r'if self\.api_key:',
        'if self.api_client:',
        content
    )
    
    # Add safety for .strip() calls
    content = re.sub(
        r'response\.choices\[0\]\.message\.content\.strip\(\)',
        '(response.choices[0].message.content or "").strip()',
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated: {filepath}")
        return True
    else:
        print(f"⏭️  Skipped (no changes): {filepath}")
        return False

def main():
    """Update all agent and feature files."""
    files_to_update = [
        "agents/repurposing_agent.py",
        "agents/adverse_event_predictor.py",
        "agents/approval_predictor.py",
        "agents/paper_analyzer.py",
        "features/voice_assistant.py"
    ]
    
    base_path = Path(__file__).parent
    updated_count = 0
    
    print("="*60)
    print("API CLIENT MIGRATION SCRIPT")
    print("="*60)
    
    for file_path in files_to_update:
        full_path = base_path / file_path
        if full_path.exists():
            if update_file(full_path):
                updated_count += 1
        else:
            print(f"❌ File not found: {file_path}")
    
    print("="*60)
    print(f"Migration complete! Updated {updated_count} files.")
    print("="*60)

if __name__ == "__main__":
    main()
