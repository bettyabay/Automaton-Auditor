# Quick Start - Running Your First Audit

## Step 1: Set Up Environment

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env and add your API key:
# OPENAI_API_KEY=sk-your-key-here
```

## Step 2: Run Self-Audit

Replace `YOUR_USERNAME` with your GitHub username:

**Windows PowerShell (single line):**
```powershell
uv run python scripts/self_audit.py "https://github.com/YOUR_USERNAME/automaton-auditor" "reports/final_report.pdf"
```

**Linux/Mac (with line continuation):**
```bash
uv run python scripts/self_audit.py \
  "https://github.com/YOUR_USERNAME/automaton-auditor" \
  "reports/final_report.pdf"
```

**Output:** `audit/report_onself_generated/self_audit_report_TIMESTAMP.md`

## Step 3: Run Peer-Audit

First, download the peer's PDF report to `reports/peer_report.pdf`, then:

**Windows PowerShell (single line):**
```powershell
uv run python scripts/peer_audit.py "https://github.com/PEER_USERNAME/automaton-auditor" "reports/peer_report.pdf"
```

**Linux/Mac (with line continuation):**
```bash
uv run python scripts/peer_audit.py \
  "https://github.com/PEER_USERNAME/automaton-auditor" \
  "reports/peer_report.pdf"
```

**Output:** `audit/report_onpeer_generated/peer_audit_PEERNAME_TIMESTAMP.md`

## What Happens During Execution

1. **Detectives collect evidence** (parallel execution):
   - RepoInvestigator: Analyzes code structure, git history
   - DocAnalyst: Extracts keywords, cross-references file paths
   - VisionInspector: Analyzes diagrams in PDF

2. **Evidence aggregation**: All evidence is merged

3. **Judges deliberate** (parallel execution):
   - Prosecutor: Adversarial evaluation
   - Defense: Generous evaluation  
   - Tech Lead: Pragmatic evaluation

4. **Chief Justice synthesizes**: Applies deterministic rules to resolve conflicts

5. **Report generated**: Markdown file with full audit results

## Enable LangSmith Tracing

Add to `.env`:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=automaton-auditor
```

Then view traces at: https://smith.langchain.com/

## Troubleshooting

- **"OPENAI_API_KEY not set"**: Make sure `.env` file exists and has your key
- **"PDF not found"**: Check the path is correct
- **"Git clone failed"**: Verify the repo URL is accessible

See `USAGE_GUIDE.md` for detailed instructions.
