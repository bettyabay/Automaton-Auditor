"""
Judicial agent nodes for evidence evaluation and opinion rendering.

This module implements the Prosecutor, Defense, and Tech Lead judge nodes,
which analyze evidence collected by detectives and render independent
judicial opinions for each rubric dimension.

Each judge has a distinct persona with conflicting philosophies:
- Prosecutor: Adversarial, looks for gaps, security flaws, and laziness
- Defense: Forgiving, rewards effort, intent, and creative workarounds
- Tech Lead: Pragmatic, focuses on architectural soundness and maintainability
"""

import json
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.state import Evidence, JudicialOpinion


# Setup LLM with structured output
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.2)
structured_llm = llm.with_structured_output(JudicialOpinion)


# Prosecutor System Prompt
PROSECUTOR_PROMPT = """
You are the PROSECUTOR in a digital courtroom. Your philosophy: "Trust No One. Assume Vibe Coding."

Your role is to scrutinize evidence for gaps, security flaws, and laziness. You are adversarial and critical.

EVIDENCE PROVIDED:
{evidence}

RUBRIC DIMENSION: {criterion_name}
{forensic_instruction}

SUCCESS PATTERN: {success_pattern}
FAILURE PATTERN: {failure_pattern}

INSTRUCTIONS:

Be harsh - look for what's MISSING, not what's present

If the rubric asks for parallel execution and you see linear flow, score 1

If you see security flaws (os.system, no sandboxing), charge with "Security Negligence"

If judges return freeform text instead of Pydantic, charge with "Hallucination Liability"

Cite specific evidence files and line numbers

Return a JudicialOpinion with:

judge: "Prosecutor"

criterion_id: {criterion_id}

score: 1-5 (be strict - 5 only if perfect)

argument: Your harsh reasoning

cited_evidence: List of evidence IDs you used
"""


# Defense Attorney System Prompt
DEFENSE_PROMPT = """
You are the DEFENSE ATTORNEY in a digital courtroom. Your philosophy: "Reward Effort and Intent. Look for the Spirit of the Law."

Your role is to highlight creative workarounds, deep thought, and effort, even if implementation is imperfect.

EVIDENCE PROVIDED:
{evidence}

RUBRIC DIMENSION: {criterion_name}
{forensic_instruction}

SUCCESS PATTERN: {success_pattern}
FAILURE PATTERN: {failure_pattern}

INSTRUCTIONS:

Be generous - look for understanding and effort

If code is buggy but shows deep understanding of concepts, argue for higher score

Look at git history - struggle and iteration show learning

If architecture report shows deep thought, reward it even if code has syntax errors

Argue for partial credit when concepts are understood but execution flawed

Return a JudicialOpinion with:

judge: "Defense"

criterion_id: {criterion_id}

score: 1-5 (be generous - 3-4 for effort, 5 for excellence)

argument: Your supportive reasoning

cited_evidence: List of evidence IDs you used
"""


# Tech Lead System Prompt
TECH_LEAD_PROMPT = """
You are the TECH LEAD in a digital courtroom. Your philosophy: "Does it actually work? Is it maintainable?"

Your role is to evaluate architectural soundness, code cleanliness, and practical viability.

EVIDENCE PROVIDED:
{evidence}

RUBRIC DIMENSION: {criterion_name}
{forensic_instruction}

SUCCESS PATTERN: {success_pattern}
FAILURE PATTERN: {failure_pattern}

INSTRUCTIONS:

Be pragmatic - ignore both vibe and struggle, focus on artifacts

Check if operator.add reducers actually prevent data overwriting

Verify tool calls are isolated and safe

Assess technical debt - is the code maintainable?

You are the tie-breaker - provide realistic scores (1, 3, or 5 typically)

Give specific technical remediation advice

Return a JudicialOpinion with:

judge: "TechLead"

criterion_id: {criterion_id}

score: 1-5 (realistic - 1=broken, 3=works but debt, 5=production-ready)

argument: Your pragmatic reasoning with technical details

cited_evidence: List of evidence IDs you used
"""


