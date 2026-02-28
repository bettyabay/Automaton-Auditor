"""
Chief Justice synthesis engine for resolving conflicting judicial opinions.

This module implements deterministic conflict resolution rules to synthesize
the three judicial opinions (Prosecutor, Defense, Tech Lead) into final
criterion scores and remediation guidance.

The Chief Justice uses hardcoded Python logic (not LLM prompts) to ensure
deterministic, reproducible synthesis following the synthesis_rules from
the rubric.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

from src.state import AgentState, AuditReport, CriterionResult, JudicialOpinion


def load_synthesis_rules(rubric_path: str = "rubric.json") -> Dict:
    """
    Load synthesis rules from rubric.json file.
    
    Args:
        rubric_path: Path to the rubric.json file
    
    Returns:
        Dictionary containing synthesis rules
    """
    try:
        with open(rubric_path, 'r', encoding='utf-8') as f:
            rubric_data = json.load(f)
        return rubric_data.get("synthesis_rules", {})
    except FileNotFoundError:
        print(f"Warning: Rubric file not found at {rubric_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in rubric file: {e}")
        return {}


class ChiefJusticeNode:
    """
    Chief Justice synthesis engine.
    
    This class implements deterministic rules for resolving conflicting
    judicial opinions into final criterion scores. It uses hardcoded
    Python logic to ensure reproducibility and consistency.
    """
    
    def __init__(self, rubric_path: str = "rubric.json"):
        """
        Initialize the Chief Justice node.
        
        Args:
            rubric_path: Path to the rubric.json file containing synthesis rules
        """
        self.rubric_path = rubric_path
        self.synthesis_rules = load_synthesis_rules(rubric_path)
        self.rubric_dimensions = self._load_rubric_dimensions()
    
    def _load_rubric_dimensions(self) -> List[Dict]:
        """Load rubric dimensions for name lookup."""
        try:
            with open(self.rubric_path, 'r', encoding='utf-8') as f:
                rubric_data = json.load(f)
            return rubric_data.get("dimensions", [])
        except Exception:
            return []
    
    def apply_security_override(self, opinions: List[JudicialOpinion]) -> bool:
        """
        Check if any prosecutor found security flaw.
        
        This implements the security_override rule: if the Prosecutor
        identifies a confirmed security vulnerability, the score is capped
        at 3 regardless of Defense arguments.
        
        Args:
            opinions: List of JudicialOpinion objects from all three judges
        
        Returns:
            True if security flaw detected, False otherwise
        """
        for op in opinions:
            if op.judge == "Prosecutor":
                argument_lower = op.argument.lower()
                if "security" in argument_lower:
                    # Check for specific security violations
                    if "os.system" in argument_lower or "no sandbox" in argument_lower:
                        return True
                    # Check for other security-related terms
                    security_indicators = [
                        "shell injection",
                        "command injection",
                        "unsanitized",
                        "raw os.system",
                        "tempfile not used",
                        "sandboxing missing"
                    ]
                    if any(indicator in argument_lower for indicator in security_indicators):
                        return True
        return False
    
    def calculate_score_variance(self, opinions: List[JudicialOpinion]) -> float:
        """
        Calculate the variance in scores across all opinions.
        
        Args:
            opinions: List of JudicialOpinion objects
        
        Returns:
            Float representing the difference between max and min scores
        """
        if not opinions:
            return 0.0
        scores = [op.score for op in opinions]
        return float(max(scores) - min(scores))
    
    def check_fact_supremacy(self, opinions: List[JudicialOpinion]) -> bool:
        """
        Check if Defense claims contradict evidence (fact supremacy rule).
        
        This implements the fact_supremacy rule: if the Defense claims
        something exists but evidence shows it doesn't, the Defense is
        overruled.
        
        Args:
            opinions: List of JudicialOpinion objects
        
        Returns:
            True if Defense should be overruled, False otherwise
        """
        defense_opinions = [op for op in opinions if op.judge == "Defense"]
        prosecutor_opinions = [op for op in opinions if op.judge == "Prosecutor"]
        
        for defense_op in defense_opinions:
            defense_arg = defense_op.argument.lower()
            # Check if Defense claims something exists
            positive_claims = [
                "found", "exists", "present", "implemented", "shows",
                "demonstrates", "contains", "has"
            ]
            
            if any(claim in defense_arg for claim in positive_claims):
                # Check if Prosecutor found evidence to the contrary
                for pros_op in prosecutor_opinions:
                    pros_arg = pros_op.argument.lower()
                    # Look for contradictions
                    if ("missing" in pros_arg or "not found" in pros_arg or 
                        "absent" in pros_arg or "no evidence" in pros_arg):
                        # If Prosecutor has lower score and mentions missing evidence
                        if pros_op.score < defense_op.score:
                            return True
        
        return False
    
    def generate_dissent_summary(self, opinions: List[JudicialOpinion]) -> str:
        """
        Generate a summary explaining why judges disagreed.
        
        This is required when score variance > 2 (dissent_requirement rule).
        
        Args:
            opinions: List of JudicialOpinion objects
        
        Returns:
            String summarizing the disagreement
        """
        if not opinions:
            return "No opinions provided."
        
        # Group opinions by judge
        prosecutor_ops = [op for op in opinions if op.judge == "Prosecutor"]
        defense_ops = [op for op in opinions if op.judge == "Defense"]
        tech_lead_ops = [op for op in opinions if op.judge == "TechLead"]
        
        summary_parts = []
        
        if prosecutor_ops and defense_ops:
            pros_score = prosecutor_ops[0].score
            def_score = defense_ops[0].score
            variance = abs(pros_score - def_score)
            
            if variance > 2:
                summary_parts.append(
                    f"Significant disagreement (variance: {variance}): "
                    f"Prosecutor scored {pros_score} while Defense scored {def_score}."
                )
                
                if prosecutor_ops:
                    summary_parts.append(
                        f"Prosecutor's argument: {prosecutor_ops[0].argument[:200]}..."
                    )
                if defense_ops:
                    summary_parts.append(
                        f"Defense's argument: {defense_ops[0].argument[:200]}..."
                    )
        
        if tech_lead_ops:
            tech_score = tech_lead_ops[0].score
            summary_parts.append(f"Tech Lead scored {tech_score}.")
        
        return "\n\n".join(summary_parts) if summary_parts else "No significant dissent."
    
    def generate_remediation(self, opinions: List[JudicialOpinion], final_score: int) -> str:
        """
        Generate specific file-level remediation instructions.
        
        Args:
            opinions: List of JudicialOpinion objects
            final_score: The final synthesized score
        
        Returns:
            String with remediation guidance
        """
        remediation_parts = []
        
        # If score is low, provide general remediation
        if final_score <= 2:
            remediation_parts.append(
                "CRITICAL: Significant improvements required. Review all cited evidence "
                "and address the fundamental issues identified by the judges."
            )
        
        # Extract specific file references from opinions
        file_references = []
        for op in opinions:
            # Look for file paths in cited_evidence
            for evidence_id in op.cited_evidence:
                if "/" in evidence_id or ".py" in evidence_id or ".md" in evidence_id:
                    file_references.append(evidence_id)
        
        if file_references:
            unique_files = list(set(file_references))
            remediation_parts.append(
                f"Files requiring attention: {', '.join(unique_files[:5])}"
            )
        
        # Add specific guidance based on prosecutor findings
        prosecutor_ops = [op for op in opinions if op.judge == "Prosecutor"]
        if prosecutor_ops:
            pros_arg = prosecutor_ops[0].argument.lower()
            if "security" in pros_arg:
                remediation_parts.append(
                    "SECURITY: Address security vulnerabilities immediately. "
                    "Ensure all external commands use subprocess.run() with proper "
                    "sandboxing via tempfile.TemporaryDirectory()."
                )
            if "parallel" in pros_arg and "linear" in pros_arg:
                remediation_parts.append(
                    "ARCHITECTURE: Implement parallel execution patterns. "
                    "Use LangGraph's fan-out/fan-in capabilities for concurrent node execution."
                )
        
        # Add guidance based on tech lead findings
        tech_lead_ops = [op for op in opinions if op.judge == "TechLead"]
        if tech_lead_ops:
            tech_arg = tech_lead_ops[0].argument.lower()
            if "technical debt" in tech_arg or "maintainability" in tech_arg:
                remediation_parts.append(
                    "MAINTAINABILITY: Refactor code to reduce technical debt. "
                    "Improve code organization and documentation."
                )
        
        return "\n".join(remediation_parts) if remediation_parts else "No specific remediation guidance available."
    
    def get_criterion_name(self, criterion_id: str) -> str:
        """
        Get the human-readable name for a criterion ID.
        
        Args:
            criterion_id: The rubric dimension ID
        
        Returns:
            Human-readable name of the criterion
        """
        for dimension in self.rubric_dimensions:
            if dimension.get("id") == criterion_id:
                return dimension.get("name", criterion_id)
        return criterion_id
    
    def resolve_criterion(
        self, 
        opinions: List[JudicialOpinion], 
        criterion_id: str
    ) -> CriterionResult:
        """
        Apply deterministic rules to resolve conflicting opinions.
        
        This method implements the synthesis rules from rubric.json:
        1. Security Override: Security flaws cap score at 3
        2. Fact Supremacy: Evidence overrules judicial opinion
        3. Functionality Weight: Tech Lead's opinion carries weight for architecture
        4. Default: Weighted average with dissent summary
        
        Args:
            opinions: List of JudicialOpinion objects (should be 3: Prosecutor, Defense, TechLead)
            criterion_id: The rubric dimension ID being evaluated
        
        Returns:
            CriterionResult with final score and synthesis details
        """
        if not opinions:
            # Return default result if no opinions
            return CriterionResult(
                dimension_id=criterion_id,
                dimension_name=self.get_criterion_name(criterion_id),
                final_score=1,
                judge_opinions=[],
                dissent_summary="No opinions provided.",
                remediation="Unable to generate remediation without judicial opinions."
            )
        
        final_score: int
        
        # Rule 1: Security override
        if self.apply_security_override(opinions):
            # Cap at 3 regardless of other scores
            max_score = max(op.score for op in opinions)
            final_score = min(3, max_score)
        
        # Rule 2: Fact supremacy - check if defense claims contradict evidence
        elif self.check_fact_supremacy(opinions):
            # Overrule defense, take weighted average of prosecutor and tech lead
            tech_scores = [op.score for op in opinions if op.judge == "TechLead"]
            pros_scores = [op.score for op in opinions if op.judge == "Prosecutor"]
            
            if tech_scores and pros_scores:
                final_score = round(
                    (sum(tech_scores) + sum(pros_scores)) / 
                    (len(tech_scores) + len(pros_scores))
                )
            elif tech_scores:
                final_score = round(sum(tech_scores) / len(tech_scores))
            elif pros_scores:
                final_score = round(sum(pros_scores) / len(pros_scores))
            else:
                final_score = round(sum(op.score for op in opinions) / len(opinions))
        
        # Rule 3: Functionality weight for architecture criteria
        elif "graph_orchestration" in criterion_id:
            tech_opinions = [op for op in opinions if op.judge == "TechLead"]
            if tech_opinions:
                final_score = tech_opinions[0].score
            else:
                final_score = round(sum(op.score for op in opinions) / len(opinions))
        
        # Default: weighted average with dissent summary
        else:
            final_score = round(sum(op.score for op in opinions) / len(opinions))
        
        # Ensure score is within valid range
        final_score = max(1, min(5, final_score))
        
        # Check variance for dissent requirement
        variance = self.calculate_score_variance(opinions)
        dissent = None
        if variance > 2:
            dissent = self.generate_dissent_summary(opinions)
        
        return CriterionResult(
            dimension_id=criterion_id,
            dimension_name=self.get_criterion_name(criterion_id),
            final_score=final_score,
            judge_opinions=opinions,
            dissent_summary=dissent,
            remediation=self.generate_remediation(opinions, final_score)
        )
    
    def generate_markdown_report(self, report: AuditReport) -> str:
        """
        Convert AuditReport to formatted Markdown.
        
        This method generates a comprehensive Markdown report with:
        - Executive summary
        - Criterion-by-criterion breakdown with judge opinions
        - Dissent summaries where applicable
        - Remediation guidance
        
        Args:
            report: The AuditReport object to convert
        
        Returns:
            Formatted Markdown string
        """
        md = f"# Audit Report: {report.repo_url}\n\n"
        md += f"## Executive Summary\n\n"
        md += f"**Overall Score: {report.overall_score:.1f}/5**\n\n"
        md += f"{report.executive_summary}\n\n"
        
        md += f"## Criterion Breakdown\n\n"
        
        for criterion in report.criteria:
            md += f"### {criterion.dimension_name}\n"
            md += f"**Final Score: {criterion.final_score}/5**\n\n"
            
            md += f"**Judge Opinions:**\n"
            for opinion in criterion.judge_opinions:
                md += f"- *{opinion.judge}* (Score: {opinion.score}): {opinion.argument}\n"
                if opinion.cited_evidence:
                    md += f"  - Evidence: {', '.join(opinion.cited_evidence)}\n"
            
            if criterion.dissent_summary:
                md += f"\n**Dissent:** {criterion.dissent_summary}\n"
            
            md += f"\n**Remediation:** {criterion.remediation}\n\n"
            md += f"---\n\n"
        
        md += f"## Remediation Plan\n\n"
        md += f"{report.remediation_plan}\n"
        
        return md


# Global instance for use in node function
chief_justice = ChiefJusticeNode()


def chief_justice_node(state: AgentState) -> Dict:
    """
    Main Chief Justice node function for LangGraph.
    
    This node:
    1. Groups judicial opinions by criterion_id
    2. Resolves each criterion using deterministic synthesis rules
    3. Calculates overall score
    4. Generates executive summary and remediation plan
    5. Creates final AuditReport
    6. Saves Markdown report to file
    
    Args:
        state: The AgentState dictionary containing opinions and other state
    
    Returns:
        Dictionary with "final_report" key containing AuditReport object
    """
    # Group opinions by criterion_id
    criteria_opinions: Dict[str, List[JudicialOpinion]] = {}
    opinions = state.get("opinions", [])
    
    for opinion in opinions:
        criterion_id = opinion.criterion_id
        if criterion_id not in criteria_opinions:
            criteria_opinions[criterion_id] = []
        criteria_opinions[criterion_id].append(opinion)
    
    # Resolve each criterion
    criteria_results = []
    for criterion_id, opinions_list in criteria_opinions.items():
        result = chief_justice.resolve_criterion(opinions_list, criterion_id)
        criteria_results.append(result)
    
    # Handle case where no opinions exist
    if not criteria_results:
        # Return default report
        report = AuditReport(
            repo_url=state.get("repo_url", "unknown"),
            executive_summary="No judicial opinions were generated. Audit incomplete.",
            overall_score=1.0,
            criteria=[],
            remediation_plan="Unable to generate remediation plan without judicial opinions."
        )
        return {"final_report": report}
    
    # Calculate overall score
    overall_score = sum(c.final_score for c in criteria_results) / len(criteria_results)
    
    # Generate executive summary
    executive_summary = f"Audit complete. Found {len(criteria_results)} criteria. "
    
    if criteria_results:
        strongest = max(criteria_results, key=lambda x: x.final_score)
        weakest = min(criteria_results, key=lambda x: x.final_score)
        executive_summary += f"Strongest: {strongest.dimension_name} ({strongest.final_score}/5). "
        executive_summary += f"Weakest: {weakest.dimension_name} ({weakest.final_score}/5)."
    
    # Generate remediation plan
    remediation_plan = "## Priority Fixes\n\n"
    # Sort by score (lowest first) and take top 3
    sorted_criteria = sorted(criteria_results, key=lambda x: x.final_score)[:3]
    
    if sorted_criteria:
        for criterion in sorted_criteria:
            remediation_plan += f"- **{criterion.dimension_name}** (Score: {criterion.final_score}/5): {criterion.remediation}\n\n"
    else:
        remediation_plan += "No specific remediation priorities identified.\n"
    
    # Add summary of all criteria
    remediation_plan += "\n## All Criteria Summary\n\n"
    for criterion in sorted(criteria_results, key=lambda x: x.final_score):
        remediation_plan += f"- **{criterion.dimension_name}**: {criterion.final_score}/5\n"
    
    # Create final report
    report = AuditReport(
        repo_url=state.get("repo_url", "unknown"),
        executive_summary=executive_summary,
        overall_score=overall_score,
        criteria=criteria_results,
        remediation_plan=remediation_plan
    )
    
    # Save to markdown file
    try:
        md_content = chief_justice.generate_markdown_report(report)
        
        # Ensure audit directory exists
        audit_dir = Path("audit")
        audit_dir.mkdir(exist_ok=True)
        
        # Generate report filename with timestamp
        timestamp = int(time.time())
        report_path = audit_dir / f"report_{timestamp}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"✓ Audit report saved to: {report_path}")
    except Exception as e:
        print(f"Warning: Failed to save markdown report: {e}")
    
    return {"final_report": report}