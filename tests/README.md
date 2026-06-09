# Tests

Steps:
- Create a virtual environment.
- Install project dependencies.
- Install test dependencies.
- Run the test suite.

Setup
1. Create and activate a virtual environment:

   python3 -m venv .venv
   source .venv/bin/activate

2. Install project dependencies:

   pip install -r requirements.txt

3. Install test tools:

   pip install pytest requests

Run tests

Run the test suite:

pytest -q
