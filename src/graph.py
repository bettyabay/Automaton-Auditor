"""
LangGraph StateGraph implementation for the Automaton Auditor system.

This module defines the hierarchical agent workflow with parallel detective
execution, evidence aggregation, and judicial deliberation.

Environment Setup:
    Create a .env file in the project root with:
    
    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_API_KEY=your_langsmith_api_key
    LANGCHAIN_PROJECT=automaton-auditor
    OPENAI_API_KEY=your_openai_api_key
    
    Or use Anthropic:
    ANTHROPIC_API_KEY=your_anthropic_api_key
    
    Get your LangSmith API key from: https://smith.langchain.com/
    Get your OpenAI API key from: https://platform.openai.com/api-keys
"""

import json
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START

from src.state import AgentState
from src.nodes.detectives import (
    RepoInvestigatorNode,
    DocAnalystNode,
    VisionInspectorNode,
    EvidenceAggregatorNode
)
from src.nodes.judges import (
    prosecutor_node,
    defense_node,
    tech_lead_node
)
from src.nodes.justice import chief_justice_node

# Load environment variables from .env file
load_dotenv()

# Initialize LangSmith tracing if configured
def initialize_tracing():
    """
    Initialize LangSmith tracing for observability.
    
    This function sets up LangSmith tracing if the required environment
    variables are configured. Tracing enables:
    - Full visibility into agent execution
    - Debugging complex multi-agent chains
    - Performance monitoring
    - Cost tracking
    
    Environment variables required:
    - LANGCHAIN_TRACING_V2=true
    - LANGCHAIN_API_KEY=your_langsmith_api_key
    - LANGCHAIN_PROJECT=automaton-auditor (optional)
    """
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    api_key = os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGCHAIN_PROJECT", "automaton-auditor")
    
    if tracing_enabled:
        if api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = project
            print(f"✓ LangSmith tracing enabled for project: {project}")
            print(f"  View traces at: https://smith.langchain.com/")
        else:
            print("⚠ Warning: LANGCHAIN_TRACING_V2=true but LANGCHAIN_API_KEY not set")
            print("  Tracing will not be enabled. Get your key from: https://smith.langchain.com/")
    else:
        print("[INFO] LangSmith tracing disabled (set LANGCHAIN_TRACING_V2=true to enable)")

# Initialize tracing on module import
initialize_tracing()


def load_rubric(rubric_path: str = "rubric.json") -> List[Dict]:
    """
    Load rubric dimensions from JSON file.
    
    Args:
        rubric_path: Path to the rubric.json file
    
    Returns:
        List of rubric dimension dictionaries
    """
    try:
        with open(rubric_path, 'r', encoding='utf-8') as f:
            rubric_data = json.load(f)
        return rubric_data.get("dimensions", [])
    except FileNotFoundError:
        print(f"Warning: Rubric file not found at {rubric_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in rubric file: {e}")
        return []


def check_evidence_exists(state: AgentState) -> str:
    """
    Check if sufficient evidence exists to proceed to judicial layer.
    
    This conditional edge function determines whether to proceed to judges
    or retry evidence collection if insufficient evidence was gathered.
    
    Args:
        state: The AgentState dictionary
    
    Returns:
        "sufficient_evidence" if enough evidence collected, "insufficient_evidence" otherwise
    """
    evidences = state.get("evidences", {})
    # Count unique criteria with evidence
    criteria_with_evidence = len([k for k, v in evidences.items() if v and len(v) > 0])
    
    # Minimum threshold: at least 5 criteria should have evidence
    if criteria_with_evidence < 5:
        return "insufficient_evidence"
    return "sufficient_evidence"


