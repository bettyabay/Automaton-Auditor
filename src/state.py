"""
State management for the Automaton Auditor system.

This module defines the Pydantic models and TypedDict state structure
for the hierarchical agent swarm. The state uses reducers to prevent
data overwriting during parallel execution.
"""

import operator
from typing import Annotated, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# --- Detective Output ---


class Evidence(BaseModel):
    """
    Forensic evidence collected by Detective agents.
    
    This model represents objective facts discovered during code analysis.
    Detectives do not opinionate; they only report what they find.
    
    Attributes:
        goal: The specific forensic goal this evidence addresses
        found: Whether the artifact exists (boolean fact)
        content: Optional content of the artifact (e.g., code snippet, text)
        location: File path, commit hash, or other location identifier
        rationale: Explanation of why this evidence supports the goal
        confidence: Confidence score between 0.0 and 1.0
    """
    
    goal: str = Field(
        description="The specific forensic goal this evidence addresses"
    )
    found: bool = Field(
        description="Whether the artifact exists (objective fact)"
    )
    content: Optional[str] = Field(
        default=None,
        description="Optional content of the artifact (code snippet, text, etc.)"
    )
    location: str = Field(
        description="File path, commit hash, or other location identifier"
    )
    rationale: str = Field(
        description=(
            "Your rationale for your confidence "
            "on the evidence you find for this particular goal"
        )
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )


# --- Judge Output ---


class JudicialOpinion(BaseModel):
    """
    Opinion rendered by a Judge agent for a specific criterion.
    
    Each Judge (Prosecutor, Defense, Tech Lead) provides an independent
    assessment of the evidence for each rubric dimension.
    
    Attributes:
        judge: The persona rendering this opinion
        criterion_id: The rubric dimension ID this opinion addresses
        score: Score from 1-5 for this criterion
        argument: The reasoning behind the score
        cited_evidence: List of evidence IDs or locations that support this opinion
    """
    
    judge: Literal["Prosecutor", "Defense", "TechLead"] = Field(
        description="The persona rendering this opinion"
    )
    criterion_id: str = Field(
        description="The rubric dimension ID this opinion addresses"
    )
    score: int = Field(
        ge=1,
        le=5,
        description="Score from 1-5 for this criterion"
    )
    argument: str = Field(
        description="The reasoning behind the score"
    )
    cited_evidence: List[str] = Field(
        default_factory=list,
        description="List of evidence IDs or locations that support this opinion"
    )


# --- Chief Justice Output ---


class CriterionResult(BaseModel):
    """
    Final verdict for a single rubric criterion.
    
    This synthesizes the three judicial opinions into a final score
    with conflict resolution and remediation guidance.
    
    Attributes:
        dimension_id: The rubric dimension ID
        dimension_name: Human-readable name of the dimension
        final_score: Final score from 1-5 after synthesis
        judge_opinions: All three judicial opinions (Prosecutor, Defense, Tech Lead)
        dissent_summary: Summary of disagreement when score variance > 2
        remediation: Specific file-level instructions for improvement
    """
    
    dimension_id: str = Field(
        description="The rubric dimension ID"
    )
    dimension_name: str = Field(
        description="Human-readable name of the dimension"
    )
    final_score: int = Field(
        ge=1,
        le=5,
        description="Final score from 1-5 after synthesis"
    )
    judge_opinions: List[JudicialOpinion] = Field(
        default_factory=list,
        description="All three judicial opinions (Prosecutor, Defense, Tech Lead)"
    )
    dissent_summary: Optional[str] = Field(
        default=None,
        description="Required when score variance > 2, explains the conflict"
    )
    remediation: str = Field(
        description=(
            "Specific file-level instructions "
            "for improvement"
        )
    )


class AuditReport(BaseModel):
    """
    Final audit report synthesizing all evidence and judicial opinions.
    
    This is the complete output of the Automaton Auditor swarm,
    containing the executive summary, criterion-by-criterion breakdown,
    and actionable remediation plan.
    
    Attributes:
        repo_url: The GitHub repository URL that was audited
        executive_summary: High-level summary of findings
        overall_score: Aggregate score across all criteria
        criteria: List of criterion results with detailed breakdowns
        remediation_plan: Comprehensive remediation guidance
    """
    
    repo_url: str = Field(
        description="The GitHub repository URL that was audited"
    )
    executive_summary: str = Field(
        description="High-level summary of findings and overall verdict"
    )
    overall_score: float = Field(
        ge=1.0,
        le=5.0,
        description="Aggregate score across all criteria"
    )
    criteria: List[CriterionResult] = Field(
        default_factory=list,
        description="List of criterion results with detailed breakdowns"
    )
    remediation_plan: str = Field(
        description="Comprehensive remediation guidance grouped by criterion"
    )


# --- Graph State ---


