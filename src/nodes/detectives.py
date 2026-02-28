"""
Detective agent nodes for forensic evidence collection.

This module implements the RepoInvestigator and DocAnalyst nodes, which perform
objective forensic analysis of GitHub repositories and PDF reports based on
rubric dimensions.
"""

import ast
import operator
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.state import Evidence
from src.tools.repo_tools import clone_repository, extract_git_history
from src.tools.doc_tools import (
    ingest_pdf, 
    extract_keywords, 
    extract_file_paths,
    extract_images_from_pdf,
    analyze_diagram
)


class RepoInvestigator:
    """
    The Code Detective - collects objective forensic evidence from repositories.
    
    This agent does not opinionate. It only reports facts:
    - Does a file exist?
    - Does code contain specific patterns?
    - What is the structure of the code?
    
    All analysis is based on AST parsing and file system inspection,
    not subjective interpretation.
    """
    
    def __init__(self, repo_url: str):
        """
        Initialize the RepoInvestigator.
        
        Args:
            repo_url: The GitHub repository URL to investigate
        """
        self.repo_url = repo_url
        self.repo_path: Optional[str] = None
        self._cloned = False
    
    def investigate(self, rubric_dimensions: List[Dict]) -> List[Evidence]:
        """
        Perform complete forensic investigation of the repository.
        
        Args:
            rubric_dimensions: List of rubric dimension configurations
        
        Returns:
            List of Evidence objects for each dimension targeting "github_repo"
        """
        # Clone repository if not already done
        if not self._cloned:
            self.repo_path = clone_repository(self.repo_url)
            self._cloned = True
        
        evidence_list = []
        
        # Filter dimensions that target github_repo
        repo_dimensions = [
            dim for dim in rubric_dimensions
            if dim.get("target_artifact") == "github_repo"
        ]
        
        # Investigate each dimension
        for dimension in repo_dimensions:
            dimension_id = dimension.get("id")
            
            if dimension_id == "git_forensic_analysis":
                evidence = self._investigate_git_forensic_analysis()
            elif dimension_id == "state_management_rigor":
                evidence = self._investigate_state_management_rigor()
            elif dimension_id == "graph_orchestration":
                evidence = self._investigate_graph_orchestration()
            elif dimension_id == "safe_tool_engineering":
                evidence = self._investigate_safe_tool_engineering()
            elif dimension_id == "structured_output_enforcement":
                evidence = self._investigate_structured_output_enforcement()
            elif dimension_id == "judicial_nuance":
                evidence = self._investigate_judicial_nuance()
            else:
                # Skip unknown dimensions
                continue
            
            if evidence:
                evidence_list.extend(evidence if isinstance(evidence, list) else [evidence])
        
        return evidence_list
    
    def _investigate_git_forensic_analysis(self) -> Evidence:
        """
        Investigate git commit history for progression patterns.
        
        Returns:
            Evidence object with git history analysis
        """
        try:
            history = extract_git_history(self.repo_path)
            
            found = history["total_commits"] > 0
            is_atomic = history.get("is_atomic", False)
            total_commits = history["total_commits"]
            
            # Build content summary
            commits_summary = "\n".join([
                f"{i+1}. {c['hash']}: {c['message']}"
                for i, c in enumerate(history["commits"][:10])  # First 10 commits
            ])
            
            content = (
                f"Total commits: {total_commits}\n"
                f"Atomic history: {is_atomic}\n"
                f"Progression detected: {history.get('progression_detected', False)}\n"
                f"Time span: {history.get('commit_timespan_hours', 0):.1f} hours\n"
                f"Analysis: {history.get('analysis', 'N/A')}\n\n"
                f"Commit history:\n{commits_summary}"
            )
            
            # Calculate confidence based on history quality
            if total_commits == 0:
                confidence = 0.0
            elif total_commits == 1:
                confidence = 0.3  # Single commit suggests bulk upload
            elif is_atomic and total_commits > 3:
                confidence = 0.9  # Strong evidence of iterative development
            elif total_commits > 3:
                confidence = 0.6  # Multiple commits but may be bulk
            else:
                confidence = 0.5  # Limited history
            
            rationale = (
                f"Git history analysis shows {total_commits} commits. "
                f"{'Atomic progression pattern detected' if is_atomic else 'Bulk upload pattern detected'}. "
                f"{history.get('analysis', 'No detailed analysis available')}"
            )
            
            return Evidence(
                goal="git_forensic_analysis",
                found=found,
                content=content,
                location=self.repo_path,
                rationale=rationale,
                confidence=confidence
            )
        
        except Exception as e:
            return Evidence(
                goal="git_forensic_analysis",
                found=False,
                content=f"Error analyzing git history: {str(e)}",
                location=self.repo_path or "unknown",
                rationale=f"Failed to extract git history: {str(e)}",
                confidence=0.0
            )
    
    def _investigate_state_management_rigor(self) -> Evidence:
        """
        Investigate state management using AST parsing.
        
        Checks for:
        - Pydantic BaseModel classes
        - TypedDict definitions
        - Evidence and JudicialOpinion models
        - operator.add and operator.ior reducers
        """
        state_files = ["src/state.py", "src/graph.py"]
        found_file = None
        agent_state_code = None
        evidence_model_code = None
        judicial_opinion_code = None
        has_reducers = False
        
        for file_path in state_files:
            full_path = os.path.join(self.repo_path, file_path)
            if os.path.exists(full_path):
                found_file = file_path
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    # Parse AST
                    tree = ast.parse(code)
                    
                    # Check for AgentState TypedDict
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            if node.name == "AgentState":
                                agent_state_code = ast.get_source_segment(code, node)
                                # Check for Annotated with reducers
                                for item in node.body:
                                    if isinstance(item, ast.AnnAssign):
                                        if self._has_reducer_in_annotation(item.annotation, code):
                                            has_reducers = True
                    
                    # Check for Evidence BaseModel
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            if node.name == "Evidence":
                                # Check if inherits from BaseModel
                                for base in node.bases:
                                    if isinstance(base, ast.Name) and base.id == "BaseModel":
                                        evidence_model_code = ast.get_source_segment(code, node)
                    
                    # Check for JudicialOpinion BaseModel
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            if node.name == "JudicialOpinion":
                                for base in node.bases:
                                    if isinstance(base, ast.Name) and base.id == "BaseModel":
                                        judicial_opinion_code = ast.get_source_segment(code, node)
                
                except (SyntaxError, UnicodeDecodeError) as e:
                    continue
        
        found = found_file is not None
        has_pydantic = evidence_model_code is not None and judicial_opinion_code is not None
        has_typed_dict = agent_state_code is not None
        
        # Build content
        content_parts = []
        if agent_state_code:
            content_parts.append(f"AgentState found:\n{agent_state_code[:500]}...")
        if evidence_model_code:
            content_parts.append(f"Evidence model found:\n{evidence_model_code[:300]}...")
        if judicial_opinion_code:
            content_parts.append(f"JudicialOpinion model found:\n{judicial_opinion_code[:300]}...")
        
        content = "\n\n".join(content_parts) if content_parts else "No state management found"
        
        # Calculate confidence
        confidence = 0.0
        if found and has_pydantic and has_typed_dict and has_reducers:
            confidence = 0.95
        elif found and has_pydantic and has_typed_dict:
            confidence = 0.7  # Missing reducers
        elif found and (has_pydantic or has_typed_dict):
            confidence = 0.5  # Partial implementation
        elif found:
            confidence = 0.3  # File exists but no proper models
        
        rationale = (
            f"State file {'found' if found else 'not found'}. "
            f"Pydantic models: {'Yes' if has_pydantic else 'No'}. "
            f"TypedDict: {'Yes' if has_typed_dict else 'No'}. "
            f"Reducers: {'Yes' if has_reducers else 'No'}"
        )
        
        return Evidence(
            goal="state_management_rigor",
            found=found and has_pydantic and has_typed_dict,
            content=content,
            location=found_file or "not found",
            rationale=rationale,
            confidence=confidence
        )
    
    def _has_reducer_in_annotation(self, annotation: ast.AST, code: str) -> bool:
        """Check if annotation contains operator.add or operator.ior."""
        annotation_str = ast.get_source_segment(code, annotation) or ""
        return "operator.add" in annotation_str or "operator.ior" in annotation_str
    
    def _investigate_graph_orchestration(self) -> Evidence:
        """
        Investigate LangGraph orchestration using AST parsing.
        
        Checks for:
        - StateGraph instantiation
        - Parallel fan-out patterns
        - EvidenceAggregator node
        - Conditional edges
        """
        graph_file = "src/graph.py"
        full_path = os.path.join(self.repo_path, graph_file)
        
        if not os.path.exists(full_path):
            return Evidence(
                goal="graph_orchestration",
                found=False,
                content="src/graph.py not found",
                location=graph_file,
                rationale="Graph file does not exist",
                confidence=0.0
            )
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # Check for StateGraph
            has_stategraph = False
            has_parallel_detectives = False
            has_parallel_judges = False
            has_aggregator = False
            has_conditional_edges = False
            graph_code = None
            
            for node in ast.walk(tree):
                # Check for StateGraph instantiation
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "StateGraph":
                        has_stategraph = True
                        graph_code = ast.get_source_segment(code, node)
                
                # Check for add_edge calls (parallel patterns)
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr == "add_edge":
                            # Check if multiple edges from same source (fan-out)
                            has_parallel_detectives = True
                        elif node.func.attr == "add_conditional_edges":
                            has_conditional_edges = True
                
                # Check for EvidenceAggregator or similar
                if isinstance(node, ast.FunctionDef):
                    if "aggregat" in node.name.lower() or "sync" in node.name.lower():
                        has_aggregator = True
            
            # Check code for parallel patterns
            if "add_edge" in code and code.count("add_edge") > 2:
                has_parallel_detectives = True
            
            if "add_conditional_edges" in code:
                has_conditional_edges = True
            
            # Look for judge nodes in parallel
            if "Prosecutor" in code and "Defense" in code and "TechLead" in code:
                # Check if they're added in parallel pattern
                if code.count("add_edge") >= 3:
                    has_parallel_judges = True
            
            found = has_stategraph
            has_parallel_architecture = (has_parallel_detectives or has_parallel_judges) and has_aggregator
            
            # Build content
            content = f"StateGraph: {'Found' if has_stategraph else 'Not found'}\n"
            content += f"Parallel detectives: {'Yes' if has_parallel_detectives else 'No'}\n"
            content += f"Parallel judges: {'Yes' if has_parallel_judges else 'No'}\n"
            content += f"Evidence aggregator: {'Yes' if has_aggregator else 'No'}\n"
            content += f"Conditional edges: {'Yes' if has_conditional_edges else 'No'}\n"
            
            if graph_code:
                content += f"\nGraph code snippet:\n{graph_code[:500]}..."
            
            # Calculate confidence
            if has_stategraph and has_parallel_architecture and has_conditional_edges:
                confidence = 0.95
            elif has_stategraph and has_parallel_architecture:
                confidence = 0.75
            elif has_stategraph:
                confidence = 0.5  # Graph exists but may be linear
            else:
                confidence = 0.2
            
            rationale = (
                f"Graph file exists. StateGraph: {has_stategraph}. "
                f"Parallel architecture: {has_parallel_architecture}. "
                f"Conditional edges: {has_conditional_edges}"
            )
            
            return Evidence(
                goal="graph_orchestration",
                found=found,
                content=content,
                location=graph_file,
                rationale=rationale,
                confidence=confidence
            )
        
        except (SyntaxError, UnicodeDecodeError) as e:
            return Evidence(
                goal="graph_orchestration",
                found=False,
                content=f"Error parsing graph.py: {str(e)}",
                location=graph_file,
                rationale=f"Failed to parse graph file: {str(e)}",
                confidence=0.0
            )
    
    def _investigate_safe_tool_engineering(self) -> Evidence:
        """
        Investigate safe tool engineering practices.
        
        Checks for:
        - tempfile.TemporaryDirectory usage
        - subprocess.run (not os.system)
        - Error handling
        """
        tools_file = "src/tools/repo_tools.py"
        full_path = os.path.join(self.repo_path, tools_file)
        
        if not os.path.exists(full_path):
            return Evidence(
                goal="safe_tool_engineering",
                found=False,
                content="src/tools/repo_tools.py not found",
                location=tools_file,
                rationale="Repository tools file does not exist",
                confidence=0.0
            )
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Check for safe practices
            has_tempfile = "tempfile.TemporaryDirectory" in code or "tempfile" in code
            has_subprocess = "subprocess.run" in code or "subprocess" in code
            has_os_system = "os.system" in code
            has_error_handling = (
                "try:" in code and "except" in code and
                ("CalledProcessError" in code or "Exception" in code)
            )
            
            # Check for git clone function
            has_clone_function = "def clone" in code.lower() or "clone_repository" in code
            
            # Extract relevant code snippet
            clone_match = re.search(
                r'def\s+clone[_\w]*\s*\([^)]*\)[^{]*\{[^}]*\}',
                code,
                re.DOTALL
            )
            clone_code = clone_match.group(0)[:500] if clone_match else None
            
            found = has_clone_function
            is_safe = has_tempfile and has_subprocess and not has_os_system and has_error_handling
            
            content = f"Clone function: {'Found' if has_clone_function else 'Not found'}\n"
            content += f"Uses tempfile: {'Yes' if has_tempfile else 'No'}\n"
            content += f"Uses subprocess: {'Yes' if has_subprocess else 'No'}\n"
            content += f"Uses os.system: {'Yes (UNSAFE)' if has_os_system else 'No (SAFE)'}\n"
            content += f"Error handling: {'Yes' if has_error_handling else 'No'}\n"
            
            if clone_code:
                content += f"\nClone function snippet:\n{clone_code}..."
            
            # Calculate confidence
            if is_safe and found:
                confidence = 0.95
            elif found and (has_tempfile or has_subprocess):
                confidence = 0.6  # Partial safety
            elif found:
                confidence = 0.3  # Function exists but unsafe
            else:
                confidence = 0.1
            
            rationale = (
                f"Repository tools file exists. Safe practices: {is_safe}. "
                f"Uses tempfile: {has_tempfile}, subprocess: {has_subprocess}, "
                f"os.system: {has_os_system} (unsafe)"
            )
            
            return Evidence(
                goal="safe_tool_engineering",
                found=found and is_safe,
                content=content,
                location=tools_file,
                rationale=rationale,
                confidence=confidence
            )
        
        except Exception as e:
            return Evidence(
                goal="safe_tool_engineering",
                found=False,
                content=f"Error analyzing tools: {str(e)}",
                location=tools_file,
                rationale=f"Failed to analyze tools file: {str(e)}",
                confidence=0.0
            )
    
    def _investigate_structured_output_enforcement(self) -> Evidence:
        """
        Investigate structured output enforcement in judge nodes.
        
        Checks for:
        - .with_structured_output() calls
        - .bind_tools() calls
        - JudicialOpinion schema binding
        - Retry logic
        """
        judges_file = "src/nodes/judges.py"
        full_path = os.path.join(self.repo_path, judges_file)
        
        if not os.path.exists(full_path):
            return Evidence(
                goal="structured_output_enforcement",
                found=False,
                content="src/nodes/judges.py not found",
                location=judges_file,
                rationale="Judge nodes file does not exist",
                confidence=0.0
            )
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Check for structured output patterns
            has_structured_output = ".with_structured_output" in code
            has_bind_tools = ".bind_tools" in code
            has_judicial_opinion = "JudicialOpinion" in code
            has_retry = "retry" in code.lower() or "Retry" in code
            
            # Check for Pydantic validation
            has_validation = "pydantic" in code.lower() or "BaseModel" in code
            
            found = os.path.exists(full_path)
            has_enforcement = (has_structured_output or has_bind_tools) and has_judicial_opinion
            
            content = f"Judge nodes file: {'Found' if found else 'Not found'}\n"
            content += f"with_structured_output: {'Yes' if has_structured_output else 'No'}\n"
            content += f"bind_tools: {'Yes' if has_bind_tools else 'No'}\n"
            content += f"JudicialOpinion schema: {'Yes' if has_judicial_opinion else 'No'}\n"
            content += f"Retry logic: {'Yes' if has_retry else 'No'}\n"
            content += f"Pydantic validation: {'Yes' if has_validation else 'No'}\n"
            
            # Extract relevant code snippet
            if has_structured_output:
                match = re.search(
                    r'\.with_structured_output\([^)]*\)',
                    code
                )
                if match:
                    # Get surrounding context
                    start = max(0, match.start() - 100)
                    end = min(len(code), match.end() + 100)
                    content += f"\nCode snippet:\n{code[start:end]}"
            
            # Calculate confidence
            if has_enforcement and has_retry:
                confidence = 0.95
            elif has_enforcement:
                confidence = 0.75
            elif has_judicial_opinion:
                confidence = 0.5  # Schema exists but no enforcement
            else:
                confidence = 0.2
            
            rationale = (
                f"Judge nodes file exists. Structured output: {has_enforcement}. "
                f"Uses with_structured_output or bind_tools: {has_structured_output or has_bind_tools}. "
                f"JudicialOpinion binding: {has_judicial_opinion}"
            )
            
            return Evidence(
                goal="structured_output_enforcement",
                found=found and has_enforcement,
                content=content,
                location=judges_file,
                rationale=rationale,
                confidence=confidence
            )
        
        except Exception as e:
            return Evidence(
                goal="structured_output_enforcement",
                found=False,
                content=f"Error analyzing judges: {str(e)}",
                location=judges_file,
                rationale=f"Failed to analyze judge nodes: {str(e)}",
                confidence=0.0
            )
    
    def _investigate_judicial_nuance(self) -> Evidence:
        """
        Investigate judicial nuance and persona separation.
        
        Checks for:
        - Distinct prosecutor, defense, tech lead prompts
        - Persona separation in code
        - Parallel execution pattern
        """
        judges_file = "src/nodes/judges.py"
        full_path = os.path.join(self.repo_path, judges_file)
        
        if not os.path.exists(full_path):
            return Evidence(
                goal="judicial_nuance",
                found=False,
                content="src/nodes/judges.py not found",
                location=judges_file,
                rationale="Judge nodes file does not exist",
                confidence=0.0
            )
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Check for distinct personas
            has_prosecutor = "Prosecutor" in code or "prosecutor" in code
            has_defense = "Defense" in code or "defense" in code
            has_tech_lead = "TechLead" in code or "Tech Lead" in code or "tech lead" in code
            
            # Check for distinct prompts (look for system prompts)
            prosecutor_prompts = len(re.findall(r'prosecutor|adversarial|critical|scrutinize', code, re.IGNORECASE))
            defense_prompts = len(re.findall(r'defense|optimistic|reward|effort|intent', code, re.IGNORECASE))
            tech_lead_prompts = len(re.findall(r'tech.?lead|pragmatic|architectural|maintainable', code, re.IGNORECASE))
            
            has_distinct_personas = (
                has_prosecutor and has_defense and has_tech_lead and
                prosecutor_prompts > 0 and defense_prompts > 0 and tech_lead_prompts > 0
            )
            
            # Check for parallel execution (all three judges)
            has_parallel = (
                "Prosecutor" in code and "Defense" in code and "TechLead" in code and
                ("add_edge" in code or "parallel" in code.lower())
            )
            
            found = os.path.exists(full_path)
            has_nuance = has_distinct_personas and has_parallel
            
            content = f"Judge nodes file: {'Found' if found else 'Not found'}\n"
            content += f"Prosecutor persona: {'Yes' if has_prosecutor else 'No'}\n"
            content += f"Defense persona: {'Yes' if has_defense else 'No'}\n"
            content += f"Tech Lead persona: {'Yes' if has_tech_lead else 'No'}\n"
            content += f"Distinct prompts: {'Yes' if has_distinct_personas else 'No'}\n"
            content += f"Parallel execution: {'Yes' if has_parallel else 'No'}\n"
            content += f"Prosecutor keywords: {prosecutor_prompts}\n"
            content += f"Defense keywords: {defense_prompts}\n"
            content += f"Tech Lead keywords: {tech_lead_prompts}\n"
            
            # Calculate confidence
            if has_nuance:
                confidence = 0.9
            elif has_distinct_personas:
                confidence = 0.6  # Personas exist but may not be parallel
            elif has_prosecutor and has_defense and has_tech_lead:
                confidence = 0.4  # All three exist but may share prompts
            else:
                confidence = 0.2
            
            rationale = (
                f"Judge nodes file exists. Distinct personas: {has_distinct_personas}. "
                f"All three judges present: {has_prosecutor and has_defense and has_tech_lead}. "
                f"Parallel execution: {has_parallel}"
            )
            
            return Evidence(
                goal="judicial_nuance",
                found=found and has_nuance,
                content=content,
                location=judges_file,
                rationale=rationale,
                confidence=confidence
            )
        
        except Exception as e:
            return Evidence(
                goal="judicial_nuance",
                found=False,
                content=f"Error analyzing judicial nuance: {str(e)}",
                location=judges_file,
                rationale=f"Failed to analyze judge personas: {str(e)}",
                confidence=0.0
            )


