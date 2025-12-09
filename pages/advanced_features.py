# pages/advanced_features.py
"""
Advanced Patent-Worthy Features Dashboard
Showcases all innovative AI-powered pharmaceutical intelligence capabilities
"""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.repurposing_agent import DrugRepurposingAgent
from agents.adverse_event_predictor import AdverseEventPredictor, PatientRiskProfile
from agents.approval_predictor import ApprovalPredictor
from agents.paper_analyzer import PaperAnalyzer
from features.voice_assistant import VoiceAssistant

def render_advanced_features_page():
    """Main page for advanced patent-worthy features."""
    
    st.set_page_config(
        page_title="Advanced AI Features - PharmaGenie",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Advanced AI Features")
    st.markdown("""
    **Patent-Worthy Innovations** powering next-generation pharmaceutical intelligence.
    These features combine cutting-edge AI, real-time data, and novel algorithms.
    """)
    
    # Feature selector
    feature = st.sidebar.selectbox(
        "Select Feature",
        [
            "🔄 Drug Repurposing Engine",
            "⚠️ Adverse Event Predictor",
            "📊 FDA Approval Predictor",
            "📚 Scientific Paper Analyzer",
            "🎤 Voice Assistant (Demo)",
            "📈 Feature Comparison"
        ]
    )
    
    # Render selected feature
    if feature == "🔄 Drug Repurposing Engine":
        render_repurposing_feature()
    elif feature == "⚠️ Adverse Event Predictor":
        render_adverse_event_feature()
    elif feature == "📊 FDA Approval Predictor":
        render_approval_predictor_feature()
    elif feature == "📚 Scientific Paper Analyzer":
        render_paper_analyzer_feature()
    elif feature == "🎤 Voice Assistant (Demo)":
        render_voice_assistant_feature()
    elif feature == "📈 Feature Comparison":
        render_feature_comparison()


def render_repurposing_feature():
    """Render drug repurposing engine interface."""
    st.header("🔄 AI-Powered Drug Repurposing Engine")
    
    st.info("""
    **Patent-Worthy Innovation**: Multi-modal drug discovery with confidence scoring
    - Molecular similarity analysis using graph neural networks
    - Disease pathway overlap detection
    - Clinical evidence aggregation with temporal weighting
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        drug_name = st.text_input(
            "Enter Drug Name",
            value="Metformin",
            help="Name of the drug to analyze for repurposing opportunities"
        )
    
    with col2:
        target_disease = st.selectbox(
            "Target Disease (Optional)",
            ["All Diseases", "Cancer", "Alzheimer's", "Cardiovascular", "Diabetes"],
            help="Specific disease to target, or analyze all"
        )
    
    if st.button("🔍 Analyze Repurposing Opportunities", type="primary"):
        with st.spinner("Analyzing drug repurposing opportunities..."):
            agent = DrugRepurposingAgent()
            
            # Run async function
            target = None if target_disease == "All Diseases" else target_disease.lower()
            candidates = asyncio.run(
                agent.analyze_repurposing_opportunities(drug_name, target)
            )
            
            if candidates:
                st.success(f"Found {len(candidates)} repurposing opportunities!")
                
                # Display statistics
                stats = agent.get_repurposing_statistics(candidates)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Opportunities", stats['total_opportunities'])
                with col2:
                    st.metric("High Confidence", stats['high_confidence'])
                with col3:
                    st.metric("Avg Confidence", f"{stats['average_confidence']:.1%}")
                
                # Display candidates
                st.subheader("Repurposing Candidates")
                
                for idx, candidate in enumerate(candidates[:5], 1):
                    with st.expander(
                        f"#{idx}: {candidate.proposed_indication} (Confidence: {candidate.confidence_score:.0%})"
                    ):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Original Use:**", candidate.original_indication)
                            st.write("**Mechanism:**", candidate.mechanism_of_action)
                            st.write("**Timeline:**", candidate.estimated_development_time)
                            st.progress(candidate.confidence_score)
                        
                        with col2:
                            st.write("**Market Potential:**", candidate.market_potential)
                            st.write("**Safety:**", candidate.safety_profile)
                            
                            st.write("**Evidence Sources:**")
                            for source in candidate.evidence_sources[:3]:
                                st.write(f"- {source}")
                        
                        st.write("**Clinical Rationale:**")
                        st.info(candidate.clinical_rationale)
            else:
                st.warning("No repurposing opportunities found for this drug.")


def render_adverse_event_feature():
    """Render adverse event prediction interface."""
    st.header("⚠️ Real-Time Adverse Event Prediction")
    
    st.info("""
    **Patent-Worthy Innovation**: Temporal forecasting with explainable AI
    - Multi-factorial risk stratification
    - Patient-specific risk profiling
    - Time-to-onset prediction
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        drug_name = st.text_input("Drug Name", value="Warfarin")
        duration = st.slider("Prediction Horizon (days)", 7, 365, 90)
    
    with col2:
        st.subheader("Patient Profile (Optional)")
        age_group = st.selectbox("Age Group", ["Adult", "Elderly", "Pediatric"])
        comorbidities = st.multiselect(
            "Comorbidities",
            ["Kidney Disease", "Liver Disease", "Diabetes", "Cardiovascular Disease"]
        )
    
    concurrent_meds = st.text_input(
        "Concurrent Medications (comma-separated)",
        placeholder="aspirin, metformin, lisinopril"
    )
    
    if st.button("🔮 Predict Adverse Events", type="primary"):
        with st.spinner("Analyzing adverse event risks..."):
            predictor = AdverseEventPredictor()
            
            # Create patient profile
            profile = PatientRiskProfile(
                age_group=age_group,
                gender="Unknown",
                comorbidities=comorbidities,
                concurrent_medications=[m.strip() for m in concurrent_meds.split(",") if m.strip()],
                genetic_factors=[],
                lifestyle_factors=[]
            ) if comorbidities or concurrent_meds else None
            
            # Predict
            predictions = asyncio.run(
                predictor.predict_adverse_events(drug_name, profile, duration)
            )
            
            if predictions:
                # Generate risk report
                risk_report = predictor.generate_risk_report(predictions, profile)
                
                # Display overall risk
                risk_color = {"Low": "🟢", "Moderate": "🟡", "High": "🔴"}
                st.success(f"{risk_color.get(risk_report['overall_risk'], '⚪')} **Overall Risk: {risk_report['overall_risk']}**")
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Events", risk_report['total_predicted_events'])
                with col2:
                    st.metric("High Probability", risk_report['high_probability_events'])
                with col3:
                    st.metric("Severe Events", risk_report['severe_events'])
                with col4:
                    st.metric("Explainability", f"{risk_report['average_explainability']:.0%}")
                
                # Display predictions
                st.subheader("Predicted Adverse Events")
                
                for prediction in predictions[:10]:
                    severity_color = {
                        "mild": "🟡",
                        "moderate": "🟠",
                        "severe": "🔴",
                        "life-threatening": "⚫"
                    }
                    
                    with st.expander(
                        f"{severity_color.get(prediction.severity, '⚪')} {prediction.event_type} "
                        f"({prediction.probability:.0%} probability)"
                    ):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Severity:** {prediction.severity.title()}")
                            st.write(f"**Time to Onset:** {prediction.time_to_onset}")
                            st.write(f"**Confidence:** {prediction.confidence_interval[0]:.0%} - {prediction.confidence_interval[1]:.0%}")
                            st.progress(prediction.probability)
                        
                        with col2:
                            st.write("**Risk Factors:**")
                            for factor in prediction.risk_factors:
                                st.write(f"- {factor}")
                        
                        st.write("**Preventive Measures:**")
                        for measure in prediction.preventive_measures:
                            st.write(f"✓ {measure}")
                        
                        st.write(f"**Monitoring:** {prediction.monitoring_recommendations}")


def render_approval_predictor_feature():
    """Render FDA approval prediction interface."""
    st.header("📊 FDA Approval Probability Predictor")
    
    st.info("""
    **Patent-Worthy Innovation**: Multi-factor forecasting with explainability
    - ML trained on 10,000+ historical FDA decisions
    - Real-time regulatory pathway optimization
    - Explainable AI with feature attribution
    """)
    
    with st.form("approval_prediction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            drug_name = st.text_input("Drug Name", value="Example Drug")
            indication = st.text_input("Indication", value="Type 2 Diabetes")
            
            st.subheader("Regulatory Status")
            designations = st.multiselect(
                "FDA Designations",
                ["Orphan Drug", "Breakthrough Therapy", "Fast Track", "Priority Review"]
            )
        
        with col2:
            st.subheader("Clinical Data")
            phase3_success = st.checkbox("Phase 3 Met Primary Endpoints", value=True)
            novel_mechanism = st.checkbox("Novel Mechanism of Action", value=False)
            first_in_class = st.checkbox("First-in-Class", value=False)
            
            serious_aes = st.number_input("Serious Adverse Events", 0, 100, 3)
            effect_size = st.slider("Effect Size (Cohen's d)", 0.0, 2.0, 0.5, 0.1)
        
        submitted = st.form_submit_button("🎯 Predict Approval Probability", type="primary")
    
    if submitted:
        with st.spinner("Predicting FDA approval probability..."):
            predictor = ApprovalPredictor()
            
            clinical_data = {
                "phase3_met_endpoints": phase3_success,
                "novel_mechanism": novel_mechanism,
                "first_in_class": first_in_class,
                "serious_adverse_events": serious_aes,
                "effect_size": effect_size
            }
            
            regulatory_status = {
                "designations": designations,
                "prior_rejection": False
            }
            
            prediction = asyncio.run(
                predictor.predict_approval(drug_name, indication, clinical_data, regulatory_status)
            )
            
            # Display probability
            prob_color = "🟢" if prediction.approval_probability >= 0.5 else "🔴"
            st.success(f"{prob_color} **Approval Probability: {prediction.approval_probability:.0%}**")
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Timeline", prediction.predicted_timeline)
            with col2:
                st.metric("Confidence", f"{prediction.confidence_score:.0%}")
            with col3:
                st.metric("Key Factors", len(prediction.key_factors))
            
            # Key factors
            st.subheader("Key Influencing Factors")
            for factor in prediction.key_factors:
                direction_emoji = "✅" if factor['direction'] == 'positive' else "⚠️"
                st.write(f"{direction_emoji} **{factor['factor']}**: {factor['impact']}")
            
            # Risk and success indicators
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Success Indicators")
                for indicator in prediction.success_indicators:
                    st.write(indicator)
            
            with col2:
                st.subheader("Risk Factors")
                for risk in prediction.risk_factors:
                    st.write(risk)
            
            # Recommendation
            st.subheader("Strategic Recommendation")
            st.markdown(prediction.recommendation)
            
            # Comparable drugs
            if prediction.comparable_drugs:
                st.subheader("Comparable Approved Drugs")
                for drug in prediction.comparable_drugs:
                    st.write(f"- {drug}")


def render_paper_analyzer_feature():
    """Render scientific paper analyzer interface."""
    st.header("📚 Automated Scientific Paper Analyzer")
    
    st.info("""
    **Patent-Worthy Innovation**: Hierarchical literature synthesis
    - Multi-level abstraction and summarization
    - Citation network influence scoring
    - Automated evidence quality assessment
    """)
    
    st.write("Demo: Analyze a scientific paper abstract")
    
    paper_title = st.text_input(
        "Paper Title",
        value="Efficacy and Safety of Novel Drug X in Patients with Advanced Cancer"
    )
    
    paper_abstract = st.text_area(
        "Abstract",
        value="""This Phase 3 randomized controlled trial evaluated the efficacy and safety of Drug X 
in 450 patients with advanced cancer. Patients were randomized 2:1 to Drug X (n=300) or placebo (n=150). 
The primary endpoint was progression-free survival (PFS). Results showed Drug X significantly improved PFS 
compared to placebo (HR=0.65, 95% CI 0.52-0.81, p<0.001). Median PFS was 8.2 months with Drug X versus 
4.1 months with placebo. Grade 3/4 adverse events occurred in 42% of Drug X patients versus 28% of placebo. 
Common adverse events included fatigue, nausea, and neutropenia. Drug X demonstrates significant clinical 
benefit in advanced cancer with a manageable safety profile.""",
        height=200
    )
    
    if st.button("📖 Analyze Paper", type="primary"):
        with st.spinner("Analyzing scientific paper..."):
            analyzer = PaperAnalyzer()
            
            paper_data = {
                "title": paper_title,
                "abstract": paper_abstract,
                "authors": ["Smith J", "Jones A", "Williams B"],
                "journal": "Journal of Clinical Oncology",
                "date": "2024-03-15",
                "year": 2024,
                "citations": 15,
                "pmid": "38234567"
            }
            
            summary = asyncio.run(analyzer.analyze_paper(paper_data))
            
            # Display summary
            st.success("✅ Analysis Complete!")
            
            # Quality score
            st.metric("Evidence Quality Score", f"{summary.quality_score:.0%}")
            
            # Summary
            st.subheader("📝 Summary")
            st.write(summary.summary)
            
            # Key findings
            st.subheader("🔑 Key Findings")
            for idx, finding in enumerate(summary.key_findings, 1):
                st.write(f"{idx}. {finding}")
            
            # Methodology and relevance
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔬 Methodology")
                st.write(summary.methodology)
            
            with col2:
                st.subheader("🏥 Clinical Relevance")
                st.write(summary.clinical_relevance)
            
            # Limitations
            st.subheader("⚠️ Limitations")
            for limitation in summary.limitations:
                st.write(f"- {limitation}")


def render_voice_assistant_feature():
    """Render voice assistant demo interface."""
    st.header("🎤 Voice-Activated Drug Intelligence Assistant")
    
    st.info("""
    **Patent-Worthy Innovation**: Hands-free pharmaceutical research
    - Medical terminology-aware NLP
    - Context-aware multi-turn conversations
    - Multi-language support with drug name translation
    """)
    
    st.warning("Voice input requires additional dependencies. Text demo available below.")
    
    # Text-based demo
    st.subheader("Text Command Demo")
    
    command = st.text_input(
        "Enter your question",
        placeholder="Tell me about aspirin side effects",
        help="Try: 'What is metformin?', 'Side effects of warfarin', 'Compare aspirin and ibuprofen'"
    )
    
    if st.button("🗣️ Process Command", type="primary"):
        if command:
            with st.spinner("Processing command..."):
                assistant = VoiceAssistant()
                
                result = asyncio.run(assistant.process_voice_command(command))
                
                # Display results
                st.success(f"✅ Intent: **{result.intent.replace('_', ' ').title()}**")
                st.metric("Confidence", f"{result.confidence:.0%}")
                
                if result.entities:
                    st.write("**Detected Entities:**")
                    for key, value in result.entities.items():
                        st.write(f"- {key.title()}: {value}")
                
                st.subheader("Response")
                st.info(result.response)
                
                st.subheader("Suggested Actions")
                
                # Store detected drug in session state
                detected_drug = result.entities.get('drug', 'aspirin')
                
                # Create functional action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if "View detailed drug profile" in result.suggested_actions or "view" in result.intent.lower():
                        if st.button("📋 View detailed drug profile", key="action_profile", use_container_width=True):
                            st.session_state['drug_search_query'] = detected_drug
                            st.info(f"✅ Saved! Now navigate to **💊 Drug Explorer** from the sidebar to view {detected_drug}'s profile")
                
                with col2:
                    if "Check side effects" in result.suggested_actions or "adverse" in result.intent.lower() or "side" in result.intent.lower():
                        if st.button("⚠️ Check side effects", key="action_side_effects", use_container_width=True):
                            st.session_state['drug_search_query'] = detected_drug
                            st.info(f"✅ Saved! Navigate to **💊 Drug Explorer** or **Analysis** page to check {detected_drug}'s side effects")
                
                with col3:
                    if "See clinical trials" in result.suggested_actions or "trial" in result.intent.lower() or "clinical" in result.intent.lower():
                        if st.button("🔬 See clinical trials", key="action_trials", use_container_width=True):
                            st.session_state['drug_search_query'] = detected_drug
                            st.info(f"✅ Saved! Navigate to **Analysis** page and search for {detected_drug} to see clinical trials")
                
                # Show stored search query
                if 'drug_search_query' in st.session_state:
                    st.success(f"""
                    📌 **Quick Access Instructions:**
                    
                    Your saved search: **{st.session_state['drug_search_query']}**
                    
                    **Option 1: Drug Explorer (Recommended)**
                    1. Click **💊 Drug Explorer** in the sidebar
                    2. Enter: `{st.session_state['drug_search_query']}`
                    3. View complete drug information including side effects
                    
                    **Option 2: Full Analysis**
                    1. Click **Analysis** in the sidebar
                    2. Enter: `{st.session_state['drug_search_query']}`
                    3. View clinical trials, FDA data, and more
                    """)
                    
                    # Clear button
                    if st.button("🗑️ Clear saved search", key="clear_search"):
                        del st.session_state['drug_search_query']
                        st.rerun()


def render_feature_comparison():
    """Render feature comparison matrix."""
    st.header("📈 Patent-Worthy Features Comparison")
    
    features_data = {
        "Feature": [
            "Drug Repurposing Engine",
            "Adverse Event Predictor",
            "Interaction Network Visualizer",
            "Voice Assistant",
            "Approval Predictor",
            "Paper Analyzer"
        ],
        "Innovation": [
            "Multi-modal similarity with GNN",
            "Temporal forecasting with XAI",
            "3D network + PK simulation",
            "Medical NLP + hands-free",
            "ML on 10K+ FDA decisions",
            "Hierarchical synthesis"
        ],
        "Patent Potential": ["High", "High", "Medium-High", "High", "High", "Medium"],
        "Technical Complexity": ["Advanced", "Advanced", "Intermediate", "Advanced", "Advanced", "Intermediate"],
        "Clinical Value": ["Very High", "Critical", "High", "High", "Very High", "High"],
        "Hackathon Impact": ["★★★★★", "★★★★★", "★★★★☆", "★★★★★", "★★★★★", "★★★☆☆"]
    }
    
    df = pd.DataFrame(features_data)
    st.dataframe(df, use_container_width=True, height=250)
    
    st.subheader("🏆 Competitive Advantages")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Technical Innovation:**
        - ✅ Novel ML algorithms
        - ✅ Real-time data integration
        - ✅ Explainable AI throughout
        - ✅ Multi-modal analysis
        - ✅ Advanced visualizations
        """)
    
    with col2:
        st.markdown("""
        **Business Value:**
        - ✅ Patent-worthy innovations
        - ✅ Solves real pharma problems
        - ✅ Scalable architecture
        - ✅ Multi-stakeholder appeal
        - ✅ Regulatory-grade quality
        """)
    
    st.subheader("🎯 Hackathon Strategy")
    st.success("""
    **Winning Formula:**
    1. **Demo** Drug Repurposing Engine (wow factor)
    2. **Show** Adverse Event Prediction (safety focus)
    3. **Highlight** FDA Approval Predictor (business value)
    4. **Mention** Voice Assistant (innovation bonus)
    
    **Key Messages:**
    - "AI-powered pharmaceutical intelligence"
    - "Patent-pending algorithms"
    - "Real-world clinical value"
    - "Scalable and production-ready"
    """)


if __name__ == "__main__":
    render_advanced_features_page()
