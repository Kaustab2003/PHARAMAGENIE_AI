from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew
from langchain.llms import OpenAI
import os

class MasterAgent:
    def __init__(self):
        self.llm = OpenAI(
            temperature=0.3,
            model_name="gpt-4"
        )
        self.agents = self._initialize_agents()

    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize all worker agents."""
        return {
            'iqvia_agent': Agent(
                role='Market Intelligence Specialist',
                goal='Analyze market data and commercial potential',
                backstory="""
                You are an expert in pharmaceutical market analysis with deep knowledge of drug commercialization,
                market trends, and competitive landscape. You provide insights on market size, growth potential,
                and commercial viability of drug repurposing opportunities.
                """,
                llm=self.llm,
                verbose=True
            ),
            'clinical_trials_agent': Agent(
                role='Clinical Research Analyst',
                goal='Analyze clinical trial data and safety profiles',
                backstory="""
                You are a clinical research specialist with expertise in analyzing clinical trial data,
                understanding mechanisms of action, and evaluating therapeutic potential across different
                disease areas.
                """,
                llm=self.llm,
                verbose=True
            ),
            'patent_agent': Agent(
                role='Intellectual Property Specialist',
                goal='Analyze patent landscape and freedom-to-operate',
                backstory="""
                You are a patent expert with deep knowledge of pharmaceutical patents, their expiration dates,
                and freedom-to-operate analyses. You can identify potential IP barriers and opportunities.
                """,
                llm=self.llm,
                verbose=True
            )
        }

    def _create_tasks(self, drug_name: str, therapeutic_area: Optional[str] = None) -> Dict[str, Task]:
        """Create tasks for each agent."""
        tasks = {}
        
        # Market analysis task
        tasks['market_analysis'] = Task(
            description=f"""
            Analyze the market potential for {drug_name} {'in ' + therapeutic_area if therapeutic_area else ''}.
            Consider:
            - Current market size and growth projections
            - Competitive landscape
            - Unmet needs in the therapeutic area
            - Potential market share
            - Commercial viability score (1-10)
            
            Provide a detailed market analysis report.
            """,
            agent=self.agents['iqvia_agent'],
            expected_output="A detailed market analysis report with commercial potential score."
        )

        # Clinical trials task
        tasks['clinical_analysis'] = Task(
            description=f"""
            Analyze clinical trial data for {drug_name} {'in ' + therapeutic_area if therapeutic_area else ''}.
            Consider:
            - Existing clinical evidence
            - Safety profile
            - Mechanism of action
            - Potential therapeutic applications
            - Clinical trial success probability (1-10)
            
            Provide a clinical assessment report.
            """,
            agent=self.agents['clinical_trials_agent'],
            expected_output="A clinical assessment report with trial success probability score."
        )

        # Patent analysis task
        tasks['patent_analysis'] = Task(
            description=f"""
            Analyze the patent landscape for {drug_name}.
            Consider:
            - Current patent status and expiration dates
            - Freedom-to-operate analysis
            - Potential IP challenges
            - Patent strength score (1-10)
            
            Provide a patent landscape report.
            """,
            agent=self.agents['patent_agent'],
            expected_output="A patent landscape report with freedom-to-operate analysis."
        )

        return tasks

    def _calculate_innovation_score(self, results: Dict[str, Any]) -> float:
        """Calculate the innovation score based on analysis results."""
        # Simple weighted average for now - can be enhanced
        weights = {
            'market_score': 0.4,
            'clinical_score': 0.3,
            'patent_score': 0.3
        }
        
        return (
            results.get('market_score', 0) * weights['market_score'] +
            results.get('clinical_score', 0) * weights['clinical_score'] +
            results.get('patent_score', 0) * weights['patent_score']
        )

    def orchestrate_analysis(self, drug_name: str, therapeutic_area: Optional[str] = None) -> Dict[str, Any]:
        """Orchestrate the analysis across all agents."""
        # Create tasks
        tasks = self._create_tasks(drug_name, therapeutic_area)
        
        # Execute tasks in parallel
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=list(tasks.values()),
            verbose=2
        )
        
        # Execute the workflow
        results = crew.kickoff()
        
        # Process results and calculate scores
        processed_results = {
            'drug_name': drug_name,
            'therapeutic_area': therapeutic_area or 'General',
            'market_analysis': results.get('market_analysis', {}),
            'clinical_analysis': results.get('clinical_analysis', {}),
            'patent_analysis': results.get('patent_analysis', {}),
            'innovation_score': self._calculate_innovation_score({
                'market_score': results.get('market_analysis', {}).get('score', 0),
                'clinical_score': results.get('clinical_analysis', {}).get('score', 0),
                'patent_score': results.get('patent_analysis', {}).get('score', 0)
            })
        }
        
        return processed_results
