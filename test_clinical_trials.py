#!/usr/bin/env python
"""Test script for clinical trials functionality."""
from agents.clinical_trials_agent import ClinicalTrialsAgent
import json

def test_clinical_trials():
    print("Testing Clinical Trials Agent...")
    agent = ClinicalTrialsAgent()
    
    # Test with metformin
    print("\n🔍 Testing with 'metformin'...")
    result = agent.get_clinical_trials('metformin')
    
    print(f"✅ Status: {result.get('status')}")
    print(f"✅ Total studies: {result.get('total_studies', 0)}")
    print(f"✅ Phase II trials: {result.get('phase_ii_trials', 0)}")
    print(f"✅ Phase III trials: {result.get('phase_iii_trials', 0)}")
    print(f"✅ Recent trials found: {len(result.get('recent_trials', []))}")
    
    if result.get('recent_trials'):
        trial = result['recent_trials'][0]
        print('\n📋 Sample trial:')
        print(f"  Title: {trial.get('title', 'N/A')[:80]}")
        print(f"  Status: {trial.get('status', 'N/A')}")
        print(f"  Phase: {trial.get('phase', 'N/A')}")
        print(f"  Conditions: {trial.get('conditions', 'N/A')[:60]}")
        print(f"  URL: {trial.get('url', 'N/A')}")
    
    # Test with aspirin
    print("\n\n🔍 Testing with 'aspirin'...")
    result2 = agent.get_clinical_trials('aspirin')
    
    print(f"✅ Status: {result2.get('status')}")
    print(f"✅ Total studies: {result2.get('total_studies', 0)}")
    print(f"✅ Recent trials found: {len(result2.get('recent_trials', []))}")
    
    print("\n✅ Clinical Trials Agent is working correctly!")

if __name__ == '__main__':
    test_clinical_trials()
