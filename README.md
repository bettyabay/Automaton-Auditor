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

### Running the Full Swarm

The Automaton Auditor runs a complete multi-agent workflow:

1. **Detective Layer** (Parallel): RepoInvestigator, DocAnalyst, and VisionInspector collect evidence
2. **Evidence Aggregation**: All evidence is merged and validated
3. **Judicial Layer** (Parallel): Prosecutor, Defense, and Tech Lead render independent opinions
4. **Chief Justice**: Synthesizes conflicting opinions into final verdict
5. **Report Generation**: Creates comprehensive Markdown audit report

#### Method 1: Using Self-Audit Script

Audit your own repository:

```bash
# Set environment variables (or edit scripts/self_audit.py)
export AUDIT_REPO_URL="https://github.com/yourusername/automaton-auditor"
export AUDIT_PDF_PATH="reports/final_report.pdf"

# Run self-audit
uv run python scripts/self_audit.py
```

The script will:
- Initialize the full audit graph
- Load rubric dimensions
- Run complete audit workflow
- Generate report in `audit/self_audit/self_audit_report.md`
- Print summary statistics

#### Method 2: Using Peer-Audit Script

Audit a peer's repository:

```bash
# Set environment variables
export PEER_REPO_URL="https://github.com/peerusername/automaton-auditor"
export PEER_PDF_PATH="reports/peer_report.pdf"

# Run peer audit
uv run python scripts/peer_audit.py

# Or use command-line arguments
uv run python scripts/peer_audit.py \
  https://github.com/peerusername/automaton-auditor \
  reports/peer_report.pdf
```

#### Method 3: Using Python API

```python
from src.graph import run_audit

# Run complete audit workflow
final_state = run_audit(
    repo_url="https://github.com/user/repo.git",
    pdf_path="reports/architectural_report.pdf"
)

# Access results
final_report = final_state.get("final_report")
if final_report:
    print(f"Overall Score: {final_report.overall_score:.1f}/5")
    print(f"Executive Summary: {final_report.executive_summary}")
    
    for criterion in final_report.criteria:
        print(f"\n{criterion.dimension_name}: {criterion.final_score}/5")
        if criterion.dissent_summary:
            print(f"Dissent: {criterion.dissent_summary}")
```

#### Method 4: Using Docker

```bash
# Build image
docker build -t automaton-auditor .

# Run self-audit
docker run --rm \
  -e OPENAI_API_KEY=your_key \
  -e LANGCHAIN_API_KEY=your_key \
  -v $(pwd)/audit:/app/audit \
  -v $(pwd)/reports:/app/reports \
  automaton-auditor

# Or use docker-compose
docker-compose up
```

### How to Interpret Results

#### Understanding the Audit Report

The system generates comprehensive Markdown reports with the following structure:

1. **Executive Summary**
   - Overall score (1-5 scale)
   - High-level findings
   - Strongest and weakest criteria

2. **Criterion Breakdown**
   - Each rubric dimension evaluated separately
   - Final synthesized score
   - All three judge opinions (Prosecutor, Defense, Tech Lead)
   - Dissent summary (if judges disagreed significantly)
   - Remediation guidance

3. **Remediation Plan**
   - Priority fixes (lowest-scoring criteria)
   - All criteria summary
   - Actionable recommendations

#### Score Interpretation

- **5/5**: Excellent - Meets all requirements perfectly
- **4/5**: Good - Meets most requirements with minor gaps
- **3/5**: Acceptable - Meets core requirements but has significant gaps
- **2/5**: Poor - Major issues, needs substantial work
- **1/5**: Critical - Fundamental requirements missing

#### Understanding Judge Opinions

Each criterion receives three independent opinions:

- **Prosecutor** (Adversarial): Looks for gaps, security flaws, and laziness. Typically scores 1-3.
- **Defense** (Generous): Rewards effort and intent. Typically scores 3-5.
- **Tech Lead** (Pragmatic): Evaluates technical correctness and maintainability. Typically scores 1, 3, or 5.

