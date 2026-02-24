"""
Repository tools for forensic code analysis.

This module provides safe, sandboxed operations for cloning and analyzing
GitHub repositories. All operations use temporary directories to prevent
contamination of the working directory and include comprehensive error handling.
"""

import os
import subprocess
import tempfile
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse


# Global variable to store the temporary directory context
# This ensures the directory persists beyond the function call
_temp_dirs: Dict[str, tempfile.TemporaryDirectory] = {}


def clone_repository(repo_url: str) -> str:
    """
    Safely clone a GitHub repository into a temporary directory.
    
    This function uses tempfile.TemporaryDirectory() to create an isolated
    sandbox for the cloned repository, preventing contamination of the
    working directory. All git operations are executed via subprocess.run()
    with proper error handling.
    
    Args:
        repo_url: The GitHub repository URL to clone (e.g., 
                 "https://github.com/user/repo.git" or "git@github.com:user/repo.git")
    
    Returns:
        str: The absolute path to the cloned repository directory
    
    Raises:
        ValueError: If the repository URL is invalid or malformed
        subprocess.CalledProcessError: If git clone fails (authentication, network, etc.)
        RuntimeError: If temporary directory creation fails
    
    Example:
        >>> repo_path = clone_repository("https://github.com/user/repo.git")
        >>> print(repo_path)
        '/tmp/tmpXXXXXX/repo'
    
    Security Notes:
        - All operations run in isolated temporary directories
        - No raw os.system() calls (uses subprocess.run() with proper validation)
        - Repository URL is validated before execution
        - Authentication errors are caught and reported gracefully
    """
    # Validate URL format
    if not repo_url or not isinstance(repo_url, str):
        raise ValueError(f"Invalid repository URL: {repo_url}")
    
    # Parse URL to extract repository name
    parsed_url = urlparse(repo_url)
    
    # Handle both HTTPS and SSH URLs
    if repo_url.startswith("git@") or repo_url.startswith("ssh://"):
        # SSH URL format: git@github.com:user/repo.git
        repo_name = repo_url.split(":")[-1].replace(".git", "").split("/")[-1]
    elif parsed_url.path:
        # HTTPS URL format: https://github.com/user/repo.git
        repo_name = parsed_url.path.strip("/").split("/")[-1].replace(".git", "")
    else:
        raise ValueError(f"Unable to parse repository name from URL: {repo_url}")
    
    if not repo_name:
        raise ValueError(f"Invalid repository URL format: {repo_url}")
    
    try:
        # Create a temporary directory for this clone operation
        # The directory will persist until cleanup_repository() is called
        temp_dir = tempfile.TemporaryDirectory(prefix="automaton_auditor_")
        temp_path = temp_dir.name
        
        # Store the TemporaryDirectory object to prevent cleanup
        _temp_dirs[repo_url] = temp_dir
        
        # Clone the repository using subprocess.run() with proper error handling
        clone_path = os.path.join(temp_path, repo_name)
        
        # Prepare git clone command
        # Use --depth 1 for faster cloning (shallow clone)
        # Use --quiet to reduce output noise
        git_cmd = [
            "git",
            "clone",
            "--depth", "1",  # Shallow clone for speed
            "--quiet",  # Suppress progress output
            repo_url,
            clone_path
        ]
        
        # Execute git clone with proper error handling
        result = subprocess.run(
            git_cmd,
            cwd=temp_path,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            check=False  # Don't raise on non-zero exit
        )
        
        # Check for authentication errors
        if result.returncode != 0:
            error_output = result.stderr.lower()
            
            if "authentication" in error_output or "permission denied" in error_output:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    git_cmd,
                    f"Authentication failed for repository: {repo_url}. "
                    "Please check your credentials or repository access permissions."
                )
            elif "not found" in error_output or "does not exist" in error_output:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    git_cmd,
                    f"Repository not found: {repo_url}. "
                    "Please verify the repository URL is correct."
                )
            elif "network" in error_output or "connection" in error_output:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    git_cmd,
                    f"Network error while cloning: {repo_url}. "
                    "Please check your internet connection."
                )
            else:
                # Generic error
                raise subprocess.CalledProcessError(
                    result.returncode,
                    git_cmd,
                    f"Git clone failed: {result.stderr}"
                )
        
        # Verify the cloned directory exists
        if not os.path.exists(clone_path):
            raise RuntimeError(f"Repository cloned but directory not found: {clone_path}")
        
        # Verify it's actually a git repository
        git_dir = os.path.join(clone_path, ".git")
        if not os.path.exists(git_dir):
            raise RuntimeError(f"Cloned directory is not a valid git repository: {clone_path}")
        
        return os.path.abspath(clone_path)
    
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Git clone operation timed out for: {repo_url}")
    except subprocess.CalledProcessError as e:
        # Re-raise with context
        raise
    except Exception as e:
        raise RuntimeError(f"Unexpected error while cloning repository: {str(e)}")


