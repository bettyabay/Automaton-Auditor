# PowerShell Command Examples

## Correct Syntax for Windows PowerShell

### Self-Audit

**✅ CORRECT (single line):**
```powershell
uv run python scripts/self_audit.py "https://github.com/YOUR_USERNAME/automaton-auditor" "reports/final_report.pdf"
```

**❌ WRONG (don't escape quotes):**
```powershell
uv run python scripts/self_audit.py\"https://github.com/YOUR_USERNAME/automaton-auditor"\"reports/final_report.pdf"
```

### Peer-Audit

**✅ CORRECT (single line):**
```powershell
uv run python scripts/peer_audit.py "https://github.com/PEER_USERNAME/automaton-auditor" "reports/peer_report.pdf"
```

**❌ WRONG (don't escape quotes):**
```powershell
uv run python scripts/peer_audit.py\"https://github.com/PEER_USERNAME/automaton-auditor"\"reports/peer_report.pdf"
```

## Key Points

1. **No backslashes before quotes** - PowerShell doesn't need `\"` for quotes in arguments
2. **Use regular quotes** - Just use `"` at the start and end of each argument
3. **Space between arguments** - Put a space between each argument

## Real Example

If auditing Martha's repo:
```powershell
uv run python scripts/peer_audit.py "https://github.com/martha-ketsela-mengistu/automaton-auditor" "reports/peer_report.pdf"
```

## Alternative: Environment Variables

If you prefer, use environment variables:
```powershell
$env:PEER_REPO_URL="https://github.com/martha-ketsela-mengistu/automaton-auditor"
$env:PEER_PDF_PATH="reports/peer_report.pdf"
uv run python scripts/peer_audit.py
```