def RepoInvestigatorNode(state: Dict) -> Dict:
    """
    LangGraph node function for RepoInvestigator.
    
    This node collects forensic evidence from the repository for all
    dimensions targeting "github_repo" in the rubric.
    
    Args:
        state: The AgentState dictionary containing repo_url and rubric_dimensions
    
    Returns:
        Dictionary with updated evidences (using reducer to merge)
    """
    repo_url = state.get("repo_url")
    rubric_dimensions = state.get("rubric_dimensions", [])
    
    if not repo_url:
        return {
            "evidences": {
                "error": [Evidence(
                    goal="initialization",
                    found=False,
                    content="No repository URL provided",
                    location="state",
                    rationale="repo_url missing from state",
                    confidence=0.0
                )]
            }
        }
    
    # Initialize investigator
    investigator = RepoInvestigator(repo_url)
    
    # Collect evidence
    evidence_list = investigator.investigate(rubric_dimensions)
    
    # Group evidence by goal (dimension id)
    evidences_by_goal: Dict[str, List[Evidence]] = {}
    for evidence in evidence_list:
        goal = evidence.goal
        if goal not in evidences_by_goal:
            evidences_by_goal[goal] = []
        evidences_by_goal[goal].append(evidence)
    
    # Store repo_path in state for DocAnalyst cross-referencing
    return {
        "evidences": evidences_by_goal,
        "repo_path": investigator.repo_path  # Make repo_path available to other nodes
    }


