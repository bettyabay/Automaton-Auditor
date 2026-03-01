# Automaton Auditor - Usage Guide for Submission

This guide will help you run the Automaton Auditor to generate the required submission files.

## Prerequisites

1. **Set up your `.env` file:**
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   LANGCHAIN_API_KEY=your_langsmith_api_key_here  # Optional but recommended
   LANGCHAIN_TRACING_V2=true  # Set to true to enable LangSmith tracing
   LANGCHAIN_PROJECT=automaton-auditor
   ```

2. **Ensure your PDF report exists:**
   - Your final report PDF should be at `reports/final_report.pdf`
   - This is what peers will audit when they run their agents against your repo

## Required Submission Files

### 1. Self-Audit Report
**Location:** `audit/report_onself_generated/`

Run your agent against your own repository:

```bash
# Option 1: Using environment variables (Linux/Mac)
export AUDIT_REPO_URL="https://github.com/YOUR_USERNAME/automaton-auditor"
export AUDIT_PDF_PATH="reports/final_report.pdf"
uv run python scripts/self_audit.py

# Option 2: Using command-line arguments (Linux/Mac)
uv run python scripts/self_audit.py "https://github.com/YOUR_USERNAME/automaton-auditor" "reports/final_report.pdf"
```

**Windows PowerShell:**
```powershell
# Option 1: Using environment variables
$env:AUDIT_REPO_URL="https://github.com/YOUR_USERNAME/automaton-auditor"
$env:AUDIT_PDF_PATH="reports/final_report.pdf"
uv run python scripts/self_audit.py

# Option 2: Single line (recommended)
uv run python scripts/self_audit.py "https://github.com/YOUR_USERNAME/automaton-auditor" "reports/final_report.pdf"

# Option 3: Using backticks for line continuation
uv run python scripts/self_audit.py `
  "https://github.com/YOUR_USERNAME/automaton-auditor" `
  "reports/final_report.pdf"
```

The report will be saved to: `audit/report_onself_generated/self_audit_report_TIMESTAMP.md`

### 2. Peer-Audit Report
**Location:** `audit/report_onpeer_generated/`

Run your agent against a peer's repository:

```bash
# First, download the peer's PDF report to your reports/ directory
# Then run:

# Option 1: Using environment variables (Linux/Mac)
export PEER_REPO_URL="https://github.com/PEER_USERNAME/automaton-auditor"
export PEER_PDF_PATH="reports/peer_report.pdf"
uv run python scripts/peer_audit.py

# Option 2: Using command-line arguments (Linux/Mac)
uv run python scripts/peer_audit.py \
  "https://github.com/PEER_USERNAME/automaton-auditor" \
  "reports/peer_report.pdf"
```

**Windows PowerShell:**
```powershell
# Option 1: Using environment variables
$env:PEER_REPO_URL="https://github.com/PEER_USERNAME/automaton-auditor"
$env:PEER_PDF_PATH="reports/peer_report.pdf"
uv run python scripts/peer_audit.py

# Option 2: Single line (recommended)
uv run python scripts/peer_audit.py "https://github.com/PEER_USERNAME/automaton-auditor" "reports/peer_report.pdf"

# Option 3: Using backticks for line continuation
uv run python scripts/peer_audit.py `
  "https://github.com/PEER_USERNAME/automaton-auditor" `
  "reports/peer_report.pdf"
```

The report will be saved to: `audit/report_onpeer_generated/peer_audit_PEERNAME_TIMESTAMP.md`

### 3. Peer-Audit Report (Received)
**Location:** `audit/report_bypeer_received/`

When a peer runs their agent against your repository, they will generate a report. You need to:
1. Ask your peer to share their generated report
2. Save it to `audit/report_bypeer_received/peer_audit_YOURNAME_TIMESTAMP.md`

This is the report that your peer's agent generated when auditing your repo.

## LangSmith Traces

To get LangSmith trace links:

1. **Enable tracing in `.env`:**
   ```
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_langsmith_api_key
   LANGCHAIN_PROJECT=automaton-auditor
   ```

2. **Run your audit** (self or peer)

3. **Get the trace link:**
   - Go to https://smith.langchain.com/
   - Navigate to your project: `automaton-auditor`
   - Find the most recent trace
   - Copy the shareable link

The trace should show:
- Detective nodes collecting evidence
- Judges rendering opinions in parallel
- Chief Justice synthesizing the final verdict

## Video Demonstration

Record a 5-minute screen recording showing:

1. **Starting the audit:**
   ```bash
   uv run python scripts/peer_audit.py \
     "https://github.com/PEER_USERNAME/automaton-auditor" \
     "reports/peer_report.pdf"
   ```

2. **Show the execution flow:**
   - Detectives collecting evidence (you can show console output or LangSmith trace)
   - Judges deliberating (show the parallel execution)
   - Chief Justice synthesis

3. **Show the final report:**
   - Open the generated Markdown report
   - Show the Executive Summary
   - Show a few Criterion Breakdown sections with judge opinions
   - Show the Remediation Plan

## Quick Start Example

Here's a complete example workflow:

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Run self-audit
uv run python scripts/self_audit.py \
  "https://github.com/YOUR_USERNAME/automaton-auditor" \
  "reports/final_report.pdf"

# 3. Run peer-audit (after downloading peer's PDF)
uv run python scripts/peer_audit.py \
  "https://github.com/PEER_USERNAME/automaton-auditor" \
  "reports/peer_report.pdf"

# 4. Check generated reports
ls audit/report_onself_generated/
ls audit/report_onpeer_generated/
```

## Troubleshooting

### "OPENAI_API_KEY not set"
- Make sure you've created `.env` file
- Make sure it contains `OPENAI_API_KEY=your_key`
- Make sure you're running from the project root

### "PDF file not found"
- Make sure the PDF path is correct
- For self-audit: `reports/final_report.pdf`
- For peer-audit: Download the peer's PDF first and place it in `reports/`

### "Git clone failed"
- Check your internet connection
- Verify the repository URL is correct and accessible
- For private repos, you may need to set up SSH keys or use a personal access token

### "No final report generated"
- Check that evidence was collected (look at console output)
- Check that judges produced opinions
- Review error messages in the console

## Report Structure

Each generated report contains:

1. **Executive Summary**
   - Overall score (1-5)
   - High-level findings

2. **Criterion Breakdown** (10 sections, one per rubric dimension)
   - Final synthesized score
   - Prosecutor opinion (adversarial)
   - Defense opinion (generous)
   - Tech Lead opinion (pragmatic)
   - Dissent summary (if judges disagreed significantly)
   - Remediation guidance

3. **Remediation Plan**
   - Priority fixes
   - All criteria summary

## Next Steps

1. ✅ Run self-audit and verify report is generated
2. ✅ Run peer-audit and verify report is generated
3. ✅ Get LangSmith trace link
4. ✅ Record video demonstration
5. ✅ Ensure `reports/final_report.pdf` is committed to your repo
6. ✅ Submit all files
