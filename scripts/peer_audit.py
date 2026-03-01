#!/usr/bin/env python3
"""
Run audit against a peer's Week 2 repository.

This script runs the Automaton Auditor against a peer's repository
to evaluate their implementation against the rubric criteria.

Usage:
    python scripts/peer_audit.py

Environment Variables:
    - OPENAI_API_KEY: Required for LLM-based analysis
    - LANGCHAIN_API_KEY: Optional, for LangSmith tracing
    - LANGCHAIN_TRACING_V2: Optional, set to "true" to enable tracing
    - PEER_REPO_URL: Optional, peer's repository URL
    - PEER_PDF_PATH: Optional, path to peer's PDF report
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.graph import create_full_graph, load_rubric
from src.nodes.justice import chief_justice

# Load environment variables
load_dotenv()


def main():
    """
    Run audit against a peer's repository.
    """
    print("=" * 70)
    print("Automaton Auditor - Peer Audit")
    print("=" * 70)
    print()
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set in environment")
        print("   Please set it in your .env file or environment variables")
        sys.exit(1)
    
    # Initialize graph
    print("1. Initializing audit graph...")
    try:
        graph = create_full_graph()
        print("   ✓ Graph initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize graph: {e}")
        sys.exit(1)
    
    # Load rubric
    print("\n2. Loading rubric...")
    try:
        rubric_dimensions = load_rubric()
        print(f"   ✓ Loaded {len(rubric_dimensions)} rubric dimensions")
    except Exception as e:
        print(f"   ❌ Failed to load rubric: {e}")
        sys.exit(1)
    
    # Get peer's repository URL and PDF path
    # Can be set via environment variables or command line arguments
    repo_url = os.getenv(
        "PEER_REPO_URL",
        "https://github.com/PEER_USERNAME/automaton-auditor"
    )
    pdf_path = os.getenv(
        "PEER_PDF_PATH",
        "reports/peer_report.pdf"
    )
    
    # Allow command line arguments to override
    if len(sys.argv) >= 2:
        repo_url = sys.argv[1]
    if len(sys.argv) >= 3:
        pdf_path = sys.argv[2]
    
    # Check if PDF exists
    if not os.path.exists(pdf_path):
        print(f"\n⚠ Warning: PDF file not found at {pdf_path}")
        print("   Please download the peer's PDF report first.")
        print("   The audit will continue, but PDF analysis will be limited.")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("   Aborting audit.")
            sys.exit(0)
    
    # Initialize state
    print("\n3. Setting up audit state...")
    initial_state = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "rubric_dimensions": rubric_dimensions,
        "evidences": {},
        "opinions": [],
        "final_report": None
    }
    print(f"   ✓ Repository: {repo_url}")
    print(f"   ✓ PDF Report: {pdf_path}")
    
    # Run audit
    print("\n4. Running peer audit...")
    print("   This may take several minutes depending on repository size...")
    print()
    
    try:
        final_state = graph.invoke(initial_state)
        print("\n   ✓ Peer audit completed successfully!")
    except KeyboardInterrupt:
        print("\n   ⚠ Audit interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n   ❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Extract and save report
    print("\n5. Processing results...")
    final_report = final_state.get("final_report")
    
    if final_report:
        # Generate markdown report
        try:
            md_content = chief_justice.generate_markdown_report(final_report)
            
            # Ensure output directory exists (submission requirement)
            output_dir = Path("audit") / "report_onpeer_generated"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract peer username from repo URL for filename
            peer_name = "peer"
            try:
                if "/" in repo_url:
                    parts = repo_url.rstrip("/").split("/")
                    if len(parts) >= 2:
                        # Extract username from GitHub URL
                        for i, part in enumerate(parts):
                            if part == "github.com" and i + 1 < len(parts):
                                peer_name = parts[i + 1]
                                break
            except Exception:
                pass
            
            # Save report with peer identifier and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = output_dir / f"peer_audit_{peer_name}_{timestamp}.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            print(f"   ✓ Report saved to: {report_path}")
            
            # Print summary
            print("\n" + "=" * 70)
            print("Peer Audit Summary")
            print("=" * 70)
            print(f"Repository: {repo_url}")
            print(f"Overall Score: {final_report.overall_score:.1f}/5")
            print(f"Criteria Evaluated: {len(final_report.criteria)}")
            print(f"\nExecutive Summary:")
            print(f"  {final_report.executive_summary}")
            print(f"\nFull report available at: {report_path}")
            print("=" * 70)
            
        except Exception as e:
            print(f"   ⚠ Failed to save report: {e}")
            print(f"   Report object is available in final_state['final_report']")
    else:
        print("   ⚠ No final report generated")
        print("   Check final_state for evidence and opinions")
    
    # Print evidence summary
    evidences = final_state.get("evidences", {})
    if evidences:
        print(f"\nEvidence collected for {len(evidences)} dimensions:")
        for dimension_id, evidence_list in evidences.items():
            print(f"  - {dimension_id}: {len(evidence_list)} evidence items")
    
    # Print opinions summary
    opinions = final_state.get("opinions", [])
    if opinions:
        print(f"\nJudicial opinions generated: {len(opinions)}")
        by_judge = {}
        for opinion in opinions:
            judge = opinion.judge
            by_judge[judge] = by_judge.get(judge, 0) + 1
        for judge, count in by_judge.items():
            print(f"  - {judge}: {count} opinions")
    
    print("\n" + "=" * 70)
    print("Peer audit complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
