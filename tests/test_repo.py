# tests/test_repo_miner.py

import os
import pandas as pd
import pytest
from datetime import datetime, timedelta
from src.repo_miner import fetch_commits, fetch_issues, merge_and_summarize
from tests.dummies import DummyAuthor, DummyCommitCommit, DummyCommit, DummyUser, DummyIssue, DummyRepo, DummyGithub

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
        assert list(df.columns) == ["sha", "author", "email", "date", "message"]
        assert len(df) == 2
        assert df.iloc[0]["message"] == "Initial commit"

# --- Tests that hit real GitHub API (will be simulated with vcrpy) ---
@pytest.mark.vcr
def test_fetch_commits_basic(monkeypatch):
    """ Basic fetch on well known small repo """
    df = fetch_commits("octocat/Hello-World")
    assert list(df.columns) == ["sha", "author", "email", "date (ISO-8601)", "message (first line)"]
    assert len(df) == 3
    assert df.iloc[0]["message"] == "Merge pull request #6 from Spaceghost/patch-1"

@pytest.mark.vcr
def test_fetch_commits_limit(monkeypatch):
    """ More commits than max_commits. Test that fetch_commits respects the max_commits limit. """
    df = fetch_commits("octocat/Hello-World", max_commits=2)
    assert list(df.columns) == ["sha", "author", "email", "date (ISO-8601)", "message (first line)"]
    assert len(df) == 2
    assert df.iloc[0]["message"] == "Merge pull request #6 from Spaceghost/patch-1"
        
@pytest.mark.vcr
def test_fetch_commits_empty(monkeypatch):
    """ Test that fetch_commits returns empty DataFrame when no max commits exist. """
    # Uses a cassette modified so that it returns 0 commits
    df = fetch_commits("octocat/Hello-World")
    assert list(df.columns) == ["sha", "author", "email", "date (ISO-8601)", "message (first line)"]
    assert len(df) == 0
    assert df.empty