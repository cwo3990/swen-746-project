# swen-746-project

## Installation
To install the necessary dependencies for this project, it is recommended to use uv; however, you can also use pip.

*Note: Make sure you have Python 3.12 or higher installed.*

### Using uv
1.  Install uv if you haven't already:
    ```bash
    pip install uv
    ```
2. To create a virtual environment and install dependencies, run:
    ```bash
    uv sync
    ```
### Using pip
1.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
2. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
1. Set your GitHub token as an environment variable:
    ```bash
    export GITHUB_TOKEN=your_github_token
    ```
*Note: Replace `your_github_token` with your actual GitHub token. If you do not set this variable, the script will use unauthenticated requests, which are subject to stricter rate limits. For instructions on how to create a GitHub token, see the [GitHub documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).*

2. Run the script with the repository name as an argument:
    ```bash
    python src/repo_miner.py fetch-commits --repo owner/repo --out output.csv
    ```
    - Note: There is an optional `--max-commits` argument to limit the number of commits fetched. If not specified, all commits will be fetched. Run the command with `--help` to see all options:
    ```bash
    python src/repo_miner.py fetch-commits --help
    ```