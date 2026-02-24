# Automaton Auditor

A hierarchical swarm of "Detective" agents collects evidence, passes it to "Judge" agents with distinct personas (Prosecutor, Defense, Tech Lead), and a "Chief Justice" synthesizes a final verdict.

## Overview

The Automaton Auditor is a production-grade automated code auditing system built with LangGraph. It implements a "Digital Courtroom" architecture where:

- **Detective Layer**: Forensic agents (RepoInvestigator, DocAnalyst) collect objective evidence from GitHub repositories and PDF reports
- **Judicial Layer**: Three distinct judge personas (Prosecutor, Defense, Tech Lead) analyze evidence independently
- **Supreme Court**: Chief Justice synthesizes conflicting opinions into a final, actionable audit report

This system is designed for automated quality assurance at scale, capable of auditing code repositories based on strict forensic rubrics.

## Prerequisites

Before installing, ensure you have:

- **Python 3.10+** (Python 3.14 recommended)
- **uv** package manager ([Installation guide](https://github.com/astral-sh/uv))
- **Git** (for repository cloning)
- **API Keys**:
  - **OpenAI API Key** (or Anthropic API Key) - [Get from OpenAI](https://platform.openai.com/api-keys) or [Anthropic](https://console.anthropic.com/)
  - **LangSmith API Key** (optional, for tracing) - [Get from LangSmith](https://smith.langchain.com/)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/automaton-auditor.git
cd automaton-auditor
```

### 2. Install Dependencies with uv

```bash
# Install uv if you haven't already
# Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates virtual environment and installs packages)
uv sync
```

This will:
- Create a virtual environment (`.venv`)
- Install all dependencies from `pyproject.toml`
- Generate `uv.lock` with pinned versions

### 3. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# On Windows: notepad .env
# On macOS/Linux: nano .env
```

Required environment variables in `.env`:

```env
# LangSmith Tracing (optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=automaton-auditor

# LLM Provider (choose one)
OPENAI_API_KEY=your_openai_api_key_here
# OR
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 4. Verify Installation

```bash
# Activate virtual environment
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Run basic test
python -m pytest tests/test_detectives.py -v

# Or test graph structure
python src/graph.py
```

## Usage

### Running an Audit

To audit a GitHub repository and PDF report:

```python
from src.graph import run_audit

# Run audit
final_state = run_audit(
    repo_url="https://github.com/user/repo.git",
    pdf_path="reports/architectural_report.pdf"
)

# Access results
evidences = final_state.get("evidences", {})
for dimension_id, evidence_list in evidences.items():
    print(f"{dimension_id}: {len(evidence_list)} evidence items")
    for evidence in evidence_list:
        print(f"  - Found: {evidence.found}, Confidence: {evidence.confidence:.2f}")
```

### Command Line Example

```bash
# Activate virtual environment first
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Run from Python
python -c "
from src.graph import run_audit
result = run_audit(
    repo_url='https://github.com/langchain-ai/langgraph.git',
    pdf_path='reports/test_report.pdf'
)
print(f'Collected evidence for {len(result[\"evidences\"])} dimensions')
"
```

### Running Tests

```bash
# Run all detective tests
pytest tests/test_detectives.py -v -s

# Run specific test class
pytest tests/test_detectives.py::TestRepoTools -v

# Run with coverage
pytest tests/test_detectives.py --cov=src --cov-report=html
```

## Project Structure

```
automaton-auditor/
├── src/
│   ├── __init__.py
│   ├── state.py              # Pydantic models (Evidence, JudicialOpinion, AgentState)
│   ├── graph.py              # LangGraph StateGraph definition
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── detectives.py     # RepoInvestigator, DocAnalyst, EvidenceAggregator
│   │   └── judges.py          # Prosecutor, Defense, TechLead (to be implemented)
│   │   └── justice.py         # ChiefJustice (to be implemented)
│   └── tools/
│       ├── __init__.py
│       ├── repo_tools.py      # Git cloning, history extraction
│       └── doc_tools.py       # PDF ingestion, keyword extraction
├── tests/
│   ├── __init__.py
│   └── test_detectives.py     # Test suite for detectives
├── reports/                   # PDF reports to analyze
├── audit/                     # Generated audit reports
├── rubric.json                # Evaluation rubric (machine-readable)
├── pyproject.toml             # Project metadata and dependencies
├── uv.lock                    # Locked dependency versions
├── .env.example               # Environment variables template
├── .env                       # Your actual environment variables (not in git)
└── README.md                  # This file
```

### Key Components

- **`src/state.py`**: Defines all Pydantic models and TypedDict state structure with reducers (`operator.ior`, `operator.add`)
- **`src/graph.py`**: Creates and compiles the LangGraph StateGraph with parallel execution
- **`src/nodes/detectives.py`**: Implements forensic evidence collection agents
- **`src/tools/repo_tools.py`**: Safe, sandboxed git operations
- **`src/tools/doc_tools.py`**: PDF parsing and text analysis
- **`rubric.json`**: Machine-readable rubric with forensic instructions and synthesis rules

## Interim Deliverables Checklist

### Phase 1: Infrastructure ✅
- [x] State definitions with Pydantic models and TypedDict
- [x] State reducers (operator.add, operator.ior) to prevent data overwriting
- [x] Environment setup with .env.example
- [x] LangSmith tracing integration
- [x] Project structure with proper package organization

### Phase 2: Detective Layer ✅
- [x] RepoInvestigator: Git forensic analysis
- [x] RepoInvestigator: State management rigor (AST parsing)
- [x] RepoInvestigator: Graph orchestration analysis
- [x] RepoInvestigator: Safe tool engineering verification
- [x] DocAnalyst: Theoretical depth analysis (keyword extraction)
- [x] DocAnalyst: Report accuracy (cross-reference file paths)
- [x] EvidenceAggregator: Fan-in synchronization node
- [x] Safe git cloning with tempfile.TemporaryDirectory()
- [x] PDF ingestion with PyPDF2/docling
- [x] AST-based code analysis (not regex)

### Phase 3: Graph Orchestration ✅
- [x] StateGraph with parallel fan-out for detectives
- [x] EvidenceAggregator fan-in node
- [x] Proper edge configuration
- [x] Graph compilation and execution

### Phase 4: Testing ✅
- [x] Test suite for repo_tools
- [x] Test suite for doc_tools
- [x] Test suite for detective nodes
- [x] Test suite for partial graph execution
- [x] Evidence format validation

### Phase 5: Judicial Layer (In Progress)
- [ ] Prosecutor node with adversarial persona
- [ ] Defense node with optimistic persona
- [ ] Tech Lead node with pragmatic persona
- [ ] Structured output enforcement (.with_structured_output)
- [ ] Parallel execution for judges
- [ ] Chief Justice synthesis engine
- [ ] Conflict resolution rules (security override, fact supremacy)
- [ ] Markdown report generation

### Phase 6: Final Deliverables (Pending)
- [ ] Complete end-to-end workflow
- [ ] Self-audit report generation
- [ ] Peer audit report generation
- [ ] Video demonstration
- [ ] LangSmith trace links
- [ ] Final PDF report

## Known Limitations

### Current Implementation

1. **Judicial Layer Not Implemented**: The judges (Prosecutor, Defense, Tech Lead) and Chief Justice are not yet implemented. The graph currently stops at evidence aggregation.

2. **Vision Inspector Missing**: The VisionInspector detective for analyzing architectural diagrams is not implemented.

3. **Limited Error Handling**: Some edge cases in git operations and PDF parsing may not be fully handled.

4. **No LLM Integration Yet**: The detective nodes use static analysis only. LLM-based analysis will be added in the judicial layer.

5. **PDF Processing**: Currently uses PyPDF2 which may have limitations with complex PDFs. Docling support is available but optional.

### Future Improvements

1. **Caching**: Repository cloning could be cached to avoid redundant operations
2. **Parallel Processing**: Some operations could be further parallelized
3. **Streaming**: Large PDFs could be processed in streaming mode
4. **Retry Logic**: Network operations could include exponential backoff retries
5. **Validation**: More comprehensive input validation for repository URLs and file paths

## Development

### Running in Development Mode

```bash
# Install with dev dependencies
uv sync --dev

# Run with auto-reload (if using a tool like watchdog)
python -m src.graph

# Run tests in watch mode
pytest-watch tests/test_detectives.py
```

### Code Style

This project uses:
- **Black** for code formatting
- **Pydantic** for data validation
- **Type hints** throughout

Format code:
```bash
black src/ tests/
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure virtual environment is activated
   - Run `uv sync` to install dependencies

2. **"Git clone failed"**
   - Check network connection
   - Verify repository URL is accessible
   - Check git is installed and in PATH

3. **"PDF ingestion failed"**
   - Ensure PyPDF2 is installed: `uv add PyPDF2`
   - Check PDF file is not corrupted or encrypted

4. **"LangSmith tracing not working"**
   - Verify LANGCHAIN_API_KEY is set in .env
   - Check API key is valid at https://smith.langchain.com/

5. **"Import errors"**
   - Ensure you're running from project root
   - Check Python path includes project directory

## Contributing

This is a course project. For questions or issues, please refer to the course materials or contact the instructor.

## License

[Add your license here]

## Acknowledgments

Built as part of the FDE Challenge Week 2: The Automaton Auditor - Orchestrating Deep LangGraph Swarms for Autonomous Governance.
