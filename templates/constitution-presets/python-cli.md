# Constitution: <project name>

## Stack
- Language: Python 3.11+
- Framework: None (plain CLI / scripts)
- Database: N/A
- Infrastructure: Local execution only (no server, no Docker required)

## Coding Standards
- Linter: Ruff (ruff.toml) or flake8
- Formatter: Ruff format or Black
- Type checker: mypy (optional, recommended for entrypoints)
- Naming: snake_case for functions/variables, PascalCase for classes
- Max function length: 50 lines
- Max nesting depth: 4 levels
- Entrypoint: main in __main__.py or a single script; use argparse or click for CLI args
- No framework lock-in: stdlib + minimal deps (requests, etc. only if needed)

## Testing
- Minimum coverage: 70% (or N/A for throwaway scripts)
- Framework: pytest
- Required: tests for core logic; optional for one-off scripts
- No API/DB fixtures: use mocks or temp files where needed

## Constraints
- No web API, no database, no background workers unless explicitly added later
- Single-purpose scripts OK: one file per experiment or tool when appropriate
- Dependencies: list in pyproject.toml or requirements.txt; prefer stdlib
- Console output only (print, logging); no GUI unless specified

## Security
- Authorization: N/A (local CLI)
- Input validation: validate CLI args and file inputs; avoid eval/exec on user input
- Secrets: environment variables or .env (never committed); no secrets in code

## LLM Rules
- Do not leave stubs without explicit TODO with justification
- Do not duplicate code: prefer reuse and clear abstractions
- Do not make hidden assumptions — if unsure, ask
- Always generate AI_NOTES.md per template when modifying non-trivial code
- Follow the coding style described above
- Prefer small, runnable scripts; document how to run (e.g. in README or docstring)