**High Variance (>2 points)**: Indicates significant disagreement, triggering deeper analysis and explicit dissent summary.

#### Understanding Synthesis Rules

The Chief Justice applies deterministic rules:

1. **Security Override**: If Prosecutor finds security flaws, score is capped at 3
2. **Fact Supremacy**: Evidence always overrules opinion. If Defense claims something exists but evidence contradicts, Defense is overruled.
3. **Functionality Weight**: For architecture criteria, Tech Lead's opinion carries highest weight
4. **Variance Re-evaluation**: High disagreement triggers specific re-evaluation

#### Reading Evidence

Evidence objects contain:
- `found`: Boolean indicating if requirement was met
- `confidence`: Float 0.0-1.0 indicating certainty
- `location`: File path or location where evidence was found
- `content`: Relevant code snippet or text
- `rationale`: Explanation of the finding

#### Example Report Analysis

```markdown
### Graph Orchestration Architecture
**Final Score: 4/5**

**Judge Opinions:**
- *Prosecutor* (Score: 3): "Judges don't start in perfect parallel..."
- *Defense* (Score: 5): "Architecture is sound. Parallel execution is implemented..."
- *TechLead* (Score: 4): "Good architecture with minor limitation..."

**Dissent:** Prosecutor noted that judges don't start in perfect parallel, 
but Defense and Tech Lead argued this is acceptable given LangGraph constraints.

**Remediation:** Investigate LangGraph's ability to route conditional edges 
to multiple nodes simultaneously for perfect parallel execution.
```

