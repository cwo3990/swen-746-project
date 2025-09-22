"""
repo_miner.py

A command-line tool to:
  1) Fetch and normalize commit data from GitHub

Sub-commands:
  - fetch-commits
"""

import os
import argparse
import pandas as pd
from github import Github
from github.Auth import Token

def fetch_commits(repo_name: str, max_commits: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_commits` from the specified GitHub repository.
    Returns a DataFrame with columns: sha, author, email, date, message.
    """
    # Handle edge case of max_commits <= 0
    if max_commits is not None and max_commits <= 0:
        return pd.DataFrame(columns=["sha", "author", "email", "date (ISO-8601)", "message (first line)"])
    
    # 1) Read GitHub token from environment
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("GITHUB_TOKEN environment variable not set. Using unauthenticated requests. Rate limits may apply.")
    
    # 2) Initialize GitHub client and get the repo
    g = Github(auth=Token(github_token)) if github_token else Github()
    
    repo = g.get_repo(repo_name)
    if not repo:
        raise ValueError(f"Repository `{repo_name}` not found or inaccessible.")

    # 3) Fetch commit objects (paginated by PyGitHub)
    print(f"Fetching commits from `{repo_name}`...")
    commits = repo.get_commits()
    if max_commits is not None:
        commits = commits[:max_commits]

    # 4) Normalize each commit into a record dict
    print("Normalizing commit data...")
    normalized_commits = []
    for commit in commits:
        record = {
            "sha": commit.sha,
            "author": commit.commit.author.name,
            "email": commit.commit.author.email,
            "date (ISO-8601)": commit.commit.author.date, # ISO-8601
            "message (first line)": commit.commit.message.split('\n', 1)[0] # first line only
        }
        normalized_commits.append(record)

    # 5) Build DataFrame from records
    commit_df: pd.DataFrame = pd.DataFrame(normalized_commits, 
                                           columns=["sha", "author", "email", "date (ISO-8601)", "message (first line)"])
    
    # Close GitHub client (not strictly necessary)
    g.close()
    
    return commit_df

def fetch_issues():
    # TODO: Implement issue fetching
    # This is currently here since the template for test_repo calls for it
    pass

def merge_and_summarize():
    # TODO: Implement merge and summarize
    # This is currently here since the template for test_repo calls for it
    pass
    

def main():
    """
    Parse command-line arguments and dispatch to sub-commands.
    """
    parser = argparse.ArgumentParser(
        prog="repo_miner",
        description="Fetch GitHub commits/issues and summarize them"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: fetch-commits
    c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
    c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c1.add_argument("--max",  type=int, dest="max_commits",
                    help="Max number of commits to fetch")
    c1.add_argument("--out",  required=True, help="Path to output commits CSV")

    args = parser.parse_args()

    # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")

if __name__ == "__main__":
    main()
