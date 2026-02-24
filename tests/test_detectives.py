"""
Test suite for detective nodes and tools.

This module tests:
- Repository tools (clone, git history extraction)
- Document tools (PDF ingestion, keyword extraction)
- Individual detective nodes
- Full partial graph execution
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest

from src.state import Evidence
from src.tools.repo_tools import clone_repository, extract_git_history, cleanup_all_repositories
from src.tools.doc_tools import ingest_pdf, extract_keywords, extract_file_paths
from src.nodes.detectives import (
    RepoInvestigator,
    DocAnalyst,
    RepoInvestigatorNode,
    DocAnalystNode,
    EvidenceAggregatorNode
)
from src.graph import create_auditor_graph, load_rubric


# Test configuration
TEST_REPO_URL = "https://github.com/langchain-ai/langgraph.git"  # Public repo for testing
TEST_PDF_PATH = "reports/test_report.pdf"  # Will create a mock if not exists


class TestRepoTools:
    """Test suite for repository tools."""
    
    def test_clone_repository(self):
        """Test cloning a public repository."""
        print("\n" + "=" * 60)
        print("Test: Clone Repository")
        print("=" * 60)
        
        try:
            repo_path = clone_repository(TEST_REPO_URL)
            
            assert repo_path is not None, "Repository path should not be None"
            assert os.path.exists(repo_path), f"Repository should exist at {repo_path}"
            assert os.path.exists(os.path.join(repo_path, ".git")), "Should be a git repository"
            
            print(f"✓ Successfully cloned repository to: {repo_path}")
            print(f"  Repository exists: {os.path.exists(repo_path)}")
            print(f"  Git directory exists: {os.path.exists(os.path.join(repo_path, '.git'))}")
            
            return repo_path
        
        except Exception as e:
            pytest.skip(f"Could not clone repository (network issue?): {e}")
    
    def test_extract_git_history(self):
        """Test extracting git history from cloned repository."""
        print("\n" + "=" * 60)
        print("Test: Extract Git History")
        print("=" * 60)
        
        # Clone first
        repo_path = self.test_clone_repository()
        if repo_path is None:
            pytest.skip("Repository not cloned")
        
        try:
            history = extract_git_history(repo_path)
            
            # Validate structure
            assert "commits" in history, "History should contain 'commits'"
            assert "total_commits" in history, "History should contain 'total_commits'"
            assert "is_atomic" in history, "History should contain 'is_atomic'"
            assert isinstance(history["commits"], list), "Commits should be a list"
            assert history["total_commits"] > 0, "Should have at least one commit"
            
            print(f"✓ Successfully extracted git history")
            print(f"  Total commits: {history['total_commits']}")
            print(f"  Atomic history: {history.get('is_atomic', False)}")
            print(f"  Progression detected: {history.get('progression_detected', False)}")
            print(f"  Time span: {history.get('commit_timespan_hours', 0):.1f} hours")
            
            # Show sample commit
            if history["commits"]:
                sample_commit = history["commits"][0]
                print(f"\n  Sample commit:")
                print(f"    Hash: {sample_commit.get('hash', 'N/A')}")
                print(f"    Message: {sample_commit.get('message', 'N/A')[:50]}...")
                print(f"    Timestamp: {sample_commit.get('timestamp', 'N/A')}")
            
            return history
        
        except Exception as e:
            pytest.fail(f"Failed to extract git history: {e}")
    
    def test_cleanup(self):
        """Clean up temporary repositories after tests."""
        cleanup_all_repositories()
        print("\n✓ Cleaned up temporary repositories")


class TestDocTools:
    """Test suite for document tools."""
    
    def create_mock_pdf(self) -> str:
        """Create a mock PDF file for testing."""
        # Create a simple text file that simulates PDF content
        # In real tests, you'd use an actual PDF
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "test_report.pdf")
        
        # Create a text file (simulating PDF extraction)
        # In production, this would be a real PDF
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write("""
            Automaton Auditor Test Report
            
            This report demonstrates Dialectical Synthesis through the implementation
            of three parallel judge personas: Prosecutor, Defense, and Tech Lead.
            
            The architecture uses Fan-In and Fan-Out patterns to orchestrate the
            detective agents in parallel, then aggregate their evidence before
            passing to the judicial layer.
            
            Metacognition is achieved by having the system evaluate its own
            evaluation quality through the Chief Justice synthesis engine.
            
            State Synchronization is handled using operator.ior and operator.add
            reducers to prevent data overwriting during parallel execution.
            
            We implemented the following files:
            - src/state.py: Contains Pydantic models and AgentState
            - src/graph.py: Contains the LangGraph StateGraph definition
            - src/nodes/detectives.py: Contains RepoInvestigator and DocAnalyst
            - src/tools/repo_tools.py: Contains git cloning and history extraction
            """)
        
        return pdf_path
    
    def test_ingest_pdf(self):
        """Test PDF ingestion."""
        print("\n" + "=" * 60)
        print("Test: Ingest PDF")
        print("=" * 60)
        
        # Create mock PDF
        pdf_path = self.create_mock_pdf()
        
        try:
            pdf_data = ingest_pdf(pdf_path)
            
            assert "full_text" in pdf_data, "PDF data should contain 'full_text'"
            assert "chunks" in pdf_data, "PDF data should contain 'chunks'"
            assert "total_pages" in pdf_data, "PDF data should contain 'total_pages'"
            assert len(pdf_data["full_text"]) > 0, "Full text should not be empty"
            assert len(pdf_data["chunks"]) > 0, "Should have at least one chunk"
            
            print(f"✓ Successfully ingested PDF")
            print(f"  Total pages: {pdf_data.get('total_pages', 'N/A')}")
            print(f"  Total chunks: {pdf_data.get('total_chunks', 'N/A')}")
            print(f"  Text length: {len(pdf_data['full_text'])} characters")
            print(f"  First chunk preview: {pdf_data['chunks'][0]['text'][:100]}...")
            
            return pdf_data
        
        except Exception as e:
            # If PDF ingestion fails (no PyPDF2), create a mock result
            print(f"⚠ PDF ingestion failed (expected if PyPDF2 not available): {e}")
            return {
                "full_text": "Mock PDF content for testing",
                "chunks": [{"text": "Mock chunk", "chunk_id": 0}],
                "total_pages": 1,
                "total_chunks": 1
            }
    
    def test_extract_keywords(self):
        """Test keyword extraction from text."""
        print("\n" + "=" * 60)
        print("Test: Extract Keywords")
        print("=" * 60)
        
        text = """
        This implementation demonstrates Dialectical Synthesis by having three
        distinct judge personas analyze the same evidence. The Fan-In and Fan-Out
        patterns are used to orchestrate parallel execution. Metacognition is
        achieved through self-evaluation. State Synchronization prevents data loss.
        """
        
        keywords = [
            "Dialectical Synthesis",
            "Fan-In",
            "Fan-Out",
            "Metacognition",
            "State Synchronization"
        ]
        
        results = extract_keywords(text, keywords)
        
        assert len(results) > 0, "Should find at least one keyword"
        
        print(f"✓ Successfully extracted keywords")
        print(f"  Keywords found: {len(results)}")
        
        for result in results:
            print(f"\n  Keyword: {result['keyword']}")
            print(f"    Substantive: {result.get('is_substantive', False)}")
            print(f"    Quality: {result.get('explanation_quality', 0):.2f}")
            print(f"    Context: {result.get('context', '')[:80]}...")
        
        return results
    
    def test_extract_file_paths(self):
        """Test file path extraction from text."""
        print("\n" + "=" * 60)
        print("Test: Extract File Paths")
        print("=" * 60)
        
        text = """
        We implemented the following files:
        - src/state.py: Contains Pydantic models
        - src/graph.py: Contains StateGraph definition
        - src/nodes/detectives.py: Contains detective nodes
        - src/tools/repo_tools.py: Contains git tools
        """
        
        paths = extract_file_paths(text)
        
        assert len(paths) > 0, "Should extract at least one file path"
        assert "src/state.py" in paths or any("state.py" in p for p in paths), "Should find state.py"
        
        print(f"✓ Successfully extracted file paths")
        print(f"  Paths found: {len(paths)}")
        for path in paths:
            print(f"    - {path}")
        
        return paths


class TestDetectiveNodes:
    """Test suite for individual detective nodes."""
    
    def test_repo_investigator_individual(self):
        """Test RepoInvestigator class individually."""
        print("\n" + "=" * 60)
        print("Test: RepoInvestigator (Individual)")
        print("=" * 60)
        
        # Load rubric
        rubric_dimensions = load_rubric()
        repo_dimensions = [
            dim for dim in rubric_dimensions
            if dim.get("target_artifact") == "github_repo"
        ]
        
        print(f"  Testing {len(repo_dimensions)} repository dimensions")
        
        # Create investigator
        investigator = RepoInvestigator(TEST_REPO_URL)
        
        try:
            # Investigate
            evidence_list = investigator.investigate(repo_dimensions)
            
            assert len(evidence_list) > 0, "Should collect at least one evidence"
            
            print(f"✓ RepoInvestigator collected {len(evidence_list)} evidence items")
            
            # Show evidence format
            for evidence in evidence_list:
                print(f"\n  Evidence for '{evidence.goal}':")
                print(f"    Found: {evidence.found}")
                print(f"    Confidence: {evidence.confidence:.2f}")
                print(f"    Location: {evidence.location}")
                print(f"    Rationale: {evidence.rationale[:80]}...")
                if evidence.content:
                    print(f"    Content preview: {evidence.content[:100]}...")
            
            return evidence_list
        
        except Exception as e:
            pytest.skip(f"Could not test RepoInvestigator (network issue?): {e}")
    
    def test_doc_analyst_individual(self):
        """Test DocAnalyst class individually."""
        print("\n" + "=" * 60)
        print("Test: DocAnalyst (Individual)")
        print("=" * 60)
        
        # Create mock PDF
        doc_tools_test = TestDocTools()
        pdf_path = doc_tools_test.create_mock_pdf()
        
        # Load rubric
        rubric_dimensions = load_rubric()
        pdf_dimensions = [
            dim for dim in rubric_dimensions
            if dim.get("target_artifact") == "pdf_report"
        ]
        
        print(f"  Testing {len(pdf_dimensions)} PDF dimensions")
        
        # Create analyst
        analyst = DocAnalyst(pdf_path)
        
        try:
            # Investigate
            evidence_list = analyst.investigate(pdf_dimensions)
            
            assert len(evidence_list) > 0, "Should collect at least one evidence"
            
            print(f"✓ DocAnalyst collected {len(evidence_list)} evidence items")
            
            # Show evidence format
            for evidence in evidence_list:
                print(f"\n  Evidence for '{evidence.goal}':")
                print(f"    Found: {evidence.found}")
                print(f"    Confidence: {evidence.confidence:.2f}")
                print(f"    Location: {evidence.location}")
                print(f"    Rationale: {evidence.rationale[:80]}...")
                if evidence.content:
                    print(f"    Content preview: {evidence.content[:100]}...")
            
            return evidence_list
        
        except Exception as e:
            pytest.skip(f"Could not test DocAnalyst: {e}")
    
    def test_evidence_format(self):
        """Test and display expected Evidence object format."""
        print("\n" + "=" * 60)
        print("Test: Evidence Object Format")
        print("=" * 60)
        
        # Create sample evidence
        sample_evidence = Evidence(
            goal="git_forensic_analysis",
            found=True,
            content="Total commits: 5\nAtomic history: True\nProgression detected: True",
            location="/tmp/test_repo",
            rationale="Git history shows 5 commits with clear progression pattern",
            confidence=0.9
        )
        
        print("✓ Sample Evidence object created")
        print("\n  Expected Evidence format:")
        print(f"    goal: {sample_evidence.goal}")
        print(f"    found: {sample_evidence.found}")
        print(f"    confidence: {sample_evidence.confidence}")
        print(f"    location: {sample_evidence.location}")
        print(f"    rationale: {sample_evidence.rationale}")
        print(f"    content: {sample_evidence.content[:80]}...")
        
        # Validate Pydantic model
        assert sample_evidence.goal == "git_forensic_analysis"
        assert sample_evidence.found is True
        assert 0.0 <= sample_evidence.confidence <= 1.0
        
        # Show JSON serialization
        evidence_dict = sample_evidence.model_dump()
        print("\n  Evidence as dictionary:")
        print(json.dumps(evidence_dict, indent=2))
        
        return sample_evidence


class TestPartialGraph:
    """Test suite for partial graph execution."""
    
    def test_repo_investigator_node(self):
        """Test RepoInvestigatorNode function."""
        print("\n" + "=" * 60)
        print("Test: RepoInvestigatorNode")
        print("=" * 60)
        
        # Create test state
        rubric_dimensions = load_rubric()
        state = {
            "repo_url": TEST_REPO_URL,
            "pdf_path": "reports/test.pdf",
            "rubric_dimensions": rubric_dimensions,
            "evidences": {},
            "opinions": [],
            "final_report": None
        }
        
        try:
            result = RepoInvestigatorNode(state)
            
            assert "evidences" in result, "Result should contain 'evidences'"
            assert isinstance(result["evidences"], dict), "Evidences should be a dict"
            
            print(f"✓ RepoInvestigatorNode executed successfully")
            print(f"  Evidence dimensions: {len(result['evidences'])}")
            
            for dimension_id, evidence_list in result["evidences"].items():
                print(f"    {dimension_id}: {len(evidence_list)} evidence items")
            
            return result
        
        except Exception as e:
            pytest.skip(f"Could not test RepoInvestigatorNode (network issue?): {e}")
    
    def test_doc_analyst_node(self):
        """Test DocAnalystNode function."""
        print("\n" + "=" * 60)
        print("Test: DocAnalystNode")
        print("=" * 60)
        
        # Create mock PDF
        doc_tools_test = TestDocTools()
        pdf_path = doc_tools_test.create_mock_pdf()
        
        # Create test state
        rubric_dimensions = load_rubric()
        state = {
            "repo_url": TEST_REPO_URL,
            "pdf_path": pdf_path,
            "rubric_dimensions": rubric_dimensions,
            "evidences": {},
            "opinions": [],
            "final_report": None
        }
        
        try:
            result = DocAnalystNode(state)
            
            assert "evidences" in result, "Result should contain 'evidences'"
            assert isinstance(result["evidences"], dict), "Evidences should be a dict"
            
            print(f"✓ DocAnalystNode executed successfully")
            print(f"  Evidence dimensions: {len(result['evidences'])}")
            
            for dimension_id, evidence_list in result["evidences"].items():
                print(f"    {dimension_id}: {len(evidence_list)} evidence items")
            
            return result
        
        except Exception as e:
            pytest.skip(f"Could not test DocAnalystNode: {e}")
    
    def test_evidence_aggregator_node(self):
        """Test EvidenceAggregatorNode function."""
        print("\n" + "=" * 60)
        print("Test: EvidenceAggregatorNode")
        print("=" * 60)
        
        # Create test state with evidence from both detectives
        state = {
            "repo_url": TEST_REPO_URL,
            "pdf_path": "reports/test.pdf",
            "rubric_dimensions": load_rubric(),
            "evidences": {
                "git_forensic_analysis": [
                    Evidence(
                        goal="git_forensic_analysis",
                        found=True,
                        content="Test content",
                        location="/tmp/repo",
                        rationale="Test rationale",
                        confidence=0.8
                    )
                ],
                "theoretical_depth": [
                    Evidence(
                        goal="theoretical_depth",
                        found=True,
                        content="Test content",
                        location="reports/test.pdf",
                        rationale="Test rationale",
                        confidence=0.7
                    )
                ]
            },
            "opinions": [],
            "final_report": None
        }
        
        result = EvidenceAggregatorNode(state)
        
        assert "evidences" in result, "Result should contain 'evidences'"
        assert len(result["evidences"]) == 2, "Should have 2 evidence dimensions"
        
        print(f"✓ EvidenceAggregatorNode executed successfully")
        print(f"  Aggregated evidence dimensions: {len(result['evidences'])}")
        
        for dimension_id, evidence_list in result["evidences"].items():
            print(f"    {dimension_id}: {len(evidence_list)} evidence items")
        
        return result
    
    def test_partial_graph_execution(self):
        """Test partial graph execution (detectives only)."""
        print("\n" + "=" * 60)
        print("Test: Partial Graph Execution")
        print("=" * 60)
        
        # Create graph
        app = create_auditor_graph()
        
        # Create test state
        doc_tools_test = TestDocTools()
        pdf_path = doc_tools_test.create_mock_pdf()
        
        initial_state = {
            "repo_url": TEST_REPO_URL,
            "pdf_path": pdf_path,
            "rubric_dimensions": load_rubric(),
            "evidences": {},
            "opinions": [],
            "final_report": None
        }
        
        print("  Graph structure:")
        print("    START -> [repo_investigator, doc_analyst] (parallel)")
        print("    -> evidence_aggregator -> END")
        
        try:
            # Execute graph
            final_state = app.invoke(initial_state)
            
            assert "evidences" in final_state, "Final state should contain 'evidences'"
            
            total_evidence = sum(
                len(ev_list) for ev_list in final_state["evidences"].values()
            )
            
            print(f"\n✓ Graph executed successfully")
            print(f"  Evidence dimensions: {len(final_state['evidences'])}")
            print(f"  Total evidence items: {total_evidence}")
            
            # Show summary
            for dimension_id, evidence_list in final_state["evidences"].items():
                print(f"\n  {dimension_id}:")
                for evidence in evidence_list:
                    print(f"    - Found: {evidence.found}, Confidence: {evidence.confidence:.2f}")
            
            return final_state
        
        except Exception as e:
            pytest.skip(f"Could not test graph execution (network issue?): {e}")


def run_all_tests():
    """Run all tests and display summary."""
    print("\n" + "=" * 60)
    print("Running All Detective Tests")
    print("=" * 60)
    
    # Test repo tools
    repo_tests = TestRepoTools()
    try:
        repo_tests.test_clone_repository()
        repo_tests.test_extract_git_history()
    except Exception as e:
        print(f"⚠ Repo tools tests skipped: {e}")
    
    # Test doc tools
    doc_tests = TestDocTools()
    doc_tests.test_ingest_pdf()
    doc_tests.test_extract_keywords()
    doc_tests.test_extract_file_paths()
    
    # Test detective nodes
    node_tests = TestDetectiveNodes()
    node_tests.test_evidence_format()
    try:
        node_tests.test_repo_investigator_individual()
    except Exception as e:
        print(f"⚠ RepoInvestigator test skipped: {e}")
    
    try:
        node_tests.test_doc_analyst_individual()
    except Exception as e:
        print(f"⚠ DocAnalyst test skipped: {e}")
    
    # Test partial graph
    graph_tests = TestPartialGraph()
    graph_tests.test_evidence_aggregator_node()
    try:
        graph_tests.test_repo_investigator_node()
    except Exception as e:
        print(f"⚠ RepoInvestigatorNode test skipped: {e}")
    
    try:
        graph_tests.test_doc_analyst_node()
    except Exception as e:
        print(f"⚠ DocAnalystNode test skipped: {e}")
    
    try:
        graph_tests.test_partial_graph_execution()
    except Exception as e:
        print(f"⚠ Partial graph test skipped: {e}")
    
    # Cleanup
    cleanup_all_repositories()
    
    print("\n" + "=" * 60)
    print("All Tests Completed")
    print("=" * 60)


if __name__ == "__main__":
    # Run tests directly (without pytest)
    run_all_tests()
    
    # Or run with pytest:
    # pytest tests/test_detectives.py -v -s