This shows:
- Final score (4/5) is a synthesis of three opinions
- Disagreement exists (variance = 2), so dissent is explained
- Remediation provides actionable next steps

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
│   ├── state.py              # Pydantic models (Evidence, JudicialOpinion, AuditReport, AgentState)
│   ├── graph.py              # LangGraph StateGraph with full workflow
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── detectives.py     # RepoInvestigator, DocAnalyst, VisionInspector, EvidenceAggregator
│   │   ├── judges.py          # Prosecutor, Defense, TechLead nodes with structured output
│   │   └── justice.py         # ChiefJustice synthesis engine with deterministic rules
│   └── tools/
│       ├── __init__.py
│       ├── repo_tools.py      # Safe git cloning, history extraction, AST parsing
│       └── doc_tools.py       # PDF ingestion, keyword extraction, image analysis
├── scripts/
│   ├── self_audit.py          # Self-audit script for own repository
│   ├── peer_audit.py          # Peer-audit script for other repositories
│   └── generate_pdf_report.py # Convert Markdown reports to PDF
├── tests/
│   ├── __init__.py
│   └── test_detectives.py     # Comprehensive test suite
├── reports/                   # PDF reports to analyze
│   ├── final_report.md        # Final project report (see Reports section)
│   └── interim_report.md      # Interim status report
├── audit/                     # Generated audit reports
│   ├── self_audit/           # Self-audit reports
│   ├── peer_audit/           # Peer-audit reports
│   └── report_*.md           # Timestamped audit reports
├── rubric.json                # Evaluation rubric (machine-readable)
├── pyproject.toml             # Project metadata and dependencies
├── uv.lock                    # Locked dependency versions
├── Dockerfile                 # Docker containerization
├── docker-compose.yml         # Docker Compose configuration
├── .dockerignore              # Docker build exclusions
├── .env.example               # Environment variables template
├── .env                       # Your actual environment variables (not in git)
└── README.md                  # This file
```

### Key Components

#### State Management (`src/state.py`)
- **Pydantic Models**: `Evidence`, `JudicialOpinion`, `CriterionResult`, `AuditReport`
- **TypedDict with Reducers**: `AgentState` uses `Annotated` with `operator.ior` (dict merge) and `operator.add` (list concat) to prevent data overwriting during parallel execution
- **Type Safety**: All models include field validations and docstrings

#### Graph Orchestration (`src/graph.py`)
- **StateGraph**: Complete workflow with parallel fan-out/fan-in patterns
- **Detective Layer**: Parallel execution of RepoInvestigator, DocAnalyst, VisionInspector
- **Judicial Layer**: Parallel execution of Prosecutor, Defense, Tech Lead
- **Conditional Edges**: Evidence sufficiency checking before judicial evaluation
- **Chief Justice**: Final synthesis and report generation

#### Detective Nodes (`src/nodes/detectives.py`)
- **RepoInvestigator**: Analyzes git history, code structure, state management, graph orchestration
- **DocAnalyst**: Extracts keywords, cross-references file paths, analyzes theoretical depth
- **VisionInspector**: Extracts and analyzes diagrams from PDFs using multimodal LLMs
- **EvidenceAggregator**: Merges evidence from all detectives using reducer-safe operations

#### Judicial Nodes (`src/nodes/judges.py`)
- **Prosecutor**: Adversarial persona, scores harshly, looks for gaps and security flaws
- **Defense**: Generous persona, rewards effort and intent, argues for partial credit
- **Tech Lead**: Pragmatic persona, evaluates technical correctness and maintainability
- **Structured Output**: All judges use `.with_structured_output(JudicialOpinion)` for type-safe opinions

#### Chief Justice (`src/nodes/justice.py`)
- **Deterministic Rules**: Security override, fact supremacy, functionality weight
- **Conflict Resolution**: Synthesizes conflicting opinions using hardcoded Python logic
- **Report Generation**: Converts `AuditReport` to formatted Markdown
- **Dissent Summaries**: Explains high-variance disagreements

#### Tools (`src/tools/`)
- **repo_tools.py**: Safe git cloning with `tempfile.TemporaryDirectory()`, git history parsing, AST-based code analysis
- **doc_tools.py**: PDF text extraction, keyword analysis, image extraction, multimodal diagram analysis

#### Scripts (`scripts/`)
- **self_audit.py**: Runs audit against own repository with comprehensive feedback
- **peer_audit.py**: Runs audit against peer repositories with command-line support
- **generate_pdf_report.py**: Converts Markdown reports to PDF format

## Reports and Documentation

### Final Report
📄 **[Final Report](reports/final_report.md)** - Comprehensive project documentation including:
- Executive Summary with key achievements
- Architecture Deep Dive (Dialectical Synthesis, Fan-In/Fan-Out, Metacognition)
- Self-Audit Results with criterion-by-criterion breakdown
- MinMax Feedback Loop Reflection
- Remediation Plan with priority order

### Interim Report
📄 **[Interim Report](reports/interim_report.md)** - Development status documentation including:
- Architecture decisions and rationale
- Current implementation status
- Known gaps and limitations
- Mermaid diagrams of graph flow
- Plan for remaining work

### Generating PDF Reports

Convert Markdown reports to PDF:

```bash
# Using the script (requires pandoc or markdown2+reportlab)
uv run python scripts/generate_pdf_report.py

# Or using pandoc directly
pandoc reports/final_report.md -o reports/final_report.pdf \
  --pdf-engine=xelatex --toc --toc-depth=2