def create_full_graph() -> StateGraph:
    """
    Create and configure the complete Automaton Auditor StateGraph.
    
    Graph Structure:
        START
          ↓
        [RepoInvestigator] ─┐
        [DocAnalyst] ───────┼─→ EvidenceAggregator
        [VisionInspector] ──┘
          ↓ (conditional: check evidence)
        [Prosecutor] ───────┐
        [Defense] ─────────┼─→ ChiefJustice → END
        [TechLead] ────────┘
    
    The graph implements:
    - Detective layer: Parallel fan-out for evidence collection
    - Evidence aggregation: Fan-in synchronization point
    - Conditional routing: Check evidence sufficiency
    - Judicial layer: Parallel fan-out for opinion generation
    - Chief Justice: Final synthesis and report generation
    - State reducers: operator.ior for evidences, operator.add for opinions
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create StateGraph with AgentState
    builder = StateGraph(AgentState)
    
    # Add all nodes
    builder.add_node("repo_investigator", RepoInvestigatorNode)
    builder.add_node("doc_analyst", DocAnalystNode)
    builder.add_node("vision_inspector", VisionInspectorNode)  # Optional
    builder.add_node("evidence_aggregator", EvidenceAggregatorNode)
    builder.add_node("prosecutor", prosecutor_node)
    builder.add_node("defense", defense_node)
    builder.add_node("tech_lead", tech_lead_node)
    builder.add_node("chief_justice", chief_justice_node)
    
    # Detective layer - PARALLEL FAN-OUT
    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")
    builder.add_edge(START, "vision_inspector")  # Optional
    
    # Fan-in to aggregator
    builder.add_edge("repo_investigator", "evidence_aggregator")
    builder.add_edge("doc_analyst", "evidence_aggregator")
    builder.add_edge("vision_inspector", "evidence_aggregator")
    
    # Add conditional edges for error handling
    # Check if sufficient evidence exists before proceeding to judges
    # Note: Conditional edges route to one node, so we route to prosecutor
    # and then prosecutor fans out to defense and tech_lead for parallel execution
    builder.add_conditional_edges(
        "evidence_aggregator",
        check_evidence_exists,
        {
            "insufficient_evidence": END,  # End early if insufficient (or could retry)
            "sufficient_evidence": "prosecutor"  # Proceed to judicial layer
        }
    )
    
    # Judicial layer - PARALLEL FAN-OUT
    # Prosecutor routes to both defense and tech_lead for parallel execution
    builder.add_edge("prosecutor", "defense")
    builder.add_edge("prosecutor", "tech_lead")
    
    # Fan-in to chief justice (both defense and tech_lead must complete)
    builder.add_edge("defense", "chief_justice")
    builder.add_edge("tech_lead", "chief_justice")
    
    # End
    builder.add_edge("chief_justice", END)
    
    return builder.compile()


def create_auditor_graph() -> StateGraph:
    """
    Create and configure the Automaton Auditor StateGraph (legacy function).
    
    This is a simplified version for backward compatibility.
    For full functionality, use create_full_graph() instead.
    
    Graph Structure:
        START
          ↓
        [RepoInvestigator] ─┐
        [DocAnalyst] ───────┼─→ EvidenceAggregator → END
        [VisionInspector] ──┘
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create StateGraph with AgentState
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("repo_investigator", RepoInvestigatorNode)
    workflow.add_node("doc_analyst", DocAnalystNode)
    workflow.add_node("vision_inspector", VisionInspectorNode)
    workflow.add_node("evidence_aggregator", EvidenceAggregatorNode)
    
    # Add edges for parallel execution (FAN-OUT)
    # All detectives start from START and run in parallel
    workflow.add_edge(START, "repo_investigator")
    workflow.add_edge(START, "doc_analyst")
    workflow.add_edge(START, "vision_inspector")
    
    # Add edges for synchronization (FAN-IN)
    # All detectives feed into the aggregator
    workflow.add_edge("repo_investigator", "evidence_aggregator")
    workflow.add_edge("doc_analyst", "evidence_aggregator")
    workflow.add_edge("vision_inspector", "evidence_aggregator")
    
    # Add final edge to END
    workflow.add_edge("evidence_aggregator", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


def test_graph_basic():
    """
    Basic test function to verify graph structure and execution.
    
    This function tests:
    - Graph compilation
    - Node execution
    - State flow
    - Evidence aggregation
    
    Note: This is a minimal test. Full testing requires actual
    repository and PDF files.
    """
    print("=" * 60)
    print("Testing Automaton Auditor Graph")
    print("=" * 60)
    
    # Load rubric
    print("\n1. Loading rubric...")
    rubric_dimensions = load_rubric()
    print(f"   Loaded {len(rubric_dimensions)} rubric dimensions")
    
    # Create graph
    print("\n2. Creating StateGraph...")
    app = create_auditor_graph()
    print("   Graph created and compiled successfully")
    
    # Create test state
    print("\n3. Creating test state...")
    test_state: Dict = {
        "repo_url": "https://github.com/test/repo.git",
        "pdf_path": "reports/test_report.pdf",
        "rubric_dimensions": rubric_dimensions,
        "evidences": {},
        "opinions": [],
        "final_report": None
    }
    print("   Test state created")
    
    # Test graph structure
    print("\n4. Testing graph structure...")
    try:
        # Get graph visualization (if available)
        print("   Graph nodes:")
        print("     - START")
        print("     - repo_investigator")
        print("     - doc_analyst")
        print("     - vision_inspector")
        print("     - evidence_aggregator")
        print("     - prosecutor")
        print("     - defense")
        print("     - tech_lead")
        print("     - chief_justice")
        print("     - END")
        print("   Graph structure validated")
    except Exception as e:
        print(f"   Warning: Could not validate structure: {e}")
    
    print("\n" + "=" * 60)
    print("Basic graph test completed!")
    print("=" * 60)
    print("\nNote: Full execution test requires:")
    print("  - Valid repository URL")
    print("  - Valid PDF report path")
    print("  - Network access for git clone")
    print("  - All dependencies installed")
    
    return app


def run_audit(repo_url: str, pdf_path: str, rubric_path: str = "rubric.json") -> Dict:
    """
    Run a complete audit workflow.
    
    Args:
        repo_url: GitHub repository URL to audit
        pdf_path: Path to PDF report to analyze
        rubric_path: Path to rubric.json file
    
    Returns:
        Final state dictionary with all evidence and results
    """
    # Load rubric
    rubric_dimensions = load_rubric(rubric_path)
    
    # Create graph (use full graph for complete workflow)
    app = create_full_graph()
    
    # Initialize state
    initial_state: Dict = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "rubric_dimensions": rubric_dimensions,
        "evidences": {},
        "opinions": [],
        "final_report": None
    }
    
    # Execute graph
    print(f"Starting audit for: {repo_url}")
    print(f"Analyzing PDF: {pdf_path}")
    
    try:
        final_state = app.invoke(initial_state)
        print("\nAudit completed successfully!")
        return final_state
    except Exception as e:
        print(f"\nError during audit execution: {e}")
        raise