def render_judicial_opinion(
    evidence_dict: Dict[str, List],
    criterion_id: str,
    persona: str,
    rubric_dimension: Dict
) -> JudicialOpinion:
    """
    Base function to render a judicial opinion for a specific criterion.
    
    This function takes evidence collected by detectives, a rubric dimension,
    and a judge persona, then uses a structured LLM to generate a JudicialOpinion.
    
    Args:
        evidence_dict: Dictionary mapping goal IDs to lists of Evidence objects
                     (e.g., {"git_forensic_analysis": [Evidence, ...]})
        criterion_id: The rubric dimension ID to evaluate
        persona: The judge persona ("Prosecutor", "Defense", or "TechLead")
        rubric_dimension: The rubric dimension dictionary containing:
                         - id: dimension ID
                         - name: dimension name
                         - forensic_instruction: instructions for evaluation
                         - success_pattern: what success looks like
                         - failure_pattern: what failure looks like
    
    Returns:
        JudicialOpinion object with judge's assessment
    
    Raises:
        ValueError: If persona is not recognized
        RuntimeError: If LLM call fails or returns invalid output
    """
    # Validate persona
    valid_personas = ["Prosecutor", "Defense", "TechLead"]
    if persona not in valid_personas:
        raise ValueError(f"Invalid persona: {persona}. Must be one of {valid_personas}")
    
    # Get evidence for this criterion
    evidence_list = evidence_dict.get(criterion_id, [])
    
    # Format evidence for prompt
    evidence_text = _format_evidence_for_prompt(evidence_list)
    
    # Get rubric dimension details
    criterion_name = rubric_dimension.get("name", criterion_id)
    forensic_instruction = rubric_dimension.get("forensic_instruction", "")
    success_pattern = rubric_dimension.get("success_pattern", "")
    failure_pattern = rubric_dimension.get("failure_pattern", "")
    
    # Select persona-specific prompt template
    if persona == "Prosecutor":
        prompt_template = PROSECUTOR_PROMPT
    elif persona == "Defense":
        prompt_template = DEFENSE_PROMPT
    elif persona == "TechLead":
        prompt_template = TECH_LEAD_PROMPT
    else:
        prompt_template = PROSECUTOR_PROMPT  # Default
    
    # Format the prompt
    formatted_prompt = prompt_template.format(
        evidence=evidence_text,
        criterion_name=criterion_name,
        criterion_id=criterion_id,
        forensic_instruction=forensic_instruction,
        success_pattern=success_pattern,
        failure_pattern=failure_pattern
    )
    
    # Create messages for LLM
    messages = [
        SystemMessage(content=formatted_prompt),
        HumanMessage(content=f"Evaluate the evidence for criterion: {criterion_name}")
    ]
    
    # Call structured LLM
    try:
        opinion = structured_llm.invoke(messages)
        
        # Ensure the opinion has the correct judge and criterion_id
        # (in case the LLM doesn't follow instructions perfectly)
        opinion.judge = persona
        opinion.criterion_id = criterion_id
        
        return opinion
    
    except Exception as e:
        # If structured output fails, return a default opinion with error
        return JudicialOpinion(
            judge=persona,
            criterion_id=criterion_id,
            score=1,  # Lowest score on error
            argument=f"Error rendering opinion: {str(e)}. Evidence may be insufficient or malformed.",
            cited_evidence=[]
        )


def _format_evidence_for_prompt(evidence_list: List) -> str:
    """
    Format a list of Evidence objects into a readable string for the prompt.
    
    Args:
        evidence_list: List of Evidence objects
    
    Returns:
        Formatted string describing the evidence
    """
    if not evidence_list:
        return "No evidence found for this criterion."
    
    formatted_parts = []
    for idx, evidence in enumerate(evidence_list, start=1):
        # Handle both Evidence objects and dicts
        if hasattr(evidence, 'found'):
            found = evidence.found
            content = evidence.content
            location = evidence.location
            rationale = evidence.rationale
            confidence = evidence.confidence
        elif isinstance(evidence, dict):
            found = evidence.get("found", False)
            content = evidence.get("content", "")
            location = evidence.get("location", "")
            rationale = evidence.get("rationale", "")
            confidence = evidence.get("confidence", 0.0)
        else:
            continue
        
        formatted_parts.append(
            f"Evidence #{idx}:\n"
            f"  Found: {found}\n"
            f"  Location: {location}\n"
            f"  Confidence: {confidence:.2f}\n"
            f"  Rationale: {rationale}\n"
            f"  Content: {content[:500]}{'...' if len(content) > 500 else ''}\n"
        )
    
    return "\n".join(formatted_parts)
