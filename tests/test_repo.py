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
        assert df.iloc[0]["message"] == "Initial commit"
        
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
    
    def test_merge_and_summarize_output(self, capsys):
        # Prepare test DataFrames
        df_commits = pd.DataFrame({
            "sha": ["a", "b", "c", "d"],
            "author": ["X", "Y", "X", "Z"],
            "email": ["x@e", "y@e", "x@e", "z@e"],
            "date": ["2025-01-01T00:00:00", "2025-01-01T01:00:00",
                    "2025-01-02T00:00:00", "2025-01-02T01:00:00"],
            "message": ["m1", "m2", "m3", "m4"]
        })
        df_issues = pd.DataFrame({
            "id": [1,2,3],
            "number": [101,102,103],
            "title": ["I1","I2","I3"],
            "user": ["u1","u2","u3"],
            "state": ["closed","open","closed"],
            "created_at": ["2025-01-01T00:00:00","2025-01-01T02:00:00","2025-01-02T00:00:00"],
            "closed_at": ["2025-01-01T12:00:00",None,"2025-01-02T12:00:00"],
            "comments": [0,1,2]
        })
        # Run summarize
        merge_and_summarize(df_commits, df_issues)
        captured = capsys.readouterr().out
        # Check top committer
        assert "Top 5 committers" in captured
        assert "X: 2 commits" in captured
        # Check close rate
        assert "Issue close rate: 0.67" in captured
        # Check avg open duration
        assert "Avg. issue open duration:" in captured

# --- Tests that hit real GitHub API (will be simulated with vcrpy) ---
class TestsWithVCR:
    @pytest.mark.vcr
    def test_fetch_commits_basic(self, monkeypatch):
        """ Basic fetch on well known small repo """
        df = fetch_commits("octocat/Hello-World")
        assert list(df.columns) == COMMIT_COLUMNS
        assert len(df) == 3
        assert df.iloc[0]["message"] == "Merge pull request #6 from Spaceghost/patch-1"

    @pytest.mark.vcr
    def test_fetch_commits_limit(self, monkeypatch):
        """ More commits than max_commits. Test that fetch_commits respects the max_commits limit. """
        df = fetch_commits("octocat/Hello-World", max_commits=2)
        assert list(df.columns) == COMMIT_COLUMNS
        assert len(df) == 2
        assert df.iloc[0]["message"] == "Merge pull request #6 from Spaceghost/patch-1"
            
    @pytest.mark.vcr
    def test_fetch_commits_empty(self, monkeypatch):
        """ Test that fetch_commits returns empty DataFrame when no max commits exist. """
        # Uses a cassette modified so that it returns 0 commits
        df = fetch_commits("octocat/Hello-World")
        assert list(df.columns) == COMMIT_COLUMNS
        assert len(df) == 0
        assert df.empty
    
    @pytest.mark.vcr()
    def test_fetch_issues_PR_filtering(self, monkeypatch):
        """ Test that fetch issues filters out PRs."""
        PR_issue_nums = [112, 106, 105, 104]
        df = fetch_issues("talos-rit/commander", state="all", max_issues=17)
        assert list(df.columns) == ISSUE_COLUMNS
        # Check that none of the PR issue numbers from the recorded cassette are in the DataFrame
        for issue_num in PR_issue_nums:
            assert issue_num not in df["number"].values
    
    @pytest.mark.vcr()
    def test_fetch_issues_correct_date_parsing(self, monkeypatch):
        """ Test that fetch issues correctly parses dates. Dates should be in ISO-8601 format if existing else None. """
        df = fetch_issues("talos-rit/commander", state="all", max_issues=17)
        # check that issue that hasn't been closed is None
        assert df.iloc[0]["closed_at"] is None
        # Pick an issue that has both created at and closed at dates and check its dates are in ISO-8601 format
        assert list(df.columns) == ISSUE_COLUMNS
        assert is_iso8601_format(df.iloc[11]["created_at"])
        assert is_iso8601_format(df.iloc[11]["closed_at"])
    
    @pytest.mark.vcr()
    def test_fetch_issues_open_duration(self, monkeypatch):
        """ Test that fetch issues correctly computes open_duration_days. """
        expected_open_duration = 41 # days
        df = fetch_issues("talos-rit/commander", state="closed", max_issues=20)
        assert list(df.columns) == ISSUE_COLUMNS
        # Test an issue that has been closed after being open for more than 0 or 1 days
        assert df.iloc[2]["open_duration_days"] == expected_open_duration
