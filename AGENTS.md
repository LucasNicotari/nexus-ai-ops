# NEXUS AI Ops — Agent Instructions

## Architecture

Keep domain, infrastructure, API, data, ML, AI, and observability concerns clearly separated. Introduce a layer only when its responsibility is needed; avoid premature abstractions.

## Code

- Prefer readable, low-coupling code and small, focused functions.
- Use type annotations when they improve clarity or safety.
- Avoid duplication and do not mask exceptions.
- Keep configuration in environment variables; never hardcode secrets.

## Testing and quality

- Consider validation for every relevant feature and add tests with the feature.
- Run `pytest`, `ruff check .`, and `ruff format --check .` after relevant changes.
- Report commands, results, warnings, and failures honestly.

## Security

- Never commit `.env`, credentials, tokens, passwords, or real corporate information.
- Use `.env.example` for documented local configuration.

## Git

Use Conventional Commits, such as `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, and `chore:`.

## Documentation and workflow

- Record significant architectural decisions in `docs/adr/`.
- Before substantial changes: explain the plan and affected files, implement, validate, report results, then suggest the next step.
- For important technologies, explain what it is, why it is used, alternatives, trade-offs, its role in NEXUS, and relevant interview talking points at an appropriate depth.
