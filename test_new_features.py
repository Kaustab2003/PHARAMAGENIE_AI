"""
Comprehensive test suite for all patent-worthy features
Tests each feature for basic functionality and integration
"""
import asyncio
import sys
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test results tracker
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_test(test_name: str, status: str, message: str = ""):
    """Log test results"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"STATUS: {status}")
    if message:
        print(f"MESSAGE: {message}")
    print(f"{'='*60}")
    
    if status == "PASSED":
        test_results["passed"].append(test_name)
    elif status == "FAILED":
        test_results["failed"].append((test_name, message))
    else:
        test_results["warnings"].append((test_name, message))

async def test_drug_repurposing_agent():
    """Test Drug Repurposing Agent"""
    try:
        from agents.repurposing_agent import DrugRepurposingAgent
        
        agent = DrugRepurposingAgent()
        assert hasattr(agent, 'analyze_repurposing_opportunities'), "Missing analyze_repurposing_opportunities method"
        
        # Test with sample data
        candidates = await agent.analyze_repurposing_opportunities("Metformin", "cancer")
        
        assert isinstance(candidates, list), "Should return a list"
        if len(candidates) > 0:
            assert hasattr(candidates[0], 'drug_name'), "Candidate missing drug_name attribute"
            assert hasattr(candidates[0], 'confidence_score'), "Candidate missing confidence_score"
        
        log_test("Drug Repurposing Agent", "PASSED", f"Found {len(candidates)} repurposing candidates")
        return True
        
    except Exception as e:
        log_test("Drug Repurposing Agent", "FAILED", str(e))
        return False

async def test_adverse_event_predictor():
    """Test Adverse Event Predictor"""
    try:
        from agents.adverse_event_predictor import AdverseEventPredictor, PatientRiskProfile
        
        predictor = AdverseEventPredictor()
        assert hasattr(predictor, 'predict_adverse_events'), "Missing predict_adverse_events method"
        
        # Test with sample patient profile
        profile = PatientRiskProfile(
            age_group="Adult",
            comorbidities=["Hypertension"],
            concurrent_medications=["Lisinopril"]
        )
        
        predictions = await predictor.predict_adverse_events("Aspirin", profile, 30)
        
        assert isinstance(predictions, list), "Should return a list"
        if len(predictions) > 0:
            assert hasattr(predictions[0], 'event_type'), "Prediction missing event_type"
            assert hasattr(predictions[0], 'probability'), "Prediction missing probability"
        
        log_test("Adverse Event Predictor", "PASSED", f"Predicted {len(predictions)} potential adverse events")
        return True
        
    except Exception as e:
        log_test("Adverse Event Predictor", "FAILED", str(e))
        return False

async def test_approval_predictor():
    """Test FDA Approval Predictor"""
    try:
        from agents.approval_predictor import ApprovalPredictor
        
        predictor = ApprovalPredictor()
        assert hasattr(predictor, 'predict_approval'), "Missing predict_approval method"
        
        # Test with sample data
        clinical_data = {
            "phase3_met_endpoints": True,
            "novel_mechanism": False,
            "serious_adverse_events": 2,
            "effect_size": 0.7
        }
        
        regulatory_status = {
            "designations": ["Fast Track"]
        }
        
        prediction = await predictor.predict_approval(
            "Test Drug",
            "Type 2 Diabetes",
            clinical_data,
            regulatory_status
        )
        
        assert hasattr(prediction, 'approval_probability'), "Prediction missing approval_probability"
        assert hasattr(prediction, 'timeline_months'), "Prediction missing timeline_months"
        assert 0 <= prediction.approval_probability <= 1, "Probability should be between 0 and 1"
        
        log_test("FDA Approval Predictor", "PASSED", f"Probability: {prediction.approval_probability:.1%}")
        return True
        
    except Exception as e:
        log_test("FDA Approval Predictor", "FAILED", str(e))
        return False

async def test_paper_analyzer():
    """Test Paper Analyzer"""
    try:
        from agents.paper_analyzer import PaperAnalyzer
        
        analyzer = PaperAnalyzer()
        assert hasattr(analyzer, 'analyze_paper'), "Missing analyze_paper method"
        
        # Test with sample paper data
        paper_data = {
            "title": "Novel Treatment for Disease X",
            "abstract": "This study investigates a new therapeutic approach...",
            "authors": ["Smith J", "Jones A"],
            "journal": "Nature Medicine",
            "year": 2024
        }
        
        summary = await analyzer.analyze_paper(paper_data)
        
        assert hasattr(summary, 'summary'), "Summary missing summary attribute"
        assert hasattr(summary, 'key_findings'), "Summary missing key_findings"
        assert hasattr(summary, 'quality_score'), "Summary missing quality_score"
        
        log_test("Paper Analyzer", "PASSED", f"Quality score: {summary.quality_score:.2f}")
        return True
        
    except Exception as e:
        log_test("Paper Analyzer", "FAILED", str(e))
        return False

async def test_voice_assistant():
    """Test Voice Assistant"""
    try:
        from features.voice_assistant import VoiceAssistant
        
        assistant = VoiceAssistant()
        assert hasattr(assistant, 'process_voice_command'), "Missing process_voice_command method"
        
        # Test with sample command
        command = await assistant.process_voice_command(
            "Tell me about metformin side effects"
        )
        
        assert hasattr(command, 'intent'), "Command missing intent"
        assert hasattr(command, 'entities'), "Command missing entities"
        assert hasattr(command, 'response'), "Command missing response"
        
        log_test("Voice Assistant", "PASSED", f"Intent: {command.intent}")
        return True
        
    except Exception as e:
        log_test("Voice Assistant", "FAILED", str(e))
        return False

async def test_interaction_network():
    """Test Interaction Network Visualizer"""
    try:
        from pages.interaction_network import InteractionNetworkVisualizer
        
        visualizer = InteractionNetworkVisualizer()
        assert hasattr(visualizer, 'create_interaction_network'), "Missing create_interaction_network method"
        assert hasattr(visualizer, 'simulate_pharmacokinetics'), "Missing simulate_pharmacokinetics method"
        
        # Test network creation
        fig, interactions = visualizer.create_interaction_network(["Warfarin", "Aspirin"])
        
        assert fig is not None, "Figure should not be None"
        assert isinstance(interactions, list), "Interactions should be a list"
        
        # Test PK simulation
        time, concentration = visualizer.simulate_pharmacokinetics("Warfarin", dose=5.0)
        
        assert len(time) > 0, "Should return time points"
        assert len(concentration) > 0, "Should return concentration values"
        
        log_test("Interaction Network Visualizer", "PASSED", f"Created network with {len(interactions)} interactions")
        return True
        
    except Exception as e:
        log_test("Interaction Network Visualizer", "FAILED", str(e))
        return False

def test_advanced_features_page():
    """Test Advanced Features Page"""
    try:
        from pages.advanced_features import render_advanced_features_page
        
        assert callable(render_advanced_features_page), "render_advanced_features_page should be callable"
        
        log_test("Advanced Features Page", "PASSED", "Page function exists and is callable")
        return True
        
    except Exception as e:
        log_test("Advanced Features Page", "FAILED", str(e))
        return False

def test_main_app_integration():
    """Test Main App Integration"""
    try:
        # Check if app.py can be imported
        import app
        
        log_test("Main App Integration", "PASSED", "app.py imports successfully")
        return True
        
    except Exception as e:
        log_test("Main App Integration", "FAILED", str(e))
        return False

def test_dependencies():
    """Test Required Dependencies"""
    required_packages = [
        "streamlit",
        "openai",
        "pandas",
        "numpy",
        "plotly",
        "networkx",
        "scipy",
        "sklearn",
        "aiohttp"
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == "sklearn":
                __import__("sklearn")
            else:
                __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        log_test("Dependencies Check", "WARNING", f"Missing packages: {', '.join(missing)}")
        return False
    else:
        log_test("Dependencies Check", "PASSED", "All required packages installed")
        return True

async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHARAMAGENIE AI - PATENT FEATURES TEST SUITE")
    print("="*60)
    
    # Test dependencies first
    test_dependencies()
    
    # Run async tests
    await test_drug_repurposing_agent()
    await test_adverse_event_predictor()
    await test_approval_predictor()
    await test_paper_analyzer()
    await test_voice_assistant()
    await test_interaction_network()
    
    # Run sync tests
    test_advanced_features_page()
    test_main_app_integration()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ PASSED: {len(test_results['passed'])}")
    for test in test_results['passed']:
        print(f"   - {test}")
    
    if test_results['warnings']:
        print(f"\n⚠️  WARNINGS: {len(test_results['warnings'])}")
        for test, msg in test_results['warnings']:
            print(f"   - {test}: {msg}")
    
    if test_results['failed']:
        print(f"\n❌ FAILED: {len(test_results['failed'])}")
        for test, msg in test_results['failed']:
            print(f"   - {test}: {msg}")
    else:
        print("\n🎉 ALL TESTS PASSED!")
    
    print("="*60)
    
    return len(test_results['failed']) == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