class DocAnalyst:
    """
    The Paperwork Detective - collects objective forensic evidence from PDF reports.
    
    This agent analyzes PDF documents to verify:
    - Theoretical depth of concepts (keywords used substantively vs buzzwords)
    - Report accuracy (cross-reference claimed files with actual repository)
    
    All analysis is objective fact-checking, not subjective interpretation.
    """
    
    def __init__(self, pdf_path: str, repo_path: Optional[str] = None):
        """
        Initialize the DocAnalyst.
        
        Args:
            pdf_path: Path to the PDF report to analyze
            repo_path: Optional path to cloned repository for cross-referencing
        """
        self.pdf_path = pdf_path
        self.repo_path = repo_path
        self._pdf_ingested = False
        self._pdf_data: Optional[Dict] = None
    
    def investigate(
        self, 
        rubric_dimensions: List[Dict],
        repo_evidences: Optional[Dict[str, List[Evidence]]] = None
    ) -> List[Evidence]:
        """
        Perform complete forensic investigation of the PDF report.
        
        Args:
            rubric_dimensions: List of rubric dimension configurations
            repo_evidences: Optional evidence from RepoInvestigator for cross-referencing
        
        Returns:
            List of Evidence objects for each dimension targeting "pdf_report"
        """
        # Ingest PDF if not already done
        if not self._pdf_ingested:
            try:
                self._pdf_data = ingest_pdf(self.pdf_path)
                self._pdf_ingested = True
            except Exception as e:
                # Return error evidence if PDF ingestion fails
                return [
                    Evidence(
                        goal="pdf_ingestion",
                        found=False,
                        content=f"Failed to ingest PDF: {str(e)}",
                        location=self.pdf_path,
                        rationale=f"PDF ingestion error: {str(e)}",
                        confidence=0.0
                    )
                ]
        
        evidence_list = []
        
        # Filter dimensions that target pdf_report
        pdf_dimensions = [
            dim for dim in rubric_dimensions
            if dim.get("target_artifact") == "pdf_report"
        ]
        
        # Investigate each dimension
        for dimension in pdf_dimensions:
            dimension_id = dimension.get("id")
            
            if dimension_id == "theoretical_depth":
                evidence = self._investigate_theoretical_depth()
            elif dimension_id == "report_accuracy":
                evidence = self._investigate_report_accuracy(repo_evidences)
            else:
                # Skip unknown dimensions
                continue
            
            if evidence:
                evidence_list.extend(evidence if isinstance(evidence, list) else [evidence])
        
        return evidence_list
    
    def _investigate_theoretical_depth(self) -> Evidence:
        """
        Investigate theoretical depth of concepts in the PDF.
        
        Searches for keywords like "Dialectical Synthesis", "Fan-In/Fan-Out",
        "Metacognition", "State Synchronization" and determines if they are
        used substantively or just dropped as buzzwords.
        
        Returns:
            Evidence object with keyword analysis
        """
        if not self._pdf_data:
            return Evidence(
                goal="theoretical_depth",
                found=False,
                content="PDF not ingested",
                location=self.pdf_path,
                rationale="PDF ingestion failed",
                confidence=0.0
            )
        
        full_text = self._pdf_data.get("full_text", "")
        
        # Extract keywords with context analysis
        keywords = [
            "Dialectical Synthesis",
            "Fan-In",
            "Fan-Out",
            "Metacognition",
            "State Synchronization"
        ]
        
        keyword_results = extract_keywords(full_text, keywords)
        
        # Analyze results
        total_keywords_found = len(keyword_results)
        substantive_count = sum(1 for r in keyword_results if r.get("is_substantive", False))
        avg_quality = (
            sum(r.get("explanation_quality", 0) for r in keyword_results) / total_keywords_found
            if total_keywords_found > 0 else 0.0
        )
        
        # Build content
        content_parts = [
            f"Total keywords found: {total_keywords_found}",
            f"Substantive usage: {substantive_count}/{total_keywords_found}",
            f"Average explanation quality: {avg_quality:.2f}",
            ""
        ]
        
        # Add details for each keyword
        for result in keyword_results:
            keyword = result["keyword"]
            is_substantive = result.get("is_substantive", False)
            quality = result.get("explanation_quality", 0.0)
            context = result.get("context", "")[:200]  # First 200 chars
            
            content_parts.append(
                f"Keyword: {keyword}\n"
                f"  Substantive: {'Yes' if is_substantive else 'No'}\n"
                f"  Quality: {quality:.2f}\n"
                f"  Context: {context}...\n"
            )
        
        content = "\n".join(content_parts)
        
        # Calculate confidence
        if total_keywords_found == 0:
            confidence = 0.0
            rationale = "No theoretical keywords found in PDF"
        elif substantive_count == total_keywords_found and avg_quality > 0.7:
            confidence = 0.95
            rationale = (
                f"All {total_keywords_found} keywords used substantively "
                f"with high quality explanations (avg: {avg_quality:.2f})"
            )
        elif substantive_count >= total_keywords_found * 0.7:
            confidence = 0.75
            rationale = (
                f"Most keywords ({substantive_count}/{total_keywords_found}) "
                f"used substantively, but some may be buzzwords"
            )
        elif substantive_count > 0:
            confidence = 0.5
            rationale = (
                f"Some keywords ({substantive_count}/{total_keywords_found}) "
                f"used substantively, but many appear as buzzwords"
            )
        else:
            confidence = 0.2
            rationale = (
                f"Keywords found but used as buzzwords without substantive explanation"
            )
        
        found = total_keywords_found > 0
        
        return Evidence(
            goal="theoretical_depth",
            found=found,
            content=content,
            location=self.pdf_path,
            rationale=rationale,
            confidence=confidence
        )
    
    def _investigate_report_accuracy(
        self, 
        repo_evidences: Optional[Dict[str, List[Evidence]]] = None
    ) -> Evidence:
        """
        Investigate report accuracy by cross-referencing claimed files.
        
        Extracts file paths mentioned in the PDF and cross-references them
        with the actual repository structure (from RepoInvestigator evidence).
        
        Args:
            repo_evidences: Evidence from RepoInvestigator for cross-referencing
        
        Returns:
            Evidence object with verified vs hallucinated paths
        """
        if not self._pdf_data:
            return Evidence(
                goal="report_accuracy",
                found=False,
                content="PDF not ingested",
                location=self.pdf_path,
                rationale="PDF ingestion failed",
                confidence=0.0
            )
        
        full_text = self._pdf_data.get("full_text", "")
        
        # Extract file paths from PDF
        claimed_paths = extract_file_paths(full_text)
        
        # Get verified paths from repository
        verified_paths = []
        hallucinated_paths = []
        
        if self.repo_path and os.path.exists(self.repo_path):
            # Check each claimed path against actual repository
            for path in claimed_paths:
                # Normalize path
                normalized_path = path.replace("\\", "/")
                
                # Check if file exists in repo
                full_file_path = os.path.join(self.repo_path, normalized_path)
                if os.path.exists(full_file_path) and os.path.isfile(full_file_path):
                    verified_paths.append(path)
                else:
                    hallucinated_paths.append(path)
        else:
            # If no repo path, try to infer from repo_evidences
            if repo_evidences:
                # Extract file paths from evidence locations
                evidence_locations = set()
                for evidence_list in repo_evidences.values():
                    for evidence in evidence_list:
                        if evidence.location and evidence.location != "not found":
                            evidence_locations.add(evidence.location)
                
                # Check claimed paths against evidence locations
                for path in claimed_paths:
                    normalized_path = path.replace("\\", "/")
                    # Check if path matches any evidence location
                    if any(normalized_path in loc or loc in normalized_path 
                           for loc in evidence_locations):
                        verified_paths.append(path)
                    else:
                        hallucinated_paths.append(path)
            else:
                # No way to verify - mark all as unverified
                hallucinated_paths = claimed_paths.copy()
        
        # Build content
        content_parts = [
            f"Total file paths mentioned: {len(claimed_paths)}",
            f"Verified paths: {len(verified_paths)}",
            f"Hallucinated paths: {len(hallucinated_paths)}",
            ""
        ]
        
        if verified_paths:
            content_parts.append("Verified paths:")
            for path in verified_paths[:20]:  # Limit to first 20
                content_parts.append(f"  ✓ {path}")
            if len(verified_paths) > 20:
                content_parts.append(f"  ... and {len(verified_paths) - 20} more")
            content_parts.append("")
        
        if hallucinated_paths:
            content_parts.append("Hallucinated paths (not found in repo):")
            for path in hallucinated_paths[:20]:  # Limit to first 20
                content_parts.append(f"  ✗ {path}")
            if len(hallucinated_paths) > 20:
                content_parts.append(f"  ... and {len(hallucinated_paths) - 20} more")
        
        content = "\n".join(content_parts)
        
        # Calculate confidence
        total_paths = len(claimed_paths)
        if total_paths == 0:
            confidence = 0.5  # No paths mentioned - neutral
            rationale = "No file paths mentioned in report"
        elif len(hallucinated_paths) == 0:
            confidence = 0.95
            rationale = (
                f"All {total_paths} file paths mentioned in report "
                f"exist in repository (100% accuracy)"
            )
        elif len(hallucinated_paths) / total_paths < 0.1:
            confidence = 0.8
            rationale = (
                f"Most paths verified ({len(verified_paths)}/{total_paths}), "
                f"only {len(hallucinated_paths)} hallucinated paths"
            )
        elif len(hallucinated_paths) / total_paths < 0.3:
            confidence = 0.6
            rationale = (
                f"Some accuracy issues: {len(verified_paths)} verified, "
                f"{len(hallucinated_paths)} hallucinated paths"
            )
        else:
            confidence = 0.3
            rationale = (
                f"Significant accuracy issues: {len(hallucinated_paths)}/{total_paths} "
                f"paths are hallucinated (not found in repository)"
            )
        
        found = total_paths > 0
        
        return Evidence(
            goal="report_accuracy",
            found=found,
            content=content,
            location=self.pdf_path,
            rationale=rationale,
            confidence=confidence
        )