```

## Implementation Status

### ✅ Completed Features

#### Phase 1: Infrastructure
- [x] State definitions with Pydantic models and TypedDict
- [x] State reducers (operator.add, operator.ior) to prevent data overwriting
- [x] Environment setup with .env.example
- [x] LangSmith tracing integration
- [x] Project structure with proper package organization

#### Phase 2: Detective Layer
- [x] RepoInvestigator: Git forensic analysis, state management, graph orchestration
- [x] DocAnalyst: Theoretical depth analysis, report accuracy cross-referencing
- [x] VisionInspector: Diagram extraction and multimodal analysis
- [x] EvidenceAggregator: Fan-in synchronization node
- [x] Safe git cloning with tempfile.TemporaryDirectory()
- [x] PDF ingestion with PyPDF2/docling
- [x] AST-based code analysis (not regex)

#### Phase 3: Graph Orchestration
- [x] StateGraph with parallel fan-out for detectives
- [x] EvidenceAggregator fan-in node
- [x] Conditional edges for evidence validation
- [x] Graph compilation and execution

#### Phase 4: Judicial Layer
- [x] Prosecutor node with adversarial persona
- [x] Defense node with generous persona
- [x] Tech Lead node with pragmatic persona
- [x] Structured output enforcement (.with_structured_output)
- [x] Parallel execution for judges
- [x] Chief Justice synthesis engine
- [x] Conflict resolution rules (security override, fact supremacy, functionality weight)
- [x] Markdown report generation

#### Phase 5: Final Deliverables
- [x] Complete end-to-end workflow
- [x] Self-audit script
- [x] Peer-audit script
- [x] Final report documentation
- [x] Docker containerization
- [x] Comprehensive README

## Known Limitations

### Current Implementation

1. **Judge Parallel Execution**: Judges don't start in perfect parallel due to LangGraph conditional edge limitations. Conditional routes to Prosecutor first, then Prosecutor fans out to Defense and Tech Lead. This is a minor architectural limitation but doesn't affect functionality.

2. **Error Recovery**: If one detective fails completely, the audit may fail. Partial evidence collection is supported, but graceful degradation could be improved.

3. **PDF Processing Quality**: PDF text extraction quality varies by document structure. Complex PDFs with tables, charts, or unusual layouts may not extract perfectly. Docling support improves quality but is optional.

4. **Performance**: Large repositories take significant time to clone and analyze. No caching mechanism exists yet, so repeated audits of the same repository re-clone each time.

5. **Test Coverage**: Current test coverage is ~60%. Edge cases and error scenarios need more comprehensive testing.

6. **Vision Analysis**: Vision Inspector requires multimodal LLM (GPT-4V or Gemini Pro Vision). If these are unavailable, diagram analysis is skipped.

### Future Improvements

1. **Perfect Judge Parallel Execution**: Investigate LangGraph's ability to route conditional edges to multiple nodes simultaneously, or create a routing node that fans out to all three judges.

2. **Enhanced Error Recovery**: Implement try-catch in each detective node, allowing partial evidence collection even if one detective fails.

3. **Repository Caching**: Cache cloned repositories to avoid redundant operations. Implement incremental updates for repositories that have already been cloned.

4. **Performance Optimization**: 
   - Parallel file analysis within repositories
   - Streaming PDF processing for large documents
   - Incremental git history analysis

5. **Comprehensive Test Coverage**: Add integration tests for full graph execution, error scenarios, and edge cases. Target 90%+ coverage.

6. **Enhanced PDF Analysis**: Integrate advanced PDF libraries (docling, pdfplumber) with better extraction for tables, charts, and complex layouts.

7. **Interactive Report Viewer**: Create web-based report viewer with filtering, search, and visualization capabilities.

8. **Multi-Repository Batch Audits**: Add batch processing capability for comparing multiple repositories simultaneously.

9. **Custom Rubric Support**: Add support for custom rubric schemas and validation for different use cases.

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

## Docker Deployment

### Building the Image

```bash
# Build Docker image
docker build -t automaton-auditor .

# Verify image was created
docker images | grep automaton-auditor
```

### Running with Docker

```bash
# Run self-audit (requires environment variables)
docker run --rm \
  -e OPENAI_API_KEY=your_key \
  -e LANGCHAIN_API_KEY=your_key \
  -e LANGCHAIN_TRACING_V2=true \
  -e AUDIT_REPO_URL=https://github.com/yourusername/automaton-auditor \
  -e AUDIT_PDF_PATH=reports/final_report.pdf \
  -v $(pwd)/audit:/app/audit \
  -v $(pwd)/reports:/app/reports \
  automaton-auditor

# Run peer audit
docker run --rm \
  -e OPENAI_API_KEY=your_key \
  -e PEER_REPO_URL=https://github.com/peerusername/automaton-auditor \
  -e PEER_PDF_PATH=reports/peer_report.pdf \
  -v $(pwd)/audit:/app/audit \
  -v $(pwd)/reports:/app/reports \
  automaton-auditor \
  uv run python scripts/peer_audit.py
