#!/usr/bin/env python3
"""Quick test to verify imports work"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.state import Evidence, AgentState, JudicialOpinion
    print("[OK] State models imported successfully")
    
    from src.graph import load_rubric, create_full_graph
    print("[OK] Graph module imported successfully")
    
    rubric = load_rubric()
    print(f"[OK] Rubric loaded: {len(rubric)} dimensions")
    
    graph = create_full_graph()
    print("[OK] Graph created successfully")
    
    print("\n[SUCCESS] All basic imports work!")
    
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