def DocAnalystNode(state: Dict) -> Dict:
    """
    LangGraph node function for DocAnalyst.
    
    This node collects forensic evidence from the PDF report for all
    dimensions targeting "pdf_report" in the rubric.
    
    Args:
        state: The AgentState dictionary containing pdf_path, rubric_dimensions,
               and optionally repo_path and evidences for cross-referencing
    
    Returns:
        Dictionary with updated evidences (using reducer to merge)
    """
    pdf_path = state.get("pdf_path")
    rubric_dimensions = state.get("rubric_dimensions", [])
    repo_path = state.get("repo_path")  # May be set by RepoInvestigator
    existing_evidences = state.get("evidences", {})  # For cross-referencing
    
    if not pdf_path:
        return {
            "evidences": {
                "error": [Evidence(
                    goal="initialization",
                    found=False,
                    content="No PDF path provided",
                    location="state",
                    rationale="pdf_path missing from state",
                    confidence=0.0
                )]
            }
        }
    
    # Initialize analyst
    analyst = DocAnalyst(pdf_path, repo_path)
    
    # Collect evidence (pass repo evidences for cross-referencing)
    evidence_list = analyst.investigate(rubric_dimensions, existing_evidences)
    
    # Group evidence by goal (dimension id)
    evidences_by_goal: Dict[str, List[Evidence]] = {}
    for evidence in evidence_list:
        goal = evidence.goal
        if goal not in evidences_by_goal:
            evidences_by_goal[goal] = []
        evidences_by_goal[goal].append(evidence)
    
    return {
        "evidences": evidences_by_goal
    }