def extract_git_history(repo_path: str) -> Dict:
    """
    Extract and parse git commit history from a cloned repository.
    
    This function runs 'git log --oneline --reverse' to get a chronological
    list of commits and analyzes the history to determine if it shows
    iterative development (atomic commits with progression) or bulk upload
    patterns (single init commit or clustered timestamps).
    
    Args:
        repo_path: The absolute path to the cloned repository directory
    
    Returns:
        Dict: A structured dictionary containing:
            - commits: List of commit dictionaries with:
                - hash: Short commit hash
                - message: Commit message
                - timestamp: ISO format timestamp
                - datetime: Parsed datetime object
            - total_commits: Total number of commits
            - is_atomic: Boolean indicating if history shows iterative development
            - progression_detected: Boolean indicating clear progression pattern
            - commit_timespan_hours: Time span between first and last commit (hours)
            - analysis: Human-readable analysis summary
    
    Raises:
        ValueError: If repo_path is invalid or not a git repository
        subprocess.CalledProcessError: If git log command fails
        RuntimeError: If repository analysis fails
    
    Example:
        >>> history = extract_git_history("/tmp/repo")
        >>> print(history["total_commits"])
        5
        >>> print(history["is_atomic"])
        True
    
    Analysis Logic:
        - Atomic history: >3 commits with meaningful progression
        - Bulk upload: Single commit or timestamps clustered within minutes
        - Progression: Commit messages show clear development stages
    """
    # Validate repository path
    if not repo_path or not isinstance(repo_path, str):
        raise ValueError(f"Invalid repository path: {repo_path}")
    
    if not os.path.exists(repo_path):
        raise ValueError(f"Repository path does not exist: {repo_path}")
    
    # Verify it's a git repository
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.exists(git_dir):
        raise ValueError(f"Path is not a git repository: {repo_path}")
    
    try:
        # Run git log with detailed format
        # --oneline: One line per commit
        # --reverse: Chronological order (oldest first)
        # --format: Custom format with hash, timestamp, and message
        git_cmd = [
            "git",
            "log",
            "--oneline",
            "--reverse",
            "--format=%H|%ai|%s",  # Full hash|ISO timestamp|subject
            "--all"  # Include all branches
        ]
        
        result = subprocess.run(
            git_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout
            check=True
        )
        
        # Parse commit lines
        commits = []
        lines = result.stdout.strip().split("\n")
        
        for line in lines:
            if not line.strip():
                continue
            
            try:
                # Parse format: HASH|TIMESTAMP|MESSAGE
                parts = line.split("|", 2)
                if len(parts) >= 3:
                    commit_hash = parts[0][:7]  # Short hash
                    timestamp_str = parts[1]
                    message = parts[2].strip()
                    
                    # Parse timestamp
                    try:
                        # Git timestamp format: 2024-01-15 10:30:45 -0500
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S %z")
                    except ValueError:
                        # Fallback parsing
                        dt = datetime.fromisoformat(timestamp_str.replace(" ", "T"))
                    
                    commits.append({
                        "hash": commit_hash,
                        "message": message,
                        "timestamp": timestamp_str,
                        "datetime": dt.isoformat()
                    })
            except (ValueError, IndexError) as e:
                # Skip malformed lines but continue processing
                continue
        
        total_commits = len(commits)
        
        # Analyze commit history patterns
        is_atomic = False
        progression_detected = False
        commit_timespan_hours = 0.0
        analysis = ""
        
        if total_commits == 0:
            analysis = "No commits found in repository."
        elif total_commits == 1:
            analysis = "Single commit detected - likely bulk upload or initial commit."
            is_atomic = False
        else:
            # Calculate time span
            first_commit = commits[0]
            last_commit = commits[-1]
            
            try:
                first_dt = datetime.fromisoformat(first_commit["datetime"])
                last_dt = datetime.fromisoformat(last_commit["datetime"])
                time_diff = last_dt - first_dt
                commit_timespan_hours = time_diff.total_seconds() / 3600.0
            except (ValueError, KeyError):
                commit_timespan_hours = 0.0
            
            # Check for atomic progression
            # Criteria: >3 commits AND meaningful time span OR progression keywords
            if total_commits > 3:
                # Check for progression keywords in commit messages
                progression_keywords = [
                    "init", "setup", "add", "implement", "refactor",
                    "fix", "update", "create", "add", "feat", "chore"
                ]
                
                keyword_count = sum(
                    1 for commit in commits
                    if any(keyword in commit["message"].lower() for keyword in progression_keywords)
                )
                
                # Check if timestamps are spread out (not clustered)
                # If timespan > 1 hour, likely iterative development
                timespan_ok = commit_timespan_hours > 1.0
                
                # If >50% of commits have progression keywords, likely atomic
                keyword_ratio = keyword_count / total_commits if total_commits > 0 else 0
                
                is_atomic = timespan_ok or keyword_ratio > 0.5
                progression_detected = keyword_ratio > 0.3 and timespan_ok
                
                if is_atomic:
                    analysis = (
                        f"Atomic history detected: {total_commits} commits "
                        f"over {commit_timespan_hours:.1f} hours. "
                        "Shows iterative development pattern."
                    )
                else:
                    analysis = (
                        f"Bulk upload pattern: {total_commits} commits "
                        f"but timestamps clustered within {commit_timespan_hours:.1f} hours. "
                        "Likely single bulk upload."
                    )
            else:
                # 2-3 commits: borderline case
                if commit_timespan_hours > 0.5:
                    is_atomic = True
                    analysis = (
                        f"Limited history ({total_commits} commits) "
                        f"but shows some progression over {commit_timespan_hours:.1f} hours."
                    )
                else:
                    analysis = (
                        f"Limited history ({total_commits} commits) "
                        "with clustered timestamps. May be bulk upload."
                    )
        
        return {
            "commits": commits,
            "total_commits": total_commits,
            "is_atomic": is_atomic,
            "progression_detected": progression_detected,
            "commit_timespan_hours": commit_timespan_hours,
            "analysis": analysis
        }
    
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(
            e.returncode,
            e.cmd,
            f"Git log failed: {e.stderr}"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Git log operation timed out for: {repo_path}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error while extracting git history: {str(e)}")


def cleanup_repository(repo_url: str) -> None:
    """
    Clean up the temporary directory for a cloned repository.
    
    This function should be called when the repository analysis is complete
    to free up disk space. The temporary directory and all its contents will
    be deleted.
    
    Args:
        repo_url: The repository URL that was cloned
    
    Example:
        >>> cleanup_repository("https://github.com/user/repo.git")
    """
    if repo_url in _temp_dirs:
        try:
            _temp_dirs[repo_url].cleanup()
            del _temp_dirs[repo_url]
        except Exception as e:
            # Log but don't raise - cleanup failures shouldn't break the flow
            print(f"Warning: Failed to cleanup repository {repo_url}: {e}")


def cleanup_all_repositories() -> None:
    """
    Clean up all temporary directories created by clone_repository.
    
    This function should be called at the end of the audit process
    to ensure all temporary directories are cleaned up.
    
    Example:
        >>> cleanup_all_repositories()
    """
    for repo_url in list(_temp_dirs.keys()):
        cleanup_repository(repo_url)
