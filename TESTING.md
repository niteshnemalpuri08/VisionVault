Smoke & Update Tests

Overview
- This project includes simple smoke and update tests to validate core authentication and data-propagation flows.
- Tests are designed to run locally and in CI (GitHub Actions workflow: .github/workflows/smoke-tests.yml).

Run locally
1. Create a Python 3.12 venv and activate it.
2. Install requirements: pip install -r requirements.txt
3. Build the DB with demo data: python -m backend.json_to_sql
4. Start the server: python -m backend.server
   - For deterministic test runs, ensure the server is started without the Flask reloader (the server disables debug reloader by default).
5. Run smoke tests: python -m backend.scripts.run_smoke_tests
6. Run update tests: python -m backend.scripts.test_updates

Troubleshooting
- Connection refused / intermittent failures:
  - Ensure no other process is using port 5000.
  - Confirm the server started successfully and that you can reach http://127.0.0.1:5000/ in a browser or via curl.
  - If running inside WSL or containers, use the correct host binding.

CI
- The GitHub Actions workflow will:
  - Install dependencies
  - Build the DB
  - Start the server in the background
  - Wait for it to respond on http://127.0.0.1:5000/
  - Run the smoke tests

If you want the test suite to run longer or add more deterministic checks, consider running tests inside a container or using a process manager in CI to control server lifecycle precisely.