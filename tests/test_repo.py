# tests/test_repo_miner.py

import os
import pandas as pd
import pytest
from datetime import datetime, timedelta
from src.config import COMMIT_COLUMNS, ISSUE_COLUMNS
from src.repo_miner import fetch_commits, fetch_issues, merge_and_summarize
from tests.dummies import DummyAuthor, DummyCommitCommit, DummyCommit, DummyUser, DummyIssue, DummyRepo, DummyGithub

def is_iso8601_format(date_str: str) -> bool:
    try:
        datetime.fromisoformat(date_str)
        return True
    except ValueError:
        return False

# --- Tests for fetch_commits ---
class TestsWithDummies:
    
    # Helper instance
    gh_instance = DummyGithub("fake-token")
    
    @pytest.fixture(autouse=True)
    def patch_env_and_github(self, monkeypatch):
        # Set fake token
        monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
        # Patch Github class'
        monkeypatch.setattr("src.repo_miner.Github", lambda auth=None: self.gh_instance)
        
    
    # An example test case
    def test_fetch_commits_basic(self, monkeypatch):
        # Setup dummy commits
        now = datetime.now()
        commits = [
            DummyCommit("sha1", "Alice", "a@example.com", now, "Initial commit\nDetails"),
            DummyCommit("sha2", "Bob", "b@example.com", now - timedelta(days=1), "Bug fix")
        ]
        self.gh_instance._repo = DummyRepo(commits, [])
        df = fetch_commits("any/repo")
        assert list(df.columns) == COMMIT_COLUMNS
        assert len(df) == 2
        assert df.iloc[0]["message (first line)"] == "Initial commit"
        
    def test_fetch_issues_basic(self, monkeypatch):
        now = datetime.now()
        issues = [
            DummyIssue(1, 101, "Issue A", "alice", "open", now, None, 0),
            DummyIssue(2, 102, "Issue B", "bob", "closed", (now - timedelta(days=2)), now, 2)
        ]
        self.gh_instance._repo = DummyRepo([], issues)
        df = fetch_issues("any/repo", state="all")
        assert list(df.columns) == ISSUE_COLUMNS
        assert len(df) == 2
        # Check date normalization
        assert is_iso8601_format(df.iloc[0]["created_at"])
        assert is_iso8601_format(df.iloc[1]["closed_at"])

# --- Tests that hit real GitHub API (will be simulated with vcrpy) ---
class TestsWithVCR:
    @pytest.mark.vcr
    def test_fetch_commits_basic(self, monkeypatch):
        """ Basic fetch on well known small repo """
        df = fetch_commits("octocat/Hello-World")
        assert list(df.columns) == COMMIT_COLUMNS
        assert len(df) == 3
        assert df.iloc[0]["message (first line)"] == "Merge pull request #6 from Spaceghost/patch-1"

    @pytest.mark.vcr
    def test_fetch_commits_limit(self, monkeypatch):
        """ More commits than max_commits. Test that fetch_commits respects the max_commits limit. """
        df = fetch_commits("octocat/Hello-World", max_commits=2)
        assert list(df.columns) == COMMIT_COLUMNS
        assert len(df) == 2
        assert df.iloc[0]["message (first line)"] == "Merge pull request #6 from Spaceghost/patch-1"
            
    @pytest.mark.vcr
    def test_fetch_commits_empty(self, monkeypatch):
        """ Test that fetch_commits returns empty DataFrame when no max commits exist. """
        # Uses a cassette modified so that it returns 0 commits
        df = fetch_commits("octocat/Hello-World")
        assert list(df.columns) == COMMIT_COLUMNS
        assert len(df) == 0
        assert df.empty
    
    @pytest.mark.vcr
    def test_fetch_issues_PR_filtering(self, monkeypatch):
        """ Test that fetch issues filters out PRs."""
        # TODO: Implement this test
        pass
    
    @pytest.mark.vcr
    def test_fetch_issues_correct_date_parsing(self, monkeypatch):
        """ Test that fetch issues correctly parses dates. Dates should be in ISO-8601 format. """
        # TODO: Implement this test
        pass
    
    @pytest.mark.vcr
    def test_fetch_issues_open_duration(self, monkeypatch):
        """ Test that fetch issues correctly computes open_duration_days. """
        # TODO: Implement this test
        pass
    