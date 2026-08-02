# Tensionr

## Language

Everything written into the repo or the tracker is in **English** — issues, issue comments, docs, code comments, commit messages, PR descriptions. Live discussion with the project owner happens in Italian; nothing of that Italian ends up in a file or on GitHub.

## Python environment

- Use **`uv`** as the virtual environment and package manager.
- Always work inside the project virtualenv at **`.venv/`**; never install libraries globally. (`.env` is the secrets file, not the environment.)

## Agent skills

### Issue tracker

Issues live as GitHub issues in `exdsgift/tensionr`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary — `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — root `CONTEXT.md` plus `docs/adr/`. See `docs/agents/domain.md`.