class AgentState(TypedDict):
    """
    The shared state structure for the LangGraph StateGraph.
    
    This TypedDict defines the state schema that flows through all nodes.
    Critical: Uses Annotated reducers to prevent data overwriting during
    parallel execution.
    
    Attributes:
        repo_url: Target GitHub repository URL
        pdf_path: Path to the PDF report to analyze
        rubric_dimensions: List of rubric dimension configurations
        evidences: Dictionary mapping criterion_id to list of Evidence objects
        opinions: List of all JudicialOpinion objects from all judges
        final_report: The synthesized AuditReport from Chief Justice
    
    Reducer Behavior:
        - evidences: Uses operator.ior (dict update) to merge evidence dicts
          from parallel detectives without overwriting
        - opinions: Uses operator.add (list concatenation) to combine
          opinions from parallel judges without overwriting
    
    Example of Reducer Protection:
        Without reducers, if two detectives run in parallel:
            Detective A: evidences = {"criterion_1": [evidence_a]}
            Detective B: evidences = {"criterion_2": [evidence_b]}
            Final state might only contain Detective B's data (overwrite)
        
        With operator.ior reducer:
            Detective A: evidences = {"criterion_1": [evidence_a]}
            Detective B: evidences = {"criterion_2": [evidence_b]}
            Final state: {"criterion_1": [evidence_a], "criterion_2": [evidence_b]}
            (Both preserved via dict merge)
        
        Similarly for opinions with operator.add:
            Judge A: opinions = [opinion_1]
            Judge B: opinions = [opinion_2]
            Final state: [opinion_1, opinion_2] (concatenated, not overwritten)
    """
    
    repo_url: str
    pdf_path: str
    rubric_dimensions: List[Dict]
    # Use reducers to prevent parallel agents from overwriting data
    evidences: Annotated[
        Dict[str, List[Evidence]], 
        operator.ior  # Dict update merge: preserves all keys from parallel executions
    ]
    opinions: Annotated[
        List[JudicialOpinion], 
        operator.add  # List concatenation: preserves all items from parallel executions
    ]
    final_report: Optional[AuditReport]


# --- Example: Demonstrating Reducer Protection ---


def demonstrate_reducer_protection():
    """
    Example demonstrating how reducers prevent data overwriting.
    
    This function shows what happens with and without reducers
    when multiple agents execute in parallel.
    """
    # Simulate parallel execution without reducers (DANGEROUS)
    print("=== WITHOUT REDUCERS (Data Loss Risk) ===")
    state_without_reducer = {"evidences": {}}
    
    # Detective A writes to state
    detective_a_state = {"evidences": {"criterion_1": [Evidence(
        goal="Find state.py",
        found=True,
        location="src/state.py",
        rationale="File exists",
        confidence=1.0
    )]}}
    state_without_reducer.update(detective_a_state)
    print(f"After Detective A: {state_without_reducer}")
    
    # Detective B writes to state (might overwrite if not careful)
    detective_b_state = {"evidences": {"criterion_2": [Evidence(
        goal="Find graph.py",
        found=True,
        location="src/graph.py",
        rationale="File exists",
        confidence=1.0
    )]}}
    # Without reducer, this could overwrite if same key or if state is replaced
    state_without_reducer.update(detective_b_state)
    print(f"After Detective B: {state_without_reducer}")
    print("Risk: If state is replaced entirely, Detective A's data is lost!\n")
    
    # Simulate parallel execution WITH reducers (SAFE)
    print("=== WITH REDUCERS (Data Preservation) ===")
    state_with_reducer = {"evidences": {}}
    
    # Detective A writes to state
    detective_a_evidences = {"criterion_1": [Evidence(
        goal="Find state.py",
        found=True,
        location="src/state.py",
        rationale="File exists",
        confidence=1.0
    )]}
    # operator.ior merges dictionaries, preserving all keys
    state_with_reducer["evidences"] = operator.ior(
        state_with_reducer.get("evidences", {}),
        detective_a_evidences
    )
    print(f"After Detective A: {state_with_reducer}")
    
    # Detective B writes to state
    detective_b_evidences = {"criterion_2": [Evidence(
        goal="Find graph.py",
        found=True,
        location="src/graph.py",
        rationale="File exists",
        confidence=1.0
    )]}
    # operator.ior merges, preserving both A and B's data
    state_with_reducer["evidences"] = operator.ior(
        state_with_reducer["evidences"],
        detective_b_evidences
    )
    print(f"After Detective B: {state_with_reducer}")
    print("Result: Both detectives' evidence preserved!\n")
    
    # Demonstrate list reducer (operator.add)
    print("=== LIST REDUCER (operator.add) ===")
    state_opinions = {"opinions": []}
    
    # Judge A adds opinion
    judge_a_opinion = [JudicialOpinion(
        judge="Prosecutor",
        criterion_id="criterion_1",
        score=1,
        argument="Missing reducers",
        cited_evidence=["evidence_1"]
    )]
    state_opinions["opinions"] = operator.add(
        state_opinions.get("opinions", []),
        judge_a_opinion
    )
    print(f"After Prosecutor: {len(state_opinions['opinions'])} opinions")
    
    # Judge B adds opinion
    judge_b_opinion = [JudicialOpinion(
        judge="Defense",
        criterion_id="criterion_1",
        score=5,
        argument="Good effort",
        cited_evidence=["evidence_2"]
    )]
    state_opinions["opinions"] = operator.add(
        state_opinions["opinions"],
        judge_b_opinion
    )
    print(f"After Defense: {len(state_opinions['opinions'])} opinions")
    print("Result: Both opinions preserved in list!")


if __name__ == "__main__":
    # Run the demonstration
    demonstrate_reducer_protection()
