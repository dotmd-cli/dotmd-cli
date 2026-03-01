<div align="center">

# dotmd

**The open `.md` registry CLI**

Fetch and share the AI instruction files that power your coding assistants.

[![PyPI version](https://img.shields.io/pypi/v/dotmd.svg)](https://pypi.org/project/dotmd/)
[![Python versions](https://img.shields.io/pypi/pyversions/dotmd.svg)](https://pypi.org/project/dotmd/)
[![CI](https://github.com/dotmd-cli/dotmd-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/dotmd-cli/dotmd-cli/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

---

`dotmd` is a command-line tool for the [mydotmd.io](https://mydotmd.io) registry — like Docker Hub, but for `.md` instruction files. Browse, search, and pull the rules that configure AI coding assistants like Cursor, Claude, Windsurf, Copilot, and more.

---

## Table of Contents

- [Install](#install)
- [Quick Start](#quick-start)
- [Commands](#commands)
  - [find](#dotmd-find) ← recommended for agents
  - [get](#dotmd-get)
  - [search](#dotmd-search)
  - [list](#dotmd-list)
  - [info](#dotmd-info)
- [Output File Mapping](#output-file-mapping)
- [Configuration](#configuration)
- [LLM & Automation Usage](#llm--automation-usage)
- [Contributing](#contributing)

---

## Install

**Requires Python 3.9+**

```bash
pip install dotmd
```

Verify the install:

```bash
dotmd --version
```

---

## Quick Start

```bash
# Find and fetch a rule by description — the recommended one-liner for agents
dotmd find cli ux best practices    # → .dotmd/cli-ux.md
dotmd find hipaa compliance         # → .dotmd/hipaa.md

# Browse what's available
dotmd list

# Search by keyword
dotmd search react typescript

# Fetch a specific rule into your project
dotmd get dotmd/react-best-practices

# See where it was written
dotmd info
```

---

## Commands

### `dotmd find`

Search the registry by natural-language description and fetch the best-matching rule into `.dotmd/<title>.md`. This is the recommended command for LLM agents and agentic IDEs (Cursor, Windsurf, Claude, Copilot, etc.).

Rules are written to `.dotmd/<title>.md` so they sit alongside other context files without overwriting tool-specific instruction files like `AGENTS.md` or `.cursorrules`.

```bash
# Describe what you need — dotmd finds and fetches the best match
dotmd find cli ux best practices    # → .dotmd/cli-ux.md
dotmd find hipaa compliance         # → .dotmd/hipaa.md
dotmd find react typescript         # → .dotmd/react-best-practices.md
dotmd find testing                  # → .dotmd/testing.md
dotmd find git workflow             # → .dotmd/git.md

# Print content to stdout without writing a file
dotmd find cli ux --print

# Machine-readable JSON with full content and candidate list
dotmd find cli ux --json

# Preview destination without writing
dotmd find hipaa --dry-run
dotmd find hipaa --dry-run --json

# Write to a custom path
dotmd find hipaa --output .cursorrules

# Suppress all output (useful in scripts)
dotmd find hipaa --quiet
```

**Options:**

| Flag | Short | Description |
|------|-------|-------------|
| `--output PATH` | `-o` | Write to a specific path instead of `.dotmd/<title>.md` |
| `--force` | `-f` | Overwrite destination if it already exists |
| `--dry-run` | | Preview destination without writing |
| `--print` | | Print content to stdout, no file written |
| `--limit N` | `-n` | Number of search candidates to consider (default: 5) |
| `--quiet` | `-q` | Suppress non-error output |
| `--json` | | Emit JSON to stdout (includes `content` and `candidates` fields) |

---

### `dotmd get`

Fetch a rule from the registry and write it to the correct local instruction file for your AI tool.

```bash
# Full slug: <username>/<title>
dotmd get dotmd/react-best-practices

# Bare title — auto-resolved when only one match exists
dotmd get react-best-practices

# Explicit username with bare title
dotmd get react-best-practices --username dotmd

# Preview destination without writing (dry run)
dotmd get dotmd/react-best-practices --dry-run

# Write to a custom path
dotmd get dotmd/react-best-practices --output .cursorrules

# Overwrite an existing file
dotmd get dotmd/react-best-practices --force

# Suppress all output (useful in scripts)
dotmd get dotmd/react-best-practices --quiet

# Machine-readable JSON output
dotmd get dotmd/react-best-practices --json
```

**Options:**

| Flag | Short | Description |
|------|-------|-------------|
| `--username USER` | `-u` | Registry username (use with bare title) |
| `--output PATH` | `-o` | Write to a specific path instead of the default |
| `--force` | `-f` | Overwrite destination if it already exists |
| `--dry-run` | | Preview destination without writing |
| `--quiet` | `-q` | Suppress non-error output |
| `--json` | | Emit JSON to stdout |

---

### `dotmd search`

Search the registry for rules by keyword. Matches against rule titles.

```bash
# Single keyword
dotmd search python

# Multiple keywords (AND match)
dotmd search react typescript performance

# Limit results
dotmd search react --limit 5

# JSON output for scripting
dotmd search react --json
```

**Options:**

| Flag | Short | Description |
|------|-------|-------------|
| `--limit N` | `-n` | Max results (default: 20, max: 100) |
| `--json` | | Emit JSON to stdout |

---

### `dotmd list`

List rules for a specific user, or all public rules in the registry.

```bash
# All public rules
dotmd list

# Rules for a specific user
dotmd list dotmd

# Limit results
dotmd list --limit 50

# JSON output
dotmd list dotmd --json
```

**Options:**

| Flag | Short | Description |
|------|-------|-------------|
| `--limit N` | `-n` | Max results (default: 100, max: 200) |
| `--json` | | Emit JSON to stdout |

---

### `dotmd info`

Show version, registry details, supported formats, and configuration.

```bash
dotmd info

# Skip the ASCII art banner
dotmd info --plain

# JSON output
dotmd info --json
```

---

## Output File Mapping

When you run `dotmd get`, the rule is written to the standard location for its format type:

| Format | Written to |
|--------|-----------|
| `claude.md` | `CLAUDE.md` |
| `cursorrules` | `.cursorrules` |
| `windsurfrules` | `.windsurfrules` |
| `agents.md` | `AGENTS.md` |
| `copilot` | `.github/copilot-instructions.md` |
| `gemini` | `GEMINI.md` |
| `cline` | `.clinerules` |
| `aider` | `.aider.conf.yml` |
| `continue` | `.continue/config.json` |

Use `--output PATH` to override the destination for any rule.

---

## Configuration

`dotmd` works out of the box with no configuration. If your deployment requires authentication, set these environment variables:

```bash
# Supabase anon key (required for authenticated registries)
export DOTMD_SUPABASE_ANON_KEY="your-supabase-anon-key"

# Override the Supabase REST base URL (optional)
export DOTMD_SUPABASE_BASE_URL="https://your-project-ref.supabase.co/rest/v1"

# Aliases
export DOTMD_API_KEY="..."          # alias for DOTMD_SUPABASE_ANON_KEY
export DOTMD_BASE_URL="..."         # alias for DOTMD_SUPABASE_BASE_URL

# Disable color output (follows https://no-color.org/)
export NO_COLOR=1
```

**Auto-discovery:** If the default endpoint fails, `dotmd` automatically attempts to discover the current Supabase REST URL and anon key from `https://mydotmd.io` and retries.

---

## LLM & Automation Usage

`dotmd` is designed to work cleanly in automated pipelines and as a tool for AI agents:

**Pipe-friendly:** When stdout is not a TTY (piped, redirected, or called by an LLM), the ASCII art banner is automatically suppressed and only plain text is emitted.

**JSON output:** Every command supports `--json` for structured, machine-readable output:

```bash
# Get a rule and parse the result
dotmd get dotmd/react-best-practices --json | jq .destination

# Search and pipe to another tool
dotmd search react --json | jq '.results[].title'

# Dry run to check destination before writing
dotmd get dotmd/react-best-practices --dry-run --json
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | API or network error |
| `2` | Usage error (bad arguments, file exists without `--force`, ambiguous title) |
| `130` | Interrupted (Ctrl+C) |

**`NO_COLOR` support:** Set `NO_COLOR=1` to disable all ANSI color codes, following the [no-color.org](https://no-color.org/) convention.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and pull request guidelines.

---

## License

[MIT](LICENSE) © dotmd contributors
