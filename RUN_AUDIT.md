# How to Run the Automaton Auditor

## Prerequisites

1. **Create `.env` file with your API key:**
   ```powershell
   # Copy the example file
   Copy-Item .env.example .env
   
   # Then edit .env and add your OpenAI API key:
   # OPENAI_API_KEY=sk-your-actual-key-here
   ```

## Running Self-Audit (Windows PowerShell)

### Step 1: Replace YOUR_USERNAME
Replace `YOUR_USERNAME` with your actual GitHub username.

### Step 2: Run the command

**Option A: Single line (recommended for Windows):**
```powershell
uv run python scripts/self_audit.py "https://github.com/YOUR_USERNAME/automaton-auditor" "reports/final_report.pdf"
```

**Option B: Using environment variables:**
```powershell
$env:AUDIT_REPO_URL="https://github.com/YOUR_USERNAME/automaton-auditor"
$env:AUDIT_PDF_PATH="reports/final_report.pdf"
uv run python scripts/self_audit.py
```

## Running Peer-Audit (Windows PowerShell)

**Single line:**
```powershell
uv run python scripts/peer_audit.py "https://github.com/PEER_USERNAME/automaton-auditor" "reports/peer_report.pdf"
```

## Example with Real Values

If your GitHub username is `johndoe`:

```powershell
uv run python scripts/self_audit.py "https://github.com/johndoe/automaton-auditor" "reports/final_report.pdf"
```

## What to Expect

1. The script will:
   - Check for API key
   - Initialize the graph
   - Load the rubric
   - Clone the repository
   - Analyze the code and PDF
   - Generate judge opinions
   - Create the final report

2. Output location:
   - Report saved to: `audit/report_onself_generated/self_audit_report_TIMESTAMP.md`

3. The process takes several minutes (5-15 minutes depending on repo size)

## Troubleshooting

**"OPENAI_API_KEY not set"**
- Make sure `.env` file exists in the project root
- Make sure it contains: `OPENAI_API_KEY=sk-...`

**"PDF file not found"**
- Make sure `reports/final_report.pdf` exists
- Or provide the correct path as the second argument

**"Git clone failed"**
- Check your internet connection
- Verify the repository URL is correct
- Make sure the repository is public (or you have access)
