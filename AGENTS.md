# Repository Guidelines

## Project Structure & Module Organization
Keep the repo lean. `open_x_cdp.py` lives at the root and is the single entry point for automating Chromium through the Chrome DevTools Protocol. Place future utilities in top-level modules with descriptive names (for example, `devtools_client.py`). New test files should live under a `tests/` directory mirroring the module layout.

## Build, Test, and Development Commands
Run the tool directly with `python3 open_x_cdp.py`; it verifies that a debugging port is ready and opens https://x.com. Use `python -m venv .venv` followed by `.venv/bin/pip install -r requirements.txt` if dependencies are added later. Execute `python -m pytest` from the repo root to run the test suite once it exists.

## Coding Style & Naming Conventions
Target Python 3.10+ with 4-space indentation, descriptive docstrings, and type hints. Favor small, composable functions with underscores for internal helpers (e.g., `_ensure_debug_port_ready`). CamelCase only for classes. Run `ruff check .` and `black .` before submitting; add them to your environment if missing.

## Testing Guidelines
Write unit tests with `pytest` and organize them alongside the code they exercise (e.g., `tests/test_open_x.py`). Name tests after the behavior under scrutiny, such as `test_launches_chromium_with_debug_port`. Cover edge cases like missing executables, timeouts, and HTTP errors. Aim for full coverage of CDP interactions via mocks to avoid launching real browsers in CI.

## Commit & Pull Request Guidelines
Use imperative, concise commit messages under 50 characters, followed by focused bodies when needed. Group related changes together and avoid mixing refactors with feature additions. Pull requests should describe the motivation, summarize functional changes, list verification steps (commands run), and call out any follow-up work. Link to tracking issues when relevant and include screenshots or logs only when they clarify browser automation behavior.

## Agent-Specific Notes
Chromium must run with `--remote-debugging-port=9222`; respect existing sessions before launching a new one. Any automation that could alter the user data dir should default to the dedicated `~/.chrome-devtools` folder used by the current script.
