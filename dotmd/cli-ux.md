# CLI UX Guidelines for AI Coding Assistant

## Help Text

Always provide clear, concise, and accurate help text for all commands and subcommands. You must ensure that help text is easily accessible via `--help` or `help` arguments.

When generating help text, include a brief description of the command's purpose, a list of available flags and their descriptions, and examples of common usage.

**Good Example:**

```bash
$ mycli command --help

Usage: mycli command [OPTIONS] ARGUMENT

  This command performs a specific action.

Options:
  --force  Force the operation without confirmation.
  --output TEXT  Specify an output file.
  --help  Show this message and exit.

Examples:
  mycli command value
  mycli command --force another_value
```

**Bad Example:**

```bash
$ mycli command --help

Usage: mycli command
```

## Flag Naming

Always use descriptive and consistent flag names. You must prefer full word flags over single-letter abbreviations unless the abbreviation is universally understood (e.g., `-v` for version).

When creating new flags, use kebab-case for multi-word flag names (e.g., `--output-file` instead of `--outputFile`).

**Good Example:**

```python
parser.add_argument('--verbose', action='store_true', help='Enable verbose output.')
parser.add_argument('--config-path', type=str, help='Path to the configuration file.')
```

**Bad Example:**

```python
parser.add_argument('-v', action='store_true', help='Verbose output.') # Ambiguous, could be version
parser.add_argument('--configPath', type=str, help='Config file.')
```

## Exit Codes

Always use standard exit codes to indicate the success or failure of a command. You must return `0` for successful execution and a non-zero value for errors.

When returning non-zero exit codes, use distinct values to differentiate between different types of errors (e.g., `1` for general errors, `2` for invalid arguments, `3` for file not found).

**Good Example:**

```python
import sys

def main():
    try:
        # ... command logic ...
        sys.exit(0)
    except ValueError:
        sys.stderr.write("Error: Invalid input.\n")
        sys.exit(2)
    except FileNotFoundError:
        sys.stderr.write("Error: File not found.\n")
        sys.exit(3)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
```

**Bad Example:**

```python
import sys

def main():
    # ... command logic ...
    if success:
        sys.exit(0)
    else:
        sys.exit(1) # Does not differentiate error types
```

## Progress Output

When a command performs a long-running operation, always provide clear progress indicators. You must use spinners, progress bars, or periodic status updates to inform the user of the command's status.

Do not flood the terminal with excessive progress messages. Provide updates at reasonable intervals.

**Good Example:**

```python
import time
from tqdm import tqdm

def long_running_task():
    for i in tqdm(range(100), desc="Processing data"):
        time.sleep(0.1)
    print("\nTask completed.")

long_running_task()
```

**Bad Example:**

```python
import time

def long_running_task():
    for i in range(100):
        print(f"Step {i+1}/100") # Too frequent updates
        time.sleep(0.1)
    print("Task completed.")

long_running_task()
```

## Error Messages

Always provide user-friendly and actionable error messages. You must clearly explain what went wrong and, if possible, suggest how to resolve the issue.

When an error occurs, write error messages to `stderr`. Do not write error messages to `stdout`.

**Good Example:**

```python
import sys

def process_file(filename):
    try:
        with open(filename, 'r') as f:
            # ... process file ...
            pass
    except FileNotFoundError:
        sys.stderr.write(f"Error: File '{filename}' not found. Please ensure the file exists and the path is correct.\n")
        sys.exit(3)

process_file("non_existent_file.txt")
```

**Bad Example:**

```python
import sys

def process_file(filename):
    try:
        with open(filename, 'r') as f:
            # ... process file ...
            pass
    except FileNotFoundError:
        print("Error: File not found.") # Not specific enough, written to stdout
        sys.exit(1)

process_file("non_existent_file.txt")
```

## Color Usage

When using colors in CLI output, always use them judiciously to enhance readability and convey meaning. You must use colors consistently (e.g., red for errors, yellow for warnings, green for success).

Do not rely solely on color to convey critical information, as some users may have color blindness or be using terminals that do not support color.

**Good Example:**

```python
from colorama import Fore, Style

print(f"{Fore.GREEN}Success: Operation completed successfully.{Style.RESET_ALL}")
print(f"{Fore.YELLOW}Warning: Configuration file not found, using defaults.{Style.RESET_ALL}")
print(f"{Fore.RED}Error: Failed to connect to the server.{Style.RESET_ALL}")
```

**Bad Example:**

```python
print("Success: Operation completed successfully.") # No color for success
print("Error: Failed to connect to the server.") # No color for error
```

## Stdin/Stdout Conventions

Always adhere to standard Unix stdin/stdout conventions. You must read input from `stdin` when no file argument is provided and write primary output to `stdout`.

When writing output, ensure that `stdout` contains only the intended program output, free from extraneous messages or debugging information.

**Good Example:**

```python
import sys

def process_input():
    if not sys.stdin.isatty():
        for line in sys.stdin:
            sys.stdout.write(line.upper()) # Process input from stdin and write to stdout
    else:
        sys.stdout.write("Please provide input via stdin or a file argument.\n")

process_input()
```

**Bad Example:**

```python
import sys

def process_input():
    print("Debugging: Starting input processing.") # Debugging info on stdout
    for line in sys.stdin:
        print(line.lower()) # Writes to stdout, but also includes debug info

process_input()
```