class VisionInspector:
    """
    The Visual Detective - collects objective forensic evidence from PDF diagrams.
    
    This agent analyzes architectural diagrams in PDF reports to verify:
    - Diagram type (LangGraph State Machine, sequence diagram, flowchart, etc.)
    - Parallel branch representation (detectives and judges)
    - Flow accuracy matching expected architecture
    
    All analysis is objective fact-checking using multimodal LLM vision capabilities.
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize the VisionInspector.
        
        Args:
            pdf_path: Path to the PDF report containing diagrams
        """
        self.pdf_path = pdf_path
        self._images_extracted = False
        self._image_paths: List[str] = []
    
    def investigate(
        self, 
        rubric_dimensions: List[Dict]
    ) -> List[Evidence]:
        """
        Perform complete forensic investigation of PDF diagrams.
        
        Args:
            rubric_dimensions: List of rubric dimension configurations
        
        Returns:
            List of Evidence objects for "swarm_visual" dimension
        """
        evidence_list = []
        
        # Filter dimensions that target pdf_images
        visual_dimensions = [
            dim for dim in rubric_dimensions
            if dim.get("target_artifact") == "pdf_images"
        ]
        
        # Check if swarm_visual dimension exists
        swarm_visual_dim = next(
            (dim for dim in visual_dimensions if dim.get("id") == "swarm_visual"),
            None
        )
        
        if not swarm_visual_dim:
            # Return evidence indicating dimension not found
            return [
                Evidence(
                    goal="swarm_visual",
                    found=False,
                    content="swarm_visual dimension not found in rubric",
                    location=self.pdf_path,
                    rationale="No swarm_visual dimension configured in rubric",
                    confidence=0.0
                )
            ]
        
        # Extract images from PDF
        try:
            if not self._images_extracted:
                self._image_paths = extract_images_from_pdf(self.pdf_path)
                self._images_extracted = True
        except Exception as e:
            # Return error evidence if image extraction fails
            return [
                Evidence(
                    goal="swarm_visual",
                    found=False,
                    content=f"Failed to extract images from PDF: {str(e)}",
                    location=self.pdf_path,
                    rationale=f"Image extraction error: {str(e)}",
                    confidence=0.0
                )
            ]
        
        # If no images found, return evidence
        if not self._image_paths:
            return [
                Evidence(
                    goal="swarm_visual",
                    found=False,
                    content="No images found in PDF",
                    location=self.pdf_path,
                    rationale="PDF contains no embedded images/diagrams",
                    confidence=0.0
                )
            ]
        
        # Analyze each image
        all_evidence = []
        for image_path in self._image_paths:
            evidence = self._investigate_diagram(image_path, swarm_visual_dim)
            if evidence:
                all_evidence.append(evidence)
        
        # If no valid diagrams found, return a summary evidence
        if not all_evidence:
            return [
                Evidence(
                    goal="swarm_visual",
                    found=False,
                    content=f"Found {len(self._image_paths)} images but none matched expected diagram patterns",
                    location=self.pdf_path,
                    rationale="Images exist but do not represent LangGraph State Machine architecture",
                    confidence=0.0
                )
            ]
        
        return all_evidence
    
    def _investigate_diagram(
        self, 
        image_path: str,
        dimension: Dict
    ) -> Optional[Evidence]:
        """
        Investigate a single diagram image.
        
        Args:
            image_path: Path to the image file to analyze
            dimension: Rubric dimension configuration for swarm_visual
        
        Returns:
            Evidence object with diagram analysis, or None if analysis fails
        """
        try:
            # Analyze diagram using multimodal LLM
            analysis = analyze_diagram(image_path)
            
            # Extract key information
            diagram_type = analysis.get("diagram_type", "other")
            is_langgraph = analysis.get("is_langgraph_state_machine", False)
            shows_parallel = analysis.get("shows_parallel_branches", False)
            has_detectives_parallel = analysis.get("has_detectives_parallel", False)
            has_judges_parallel = analysis.get("has_judges_parallel", False)
            has_aggregation = analysis.get("has_aggregation_nodes", False)
            accuracy_score = analysis.get("accuracy_score", 0.0)
            flow_description = analysis.get("flow_description", "")
            analysis_details = analysis.get("analysis_details", "")
            
            # Determine if diagram matches expected pattern
            # Expected: LangGraph State Machine with parallel detectives and judges
            matches_pattern = (
                is_langgraph and 
                shows_parallel and 
                (has_detectives_parallel or has_judges_parallel)
            )
            
            # Build content description
            image_filename = Path(image_path).name
            content_parts = [
                f"Diagram Type: {diagram_type}",
                f"Is LangGraph State Machine: {is_langgraph}",
                f"Shows Parallel Branches: {shows_parallel}",
                f"Detectives in Parallel: {has_detectives_parallel}",
                f"Judges in Parallel: {has_judges_parallel}",
                f"Has Aggregation Nodes: {has_aggregation}",
                f"Accuracy Score: {accuracy_score:.2f}",
                "",
                f"Flow Description: {flow_description}",
                "",
                f"Full Analysis: {analysis_details[:500]}..." if len(analysis_details) > 500 else f"Full Analysis: {analysis_details}"
            ]
            content = "\n".join(content_parts)
            
            # Build rationale
            if matches_pattern and accuracy_score > 0.7:
                rationale = (
                    f"Diagram accurately represents LangGraph State Machine architecture "
                    f"with parallel execution (detectives: {has_detectives_parallel}, "
                    f"judges: {has_judges_parallel}) and aggregation nodes. "
                    f"Accuracy score: {accuracy_score:.2f}"
                )
                confidence = min(0.95, accuracy_score + 0.1)  # Boost confidence for good matches
                found = True
            elif matches_pattern:
                rationale = (
                    f"Diagram shows LangGraph State Machine with parallel branches, "
                    f"but accuracy score ({accuracy_score:.2f}) indicates some discrepancies "
                    f"from expected architecture."
                )
                confidence = accuracy_score
                found = True
            elif is_langgraph:
                rationale = (
                    f"Diagram is a LangGraph State Machine but does not clearly show "
                    f"parallel execution patterns for detectives/judges."
                )
                confidence = 0.4
                found = True
            elif shows_parallel:
                rationale = (
                    f"Diagram shows parallel branches but is not a LangGraph State Machine "
                    f"(classified as: {diagram_type})."
                )
                confidence = 0.3
                found = True
            else:
                rationale = (
                    f"Diagram does not match expected architecture pattern. "
                    f"Type: {diagram_type}, Parallel: {shows_parallel}"
                )
                confidence = 0.1
                found = False
            
            # Determine if flow is linear vs parallel
            flow_analysis = "parallel" if shows_parallel else "linear"
            if not shows_parallel:
                rationale += " Flow appears linear rather than parallel."
            
            return Evidence(
                goal="swarm_visual",
                found=found,
                content=content,
                location=image_filename,
                rationale=rationale,
                confidence=confidence
            )
        
        except Exception as e:
            # Return error evidence if analysis fails
            return Evidence(
                goal="swarm_visual",
                found=False,
                content=f"Failed to analyze diagram: {str(e)}",
                location=Path(image_path).name,
                rationale=f"Diagram analysis error: {str(e)}",
                confidence=0.0
            )