```

### Using Docker Compose

```bash
# Create .env file with your API keys
cp .env.example .env
# Edit .env and add your keys

# Run with docker-compose
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Docker Compose Configuration

The `docker-compose.yml` file includes:
- Environment variable support from `.env` file
- Volume mounts for `audit/` and `reports/` directories
- Easy command override for different scripts
- Automatic restart policy

## Observability and Debugging

### LangSmith Tracing

When `LANGCHAIN_TRACING_V2=true` is set, all agent executions are traced in LangSmith:

1. **View Traces**: Go to https://smith.langchain.com/
2. **Filter by Project**: Select `automaton-auditor` project
3. **Explore Execution**: Click on any trace to see:
   - Node execution order
   - State transitions
   - LLM calls and responses
   - Evidence collection details
   - Judicial opinion generation

**Example Trace Flow**:
```
START → RepoInvestigator (parallel)
      → DocAnalyst (parallel)
      → VisionInspector (parallel)
      → EvidenceAggregator
      → Prosecutor (parallel)
      → Defense (parallel)
      → TechLead (parallel)
      → ChiefJustice
      → END
```

### Debugging Tips

1. **Check Evidence Collection**: Look at `state["evidences"]` in LangSmith traces
2. **Verify Judge Opinions**: Check `state["opinions"]` to see all three perspectives
3. **Review Synthesis**: Examine Chief Justice node to see which rules were applied
4. **Trace Errors**: Failed nodes will show error details in LangSmith

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure virtual environment is activated: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux)
   - Run `uv sync` to install dependencies
   - Verify you're in the project root directory

2. **"Git clone failed"**
   - Check network connection
   - Verify repository URL is accessible (try cloning manually)
   - Check git is installed and in PATH: `git --version`
   - For private repos, ensure credentials are configured

3. **"PDF ingestion failed"**
   - Ensure PyPDF2 is installed: `uv add PyPDF2`
   - Check PDF file is not corrupted or encrypted
   - Try with a different PDF to isolate the issue
   - For complex PDFs, consider installing docling: `uv add docling`

4. **"LangSmith tracing not working"**
   - Verify `LANGCHAIN_API_KEY` is set in `.env`
   - Check API key is valid at https://smith.langchain.com/
   - Ensure `LANGCHAIN_TRACING_V2=true` is set
   - Check project name matches: `LANGCHAIN_PROJECT=automaton-auditor`

5. **"Import errors"**
   - Ensure you're running from project root
   - Check Python path includes project directory: `export PYTHONPATH=$(pwd)`
   - Verify virtual environment is activated
   - Try: `uv run python scripts/self_audit.py` instead of `python scripts/self_audit.py`

6. **"OpenAI API errors"**
   - Verify `OPENAI_API_KEY` is set correctly
   - Check API key has sufficient credits
   - Ensure you're using a model you have access to (gpt-4-turbo-preview, gpt-4o)
   - For vision analysis, ensure you have access to GPT-4V or Gemini Pro Vision

7. **"Judges not producing opinions"**
   - Check that evidence was collected (look at `state["evidences"]`)
   - Verify structured output is working (check LangSmith traces)
   - Ensure LLM has sufficient context (evidence may be too sparse)
   - Check for rate limiting or API errors in traces

8. **"Chief Justice synthesis fails"**
   - Verify all three judges produced opinions
   - Check that opinions are valid `JudicialOpinion` objects
   - Look for errors in synthesis logic (check logs)
   - Ensure `rubric.json` is valid and accessible

## Contributing

This is a course project. For questions or issues, please refer to the course materials or contact the instructor.

## License

[Add your license here]

## Acknowledgments

Built as part of the FDE Challenge Week 2: The Automaton Auditor - Orchestrating Deep LangGraph Swarms for Autonomous Governance.
