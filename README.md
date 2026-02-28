# dotmd CLI

`dotmd` is a command-line client for downloading AI instruction files from the
[mydotmd.io](https://mydotmd.io) rule registry.

## Install

```bash
pip install dotmd
```

## Usage

Fetch a rule into the current directory:

```bash
dotmd get dotmd/react-best-practices.md
```

Search for rules by keyword(s):

```bash
dotmd search react typescript performance
```

List all rules for a user:

```bash
dotmd list dotmd
```

## Configuration

The CLI sends no auth headers by default. If your Supabase deployment requires
an API key, set:

```bash
export DOTMD_SUPABASE_ANON_KEY="your-supabase-anon-key"
export DOTMD_SUPABASE_BASE_URL="https://your-project-ref.supabase.co/rest/v1" # optional
```

## Output File Mapping

- `claude.md` -> `CLAUDE.md`
- `cursorrules` -> `.cursorrules`
- `windsurfrules` -> `.windsurfrules`
- `agents.md` -> `AGENTS.md`
- `copilot` -> `.github/copilot-instructions.md`