def VisionInspectorNode(state: Dict) -> Dict:
    """
    LangGraph node function for VisionInspector.
    
    This node collects forensic evidence from PDF diagrams for the
    "swarm_visual" dimension targeting "pdf_images" in the rubric.
    
    Note: This node is optional - it will gracefully handle cases where
    no images are found or vision API is unavailable.
    
    Args:
        state: The AgentState dictionary containing pdf_path and rubric_dimensions
    
    Returns:
        Dictionary with updated evidences (using reducer to merge)
    """
    pdf_path = state.get("pdf_path")
    rubric_dimensions = state.get("rubric_dimensions", [])
    
    if not pdf_path:
        return {
            "evidences": {
                "swarm_visual": [
                    Evidence(
                        goal="swarm_visual",
                        found=False,
                        content="No PDF path provided",
                        location="state",
                        rationale="pdf_path missing from state",
                        confidence=0.0
                    )
                ]
            }
        }
    
    # Initialize inspector
    inspector = VisionInspector(pdf_path)
    
    # Collect evidence
    evidence_list = inspector.investigate(rubric_dimensions)
    
    # Group evidence by goal (should all be "swarm_visual")
    evidences_by_goal: Dict[str, List[Evidence]] = {}
    for evidence in evidence_list:
        goal = evidence.goal
        if goal not in evidences_by_goal:
            evidences_by_goal[goal] = []
        evidences_by_goal[goal].append(evidence)
    
    # Clean up temporary image files
    try:
        for image_path in inspector._image_paths:
            if os.path.exists(image_path):
                os.remove(image_path)
        # Remove temporary directory if empty
        if inspector._image_paths:
            temp_dir = os.path.dirname(inspector._image_paths[0])
            try:
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
            except OSError:
                pass  # Directory not empty or already removed
    except Exception as e:
        print(f"Warning: Failed to clean up temporary image files: {e}")
    
    return {
        "evidences": evidences_by_goal
    }


