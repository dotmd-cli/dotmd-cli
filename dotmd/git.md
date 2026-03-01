# Git Workflow Instructions

## Conventional Commits

Always use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for all commit messages. This enables automated changelog generation and semantic versioning.

### Format

Your commit messages must adhere to the following structure:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

- **type**: Must be one of the following:
  - `feat`: A new feature
  - `fix`: A bug fix
  - `docs`: Documentation only changes
  - `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semicolons, etc.)
  - `refactor`: A code change that neither fixes a bug nor adds a feature
  - `perf`: A code change that improves performance
  - `test`: Adding missing tests or correcting existing tests
  - `build`: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm)
  - `ci`: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs)
  - `chore`: Other changes that don't modify src or test files
  - `revert`: Reverts a previous commit

- **scope (optional)**: A noun describing the section of the codebase affected. Enclose in parentheses.
- **description**: A concise, imperative, present tense description of the change. Do not capitalize the first letter. Do not end with a period.
- **body (optional)**: A longer, more detailed explanation of the commit. Use imperative, present tense. Wrap at 72 characters.
- **footer(s) (optional)**: Reference issues by their ID (e.g., `Fixes #123`, `Closes #456`). For breaking changes, start with `BREAKING CHANGE:` followed by a description.

### Good Examples

```
feat(parser): add ability to parse arrays

This commit introduces the capability to parse array structures within the input.
It addresses the need for handling complex data types in configuration files.

Closes #789
```

```
fix(auth): correct token expiration logic

Previously, tokens were expiring prematurely due to an incorrect timestamp calculation.
This fix ensures tokens expire at the intended time.

Fixes #101
```

### Bad Examples

```
updated auth
```

```
Fixing a bug in the authentication module related to token expiration. This was a critical issue.
```

## Branch Naming

Always follow a clear and consistent branch naming convention. This improves traceability and organization.

### Format

Your branch names must adhere to the following structure:

```
<type>/<issue-id>-<short-description>
```

- **type**: Must be one of the following:
  - `feature`: For new features
  - `bugfix`: For bug fixes
  - `hotfix`: For urgent bug fixes on production
  - `chore`: For maintenance tasks or non-code changes
  - `docs`: For documentation updates

- **issue-id**: The ID of the associated issue from the project's issue tracker (e.g., `JIRA-123`, `GH-456`).
- **short-description**: A concise, kebab-case description of the branch's purpose.

### Good Examples

```
feature/JIRA-456-add-user-profile-page
```

```
bugfix/GH-123-fix-login-redirect
```

### Bad Examples

```
my-feature
```

```
fixlogin
```

## Pull Request (PR) Hygiene

Always ensure your Pull Requests are clean, descriptive, and ready for review. This streamlines the review process and maintains code quality.

### Title

Your PR titles must follow the Conventional Commits specification, similar to commit messages. This ensures consistency and clarity.

### Description

Always provide a detailed description for every PR. Include the following sections:

- **What does this PR do?**: Briefly explain the changes.
- **Why is this change important?**: Describe the problem it solves or the feature it adds.
- **How was this tested?**: Detail the testing steps performed.
- **Screenshots/Videos (if applicable)**: Include visual aids for UI changes.
- **Related Issues**: Link to any relevant issues (e.g., `Closes #123`, `Fixes #456`).

### Reviewers

Always assign appropriate reviewers. Do not merge your own PRs.

### Good Example

```
Title: feat(api): implement user registration endpoint

Description:
What does this PR do?
This PR adds a new API endpoint for user registration, allowing new users to create accounts.

Why is this change important?
This is a foundational feature for user management and enables the application to onboard new users.

How was this tested?
Manual testing was performed using Postman to verify successful user creation and error handling for invalid inputs.
Unit tests were added for the new endpoint.

Related Issues:
Closes #789
```

### Bad Example

```
Title: Update

Description: Some changes.
```

## Merge Strategy

Always use a rebase-and-merge strategy for feature branches into `main`. This maintains a clean, linear commit history.

### Process

When merging a feature branch into `main`:

1. **Rebase**: You must rebase your feature branch onto the latest `main` branch before creating a PR or merging.
   ```bash
   git checkout feature/your-branch
   git fetch origin
   git rebase origin/main
   ```
2. **Resolve Conflicts**: If conflicts arise during rebase, you must resolve them immediately.
3. **Force Push**: After a successful rebase, you must force push your branch (only if you are sure no one else is working on it).
   ```bash
   git push --force-with-lease origin feature/your-branch
   ```
4. **Merge**: Once the PR is approved and rebased, you must use the 
rebase and merge option in the Git platform (e.g., GitHub, GitLab).

### Good Example

```bash
# On your feature branch
git checkout feature/new-feature
git fetch origin
git rebase origin/main
# Resolve any conflicts
git push --force-with-lease origin feature/new-feature
# Then, use the 'Rebase and merge' option in your Git platform for the PR.
```

### Bad Example

```bash
# Directly merging without rebase, creating a messy history
git merge main
```

## Version Tagging

Always use [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for all releases. This provides clear communication about the impact of changes.

### Format

Your version tags must adhere to the following format:

```
v<MAJOR>.<MINOR>.<PATCH>
```

- **MAJOR**: Increment when you make incompatible API changes.
- **MINOR**: Increment when you add functionality in a backward-compatible manner.
- **PATCH**: Increment when you make backward-compatible bug fixes.

### Process

When creating a new release:

1. **Identify Changes**: You must identify the type of changes (feat, fix, breaking change) since the last release.
2. **Determine Version**: Based on Conventional Commits and Semantic Versioning, you must determine the next version number.
3. **Create Tag**: You must create an annotated tag for the new version.
   ```bash
   git tag -a v1.2.3 -m "Release v1.2.3"
   ```
4. **Push Tag**: You must push the tag to the remote repository.
   ```bash
   git push origin v1.2.3
   ```

### Good Example

```bash
# After merging a new feature (feat) into main
git tag -a v1.1.0 -m "Release v1.1.0 - New feature: user profiles"
git push origin v1.1.0
```

### Bad Example

```bash
# Arbitrary version numbers or missing tags
git tag -a release-candidate -m "RC"
```
