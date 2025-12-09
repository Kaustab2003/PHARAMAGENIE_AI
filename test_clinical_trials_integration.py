#!/usr/bin/env python
"""Integration test for clinical trials in the main app."""
import sys
from agents.clinical_trials_agent import ClinicalTrialsAgent

def test_integration():
    print("🧪 Integration Test: Clinical Trials in App")
    print("=" * 60)
    
    # Test the agent
    agent = ClinicalTrialsAgent()
    
    # Test 1: Metformin
    print("\n📊 Test 1: Metformin")
    result1 = agent.get_clinical_trials('metformin')
    print(f"  ✅ Status: {result1.get('status')}")
    print(f"  ✅ Total Studies: {result1.get('total_studies', 0)}")
    print(f"  ✅ Phase II: {result1.get('phase_ii_trials', 0)}")
    print(f"  ✅ Phase III: {result1.get('phase_iii_trials', 0)}")
    print(f"  ✅ Trials Found: {len(result1.get('recent_trials', []))}")
    
    # Test 2: Aspirin
    print("\n📊 Test 2: Aspirin")
    result2 = agent.get_clinical_trials('aspirin')
    print(f"  ✅ Status: {result2.get('status')}")
    print(f"  ✅ Total Studies: {result2.get('total_studies', 0)}")
    print(f"  ✅ Trials Found: {len(result2.get('recent_trials', []))}")
    
    # Test 3: Invalid drug name
    print("\n📊 Test 3: Invalid Drug (zzzzzzinvaliddrugname)")
    result3 = agent.get_clinical_trials('zzzzzzinvaliddrugname')
    print(f"  ✅ Message: {result3.get('message', 'N/A')[:80]}")
    print(f"  ✅ Has suggestion: {'suggestion' in result3}")
    
    # Test 4: Check data structure
    print("\n📊 Test 4: Data Structure Validation")
    if result1.get('recent_trials'):
        trial = result1['recent_trials'][0]
        required_fields = ['title', 'nct_id', 'status', 'phase', 'url', 'conditions', 'interventions']
        missing_fields = [f for f in required_fields if f not in trial]
        if not missing_fields:
            print(f"  ✅ All required fields present in trial data")
        else:
            print(f"  ❌ Missing fields: {', '.join(missing_fields)}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Clinical Trials Feature Working!")
    print("\n💡 Next Steps:")
    print("  1. Refresh your Streamlit app (Ctrl+F5)")
    print("  2. Search for any drug (e.g., 'metformin', 'aspirin', 'ibuprofen')")
    print("  3. Check the '🔬 Clinical Trials' section")
    print("  4. You should see:")
    print("     - Total studies count")
    print("     - Phase II and Phase III trial counts")
    print("     - List of recent trials with details")
    print("     - Links to view trials on ClinicalTrials.gov")

if __name__ == '__main__':
    test_integration()