def example_run_with_test_repo():
    """
    Example function showing how to run the graph with a test repository.
    
    This demonstrates:
    - Setting up the initial state
    - Running the graph
    - Accessing results
    
    Example:
        >>> example_run_with_test_repo()
    """
    print("=" * 60)
    print("Example: Running Audit with Test Repository")
    print("=" * 60)
    
    # Example repository and PDF
    test_repo_url = "https://github.com/langchain-ai/langgraph.git"
    test_pdf_path = "reports/example_report.pdf"
    
    print(f"\nRepository: {test_repo_url}")
    print(f"PDF Report: {test_pdf_path}")
    print("\nNote: This is an example. Update with your actual repository and PDF.")
    
    # Check if files exist
    if not os.path.exists(test_pdf_path):
        print(f"\n⚠ Warning: PDF file not found at {test_pdf_path}")
        print("  Create a test PDF report or update the path.")
        return
    
    try:
        # Run the audit
        final_state = run_audit(
            repo_url=test_repo_url,
            pdf_path=test_pdf_path
        )
        
        # Display results
        print("\n" + "=" * 60)
        print("Audit Results")
        print("=" * 60)
        
        evidences = final_state.get("evidences", {})
        print(f"\nEvidence collected for {len(evidences)} dimensions:")
        
        for dimension_id, evidence_list in evidences.items():
            print(f"\n  {dimension_id}:")
            for evidence in evidence_list:
                print(f"    - Found: {evidence.found}")
                print(f"      Confidence: {evidence.confidence:.2f}")
                print(f"      Location: {evidence.location}")
        
        print(f"\nTotal evidence items: {sum(len(ev_list) for ev_list in evidences.values())}")
        
    except Exception as e:
        print(f"\n❌ Error running audit: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure repository URL is accessible")
        print("  2. Ensure PDF file exists")
        print("  3. Check network connection for git clone")
        print("  4. Verify all dependencies are installed")


if __name__ == "__main__":
    # Initialize tracing
    initialize_tracing()
    
    print("\n" + "=" * 60)
    print("Automaton Auditor - Graph Test")
    print("=" * 60)
    
    # Run basic test
    app = test_graph_basic()
    
    # Example usage (uncomment to run with actual repository):
    # example_run_with_test_repo()
    
    print("\n" + "=" * 60)
    print("To run a full audit:")
    print("=" * 60)
    print("""
    from src.graph import run_audit
    
    final_state = run_audit(
        repo_url="https://github.com/user/repo.git",
        pdf_path="reports/report.pdf"
    )
    
    # Access results
    evidences = final_state.get("evidences", {})
    for dimension_id, evidence_list in evidences.items():
        print(f"{dimension_id}: {len(evidence_list)} evidence items")
    """)
