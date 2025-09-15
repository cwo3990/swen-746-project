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