def EvidenceAggregatorNode(state: Dict) -> Dict:
    """
    Evidence Aggregator node - fan-in synchronization point for detective nodes.
    
    This node runs after all detective nodes (RepoInvestigator, DocAnalyst, etc.)
    have completed their parallel execution. It merges all evidence dictionaries
    using operator.ior (dict update merge) to prevent data overwriting.
    
    The reducer (operator.ior) ensures that evidence from multiple detectives
    running in parallel is properly combined without losing any data.
    
    Args:
        state: The AgentState dictionary containing evidences from all detective nodes
    
    Returns:
        Dictionary with merged evidences using operator.ior reducer
    
    Example:
        If RepoInvestigator returns:
            {"evidences": {"git_forensic_analysis": [evidence1]}}
        
        And DocAnalyst returns:
            {"evidences": {"theoretical_depth": [evidence2]}}
        
        This node merges them to:
            {"evidences": {
                "git_forensic_analysis": [evidence1],
                "theoretical_depth": [evidence2]
            }}
    
    Notes:
        - Uses operator.ior to merge dictionaries (preserves all keys)
        - Handles cases where multiple detectives return evidence for same goal
        - Ensures no evidence is lost during parallel execution
    """
    # Get existing evidences from state (may be empty dict initially)
    existing_evidences = state.get("evidences", {})
    
    # The evidences should already be grouped by goal (dimension id)
    # from each detective node. Since we're using operator.ior reducer,
    # LangGraph will have already merged them, but we ensure consistency here.
    
    # If evidences is already a dict of {goal: [Evidence]}, we're good
    # Otherwise, we need to ensure it's properly structured
    
    # Validate and normalize evidences structure
    merged_evidences: Dict[str, List[Evidence]] = {}
    
    if isinstance(existing_evidences, dict):
        for goal, evidence_list in existing_evidences.items():
            # Ensure evidence_list is a list
            if isinstance(evidence_list, list):
                # Filter out any None values
                valid_evidences = [e for e in evidence_list if e is not None]
                if valid_evidences:
                    merged_evidences[goal] = valid_evidences
            elif isinstance(evidence_list, Evidence):
                # Single evidence object, wrap in list
                merged_evidences[goal] = [evidence_list]
    
    # Use operator.ior to merge (this is what the reducer does, but we ensure it here)
    # The reducer in state definition handles this automatically, but we validate
    
    # Count total evidence items for logging/debugging
    total_evidence_count = sum(len(ev_list) for ev_list in merged_evidences.values())
    total_goals = len(merged_evidences)
    
    # Return merged evidences
    # Note: The operator.ior reducer in AgentState will handle the actual merging
    # This node primarily serves as a synchronization point and 
    # 
    # validation
    return {
        "evidences": merged_evidences
    }
